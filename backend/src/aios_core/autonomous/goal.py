"""Autonomous Goal Engine (TASK-050 — M9-P1).

Goal là contract đầy đủ (objective/success/constraints/permissions/autonomy)
với lifecycle 13 trạng thái (PLAN §M9-5): PROPOSED → VALIDATING → APPROVED →
PLANNING → EXECUTING → EVALUATING → COMPLETED, cộng nhánh phục hồi
BLOCKED → RECOVERY → REPLANNING và ESCALATED (terminal). Persist SQLite
(autonomous.db — riêng goals.db của M2), emit events ``autonomy.goal_*``.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import GoalContract, GoalLifecycleState, _GOAL_TRANSITIONS
from .errors import GoalLifecycleError

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomous_goals (
    id TEXT PRIMARY KEY,
    objective TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    success_json TEXT NOT NULL DEFAULT '{}',
    constraints_json TEXT NOT NULL DEFAULT '{}',
    permissions_json TEXT NOT NULL DEFAULT '[]',
    autonomy TEXT NOT NULL DEFAULT 'A2',
    steps_json TEXT NOT NULL DEFAULT '[]',
    completed_steps_json TEXT NOT NULL DEFAULT '[]',
    state TEXT NOT NULL,
    history_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

_STEP_ALLOWED_STATES = {
    GoalLifecycleState.EXECUTING,
    GoalLifecycleState.REPLANNING,
    GoalLifecycleState.RECOVERY,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutonomousGoalEngine:
    """Lifecycle + persist của Autonomous Goals (TASK-050).

    Thread-safe: connection-per-call + busy_timeout (pattern EventService);
    RLock bảo vệ state in-memory. Fail-closed: transition bất hợp lệ → raise.
    """

    def __init__(self, event_service: EventService | None, db_path: Path | str) -> None:
        self._events = event_service
        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()

    # -- persistence -----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(_DB_SCHEMA)

    def _row_to_contract(self, row: sqlite3.Row) -> GoalContract:
        return GoalContract(
            id=row["id"],
            objective=row["objective"],
            description=row["description"],
            success=json.loads(row["success_json"]),
            constraints=json.loads(row["constraints_json"]),
            permissions=json.loads(row["permissions_json"]),
            autonomy=row["autonomy"],
            steps=json.loads(row["steps_json"]),
            completed_steps=json.loads(row["completed_steps_json"]),
        )

    # -- public API ------------------------------------------------------------

    def propose(self, goal: GoalContract) -> GoalContract:
        """Tạo goal ở trạng thái PROPOSED (C2-04: autonomy validated by pydantic)."""
        with self._lock:
            if not goal.id or not goal.objective.strip():
                raise GoalLifecycleError("goal cần id và objective")
            self._insert(goal, GoalLifecycleState.PROPOSED, [])
            self._emit_created(goal)
            return self.get(goal.id)

    def get(self, goal_id: str) -> GoalContract:
        with self._lock:
            row = self._query_state(goal_id)
            if row is None:
                raise GoalLifecycleError(f"goal không tồn tại: {goal_id}")
            return self._row_to_contract(row)

    def get_state(self, goal_id: str) -> GoalLifecycleState:
        with self._lock:
            row = self._query_state(goal_id)
            if row is None:
                raise GoalLifecycleError(f"goal không tồn tại: {goal_id}")
            return GoalLifecycleState(row["state"])

    def get_history(self, goal_id: str) -> list[dict[str, Any]]:
        with self._lock:
            row = self._query_state(goal_id)
            if row is None:
                raise GoalLifecycleError(f"goal không tồn tại: {goal_id}")
            return json.loads(row["history_json"])

    def list_goals(self) -> list[dict[str, Any]]:
        with self._lock:
            with closing(self._connect()) as conn:
                rows = conn.execute(
                    "SELECT id, objective, state, steps_json, completed_steps_json FROM autonomous_goals"
                ).fetchall()
            out = []
            for row in sorted(rows, key=lambda r: r["id"]):
                steps = json.loads(row["steps_json"])
                done = json.loads(row["completed_steps_json"])
                out.append(
                    {
                        "id": row["id"],
                        "objective": row["objective"],
                        "state": row["state"],
                        "progress": (len(done) / len(steps)) if steps else 0.0,
                    }
                )
            return out

    def transition(self, goal_id: str, target: GoalLifecycleState, reason: str = "auto") -> GoalContract:
        """Chuyển trạng thái — raise nếu transition không hợp lệ (fail-closed)."""
        with self._lock:
            row = self._query_state(goal_id)
            if row is None:
                raise GoalLifecycleError(f"goal không tồn tại: {goal_id}")
            current = GoalLifecycleState(row["state"])
            if target not in _GOAL_TRANSITIONS[current]:
                raise GoalLifecycleError(
                    f"transition không hợp lệ: {current.value} → {target.value}"
                )
            history = json.loads(row["history_json"])
            history.append({"state": target.value, "at": _now_iso(), "reason": reason})
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_goals SET state=?, history_json=?, updated_at=? WHERE id=?",
                    (target.value, json.dumps(history), _now_iso(), goal_id),
                )
            self._emit_state(goal_id, target.value, reason)
            return self.get(goal_id)

    # -- helper transitions (chuỗi chuẩn) --------------------------------------

    def validate(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.VALIDATING, "validate")

    def approve(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.APPROVED, "approve")

    def plan(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.PLANNING, "plan")

    def execute(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.EXECUTING, "execute")

    def evaluate(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.EVALUATING, "evaluate")

    def complete(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.COMPLETED, "success")

    def block(self, goal_id: str, reason: str = "blocked") -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.BLOCKED, reason)

    def recover(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.RECOVERY, "recover")

    def replan(self, goal_id: str) -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.REPLANNING, "replan")

    def escalate(self, goal_id: str, reason: str = "escalated") -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.ESCALATED, reason)

    def fail(self, goal_id: str, reason: str = "failed") -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.FAILED, reason)

    def cancel(self, goal_id: str, reason: str = "cancelled") -> GoalContract:
        return self.transition(goal_id, GoalLifecycleState.CANCELLED, reason)

    # -- steps + progress ------------------------------------------------------

    def set_steps(self, goal_id: str, steps: list[str]) -> GoalContract:
        with self._lock:
            self._require_state(goal_id, GoalLifecycleState.PLANNING)
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_goals SET steps_json=?, updated_at=? WHERE id=?",
                    (json.dumps(steps), _now_iso(), goal_id),
                )
            return self.get(goal_id)

    def mark_step_completed(self, goal_id: str, step: str) -> GoalContract:
        """Đánh dấu step hoàn thành — chỉ ở EXECUTING/REPLANNING/RECOVERY (C2-02)."""
        with self._lock:
            self._require_state(goal_id, _STEP_ALLOWED_STATES)
            row = self._query_state(goal_id)
            steps = json.loads(row["steps_json"])
            if step not in steps:
                raise GoalLifecycleError(f"step không thuộc goal: {step}")
            done = json.loads(row["completed_steps_json"])
            if step in done:
                raise GoalLifecycleError(f"step đã hoàn thành: {step}")
            done.append(step)
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_goals SET completed_steps_json=?, updated_at=? WHERE id=?",
                    (json.dumps(done), _now_iso(), goal_id),
                )
            return self.get(goal_id)

    def success_achieved(self, goal_id: str) -> bool:
        """success conditions đạt? V1: progress == 1.0 (mọi step xong)."""
        goal = self.get(goal_id)
        return goal.progress() >= 1.0

    # -- internals -------------------------------------------------------------

    def _insert(self, goal: GoalContract, state: GoalLifecycleState, history: list[dict[str, Any]]) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO autonomous_goals (
                    id, objective, description, success_json, constraints_json,
                    permissions_json, autonomy, steps_json, completed_steps_json,
                    state, history_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.id,
                    goal.objective,
                    goal.description,
                    json.dumps(goal.success),
                    goal.constraints.model_dump_json(),
                    json.dumps(goal.permissions),
                    goal.autonomy.value,
                    json.dumps(goal.steps),
                    json.dumps(goal.completed_steps),
                    state.value,
                    json.dumps(history),
                    _now_iso(),
                    _now_iso(),
                ),
            )

    def _query_state(self, goal_id: str) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM autonomous_goals WHERE id=?", (goal_id,)
            ).fetchone()

    def _require_state(self, goal_id: str, allowed: set[GoalLifecycleState]) -> None:
        row = self._query_state(goal_id)
        if row is None:
            raise GoalLifecycleError(f"goal không tồn tại: {goal_id}")
        current = GoalLifecycleState(row["state"])
        if current not in allowed:
            raise GoalLifecycleError(
                f"thao tác không hợp lệ ở trạng thái {current.value}"
            )

    def _emit_created(self, goal: GoalContract) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_GOAL_CREATED,
            {"goal_id": goal.id, "objective": goal.objective, "autonomy": goal.autonomy.value},
            source="autonomous.goal",
        )

    def _emit_state(self, goal_id: str, state: str, reason: str) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_GOAL_STATE,
            {"goal_id": goal_id, "state": state, "reason": reason},
            source="autonomous.goal",
        )


def new_goal_id() -> str:
    return f"goal-{uuid.uuid4().hex[:12]}"
