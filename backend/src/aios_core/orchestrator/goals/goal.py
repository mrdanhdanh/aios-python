"""Goal Manager: long-lived multi-session goals persisted in SQLite.

Each goal is broken into tasks; every task maps to a workflow. Progress and
auto-status are recomputed from the DB on every mutation (no in-memory cache —
lesson F-006). State machines are enforced both in code and via CHECK
constraints (second safety layer).
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...kernel.events import EventType
from ...kernel.services.events import EventService
from .errors import GoalError
from .schema import SCHEMA_SQL

_TASK_FIELDS = (
    "id, goal_id, title, workflow_name, status, priority, position, result, created_at, updated_at"
)


class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Goal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str = ""
    status: GoalStatus = GoalStatus.ACTIVE
    progress: float = 0.0
    created_at: str
    updated_at: str
    tasks: list[GoalTask] = Field(default_factory=list)  # noqa: F821 — forward ref


class GoalTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    goal_id: str
    title: str
    workflow_name: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    position: int = 0
    result: str = ""
    created_at: str
    updated_at: str


# Resolve the forward reference (Goal.tasks).
Goal.model_rebuild()

# Task transitions: source -> allowed targets.
_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.QUEUED, TaskStatus.PAUSED, TaskStatus.CANCELLED},
    TaskStatus.QUEUED: {TaskStatus.RUNNING, TaskStatus.PAUSED, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.PAUSED: {TaskStatus.QUEUED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.CANCELLED: set(),
}

# Goal transitions: source -> allowed targets.
_GOAL_TRANSITIONS: dict[GoalStatus, set[GoalStatus]] = {
    GoalStatus.ACTIVE: {GoalStatus.PAUSED, GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.CANCELLED},
    GoalStatus.PAUSED: {GoalStatus.ACTIVE, GoalStatus.CANCELLED},
    GoalStatus.COMPLETED: set(),
    GoalStatus.FAILED: set(),
    GoalStatus.CANCELLED: set(),
}

_TERMINAL_GOALS = {GoalStatus.COMPLETED, GoalStatus.FAILED, GoalStatus.CANCELLED}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GoalManager:
    """Persistent goal CRUD + progress + auto-status.

    Thread-safe via connection-per-call with ``busy_timeout`` (same pattern as
    EventService). GoalManager and TaskQueue MUST share the same ``db_path``
    (cancel_goal cascade touches queue_items).
    """

    def __init__(self, event_service: EventService, db_path: Path | str) -> None:
        self._events = event_service
        self._db_path = Path(db_path)
        self._init_db()

    # -- persistence helpers -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(SCHEMA_SQL)

    def _row_to_task(self, row: tuple) -> GoalTask:
        return GoalTask(
            id=row[0],
            goal_id=row[1],
            title=row[2],
            workflow_name=row[3],
            status=TaskStatus(row[4]),
            priority=row[5],
            position=row[6],
            result=row[7],
            created_at=row[8],
            updated_at=row[9],
        )

    def _row_to_goal(self, row: tuple) -> Goal:
        return Goal(
            id=row[0],
            title=row[1],
            description=row[2],
            status=GoalStatus(row[3]),
            progress=row[4],
            created_at=row[5],
            updated_at=row[6],
        )

    def _get_goal_row(self, conn: sqlite3.Connection, goal_id: str) -> tuple | None:
        return conn.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()

    def _load_tasks(self, conn: sqlite3.Connection, goal_id: str) -> list[GoalTask]:
        rows = conn.execute(
            f"SELECT {_TASK_FIELDS} FROM goal_tasks WHERE goal_id=? ORDER BY position",
            (goal_id,),
        ).fetchall()
        return [self._row_to_task(r) for r in rows]

    def _recompute_goal(self, conn: sqlite3.Connection, goal_id: str) -> None:
        """Recompute progress + auto-status for an ACTIVE goal (C2-11: also
        called by resume_goal). Caller owns the transaction."""
        row = self._get_goal_row(conn, goal_id)
        if row is None:
            return
        tasks = self._load_tasks(conn, goal_id)
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status in (TaskStatus.FAILED, TaskStatus.CANCELLED))
        progress = (completed / total) if total else 0.0
        old_status = GoalStatus(row[3])
        new_status = old_status
        if old_status == GoalStatus.ACTIVE:
            if total > 0 and completed == total:
                new_status = GoalStatus.COMPLETED
            elif failed > 0:
                new_status = GoalStatus.FAILED
        now = _now_iso()
        conn.execute(
            "UPDATE goals SET progress=?, status=?, updated_at=? WHERE id=?",
            (progress, new_status.value, now, goal_id),
        )
        if new_status != old_status:
            self._events.emit(
                EventType.GOAL_STATUS_CHANGED,
                {"goal_id": goal_id, "status": new_status.value, "progress": progress},
                source="goal_manager",
            )

    # -- public API ----------------------------------------------------------

    def create_goal(self, title: str, description: str = "", tasks: list[dict] | None = None) -> Goal:
        """Create a goal (+ optional tasks) in one transaction. Tasks dicts:
        {title, workflow_name, priority?}."""
        if not title:
            raise GoalError("goal title must not be empty")
        goal_id = uuid.uuid4().hex
        now = _now_iso()
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO goals (id, title, description, status, progress, created_at, updated_at)"
                " VALUES (?, ?, ?, 'active', 0.0, ?, ?)",
                (goal_id, title, description, now, now),
            )
            for position, spec in enumerate(tasks or []):
                task_id = uuid.uuid4().hex
                conn.execute(
                    "INSERT INTO goal_tasks (id, goal_id, title, workflow_name, status, priority, position,"
                    " result, created_at, updated_at)"
                    " VALUES (?, ?, ?, ?, 'pending', ?, ?, '', ?, ?)",
                    (
                        task_id,
                        goal_id,
                        spec["title"],
                        spec["workflow_name"],
                        int(spec.get("priority", 0)),
                        position,
                        now,
                        now,
                    ),
                )
        self._events.emit(
            EventType.GOAL_CREATED,
            {"goal_id": goal_id, "title": title},
            source="goal_manager",
        )
        goal = self.get_goal(goal_id)
        assert goal is not None
        return goal

    def add_task(self, goal_id: str, title: str, workflow_name: str, priority: int = 0) -> GoalTask:
        now = _now_iso()
        with closing(self._connect()) as conn, conn:
            row = self._get_goal_row(conn, goal_id)
            if row is None:
                raise GoalError(f"goal not found: {goal_id}")
            if GoalStatus(row[3]) in _TERMINAL_GOALS:
                raise GoalError(f"goal is terminal: {goal_id}")
            position = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM goal_tasks WHERE goal_id=?",
                (goal_id,),
            ).fetchone()[0]
            task_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO goal_tasks (id, goal_id, title, workflow_name, status, priority, position,"
                " result, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, 'pending', ?, ?, '', ?, ?)",
                (task_id, goal_id, title, workflow_name, priority, position, now, now),
            )
        task = self._load_tasks(self._connect(), goal_id)  # fresh read for the return value
        return next(t for t in task if t.id == task_id)

    def update_task_status(
        self, goal_id: str, task_id: str, status: TaskStatus, result: str = ""
    ) -> GoalTask:
        """Transition a task; recompute goal progress + auto-status.

        Events (GOAL_TASK_UPDATED / GOAL_STATUS_CHANGED) are emitted ONLY on
        success — a failed transition raises GoalError and emits nothing (C1-15).
        """
        with closing(self._connect()) as conn, conn:
            row = self._get_goal_row(conn, goal_id)
            if row is None:
                raise GoalError(f"goal not found: {goal_id}")
            task_row = conn.execute(
                "SELECT * FROM goal_tasks WHERE id=?",
                (task_id,),
            ).fetchone()
            if task_row is None:
                raise GoalError(f"task not found: {task_id}")
            if task_row[1] != goal_id:
                raise GoalError(f"task {task_id} not in goal {goal_id}")
            current = TaskStatus(task_row[4])
            if status not in _TASK_TRANSITIONS[current]:
                raise GoalError(f"invalid task transition: {current.value} -> {status.value}")
            now = _now_iso()
            conn.execute(
                "UPDATE goal_tasks SET status=?, result=?, updated_at=? WHERE id=?",
                (status.value, result, now, task_id),
            )
            self._recompute_goal(conn, goal_id)
        self._events.emit(
            EventType.GOAL_TASK_UPDATED,
            {"goal_id": goal_id, "task_id": task_id, "status": status.value},
            source="goal_manager",
        )
        with closing(self._connect()) as conn:
            task_row = conn.execute(
                "SELECT * FROM goal_tasks WHERE id=?", (task_id,)
            ).fetchone()
        return self._row_to_task(task_row)  # type: ignore[arg-type]

    def get_goal(self, goal_id: str) -> Goal | None:
        with closing(self._connect()) as conn:
            row = self._get_goal_row(conn, goal_id)
            if row is None:
                return None
            goal = self._row_to_goal(row)
            goal.tasks = self._load_tasks(conn, goal_id)
            return goal

    def list_goals(self, status: GoalStatus | None = None, limit: int = 100) -> list[Goal]:
        with closing(self._connect()) as conn:
            if status is None:
                rows = conn.execute(
                    "SELECT * FROM goals ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM goals WHERE status=? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                ).fetchall()
        goals = [self._row_to_goal(r) for r in rows]
        for goal in goals:
            with closing(self._connect()) as conn:
                goal.tasks = self._load_tasks(conn, goal.id)
        return goals

    def progress(self, goal_id: str) -> float:
        with closing(self._connect()) as conn:
            row = self._get_goal_row(conn, goal_id)
            if row is None:
                raise GoalError(f"goal not found: {goal_id}")
            return float(row[4])

    def _set_goal_status(self, goal_id: str, new_status: GoalStatus) -> Goal:
        with closing(self._connect()) as conn, conn:
            row = self._get_goal_row(conn, goal_id)
            if row is None:
                raise GoalError(f"goal not found: {goal_id}")
            current = GoalStatus(row[3])
            if new_status not in _GOAL_TRANSITIONS[current]:
                raise GoalError(f"invalid goal transition: {current.value} -> {new_status.value}")
            now = _now_iso()
            conn.execute(
                "UPDATE goals SET status=?, updated_at=? WHERE id=?",
                (new_status.value, now, goal_id),
            )
            if new_status == GoalStatus.CANCELLED:
                # Cascade (C1-02, R5): queued queue items + non-terminal tasks -> cancelled,
                # same transaction. queue_items table always exists (shared DDL — R1).
                conn.execute(
                    "UPDATE queue_items SET status='cancelled', updated_at=? WHERE goal_id=? AND status='queued'",
                    (now, goal_id),
                )
                conn.execute(
                    "UPDATE goal_tasks SET status='cancelled', updated_at=? WHERE goal_id=? AND status NOT IN"
                    " ('completed','failed','cancelled')",
                    (now, goal_id),
                )
            if new_status == GoalStatus.ACTIVE:
                # resume: recompute auto-status (C2-11) — may flip to completed/failed.
                self._recompute_goal(conn, goal_id)
        self._events.emit(
            EventType.GOAL_STATUS_CHANGED,
            {"goal_id": goal_id, "status": new_status.value, "progress": self.progress(goal_id)},
            source="goal_manager",
        )
        goal = self.get_goal(goal_id)
        assert goal is not None
        return goal

    def pause_goal(self, goal_id: str) -> Goal:
        return self._set_goal_status(goal_id, GoalStatus.PAUSED)

    def resume_goal(self, goal_id: str) -> Goal:
        return self._set_goal_status(goal_id, GoalStatus.ACTIVE)

    def cancel_goal(self, goal_id: str) -> Goal:
        return self._set_goal_status(goal_id, GoalStatus.CANCELLED)
