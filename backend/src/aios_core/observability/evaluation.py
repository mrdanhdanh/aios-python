"""Evaluation framework v2 core (TASK-021) — auto-capture + feedback store.

Auto-captures workflow outcomes from the event bus (WORKFLOW_STARTED kept
in-memory for duration); quality/feedback written explicitly via evaluate().
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from ..kernel.events import Event, EventBus, EventType


@dataclass(frozen=True)
class WorkflowEvaluation:
    execution_id: str
    workflow_id: str
    success: bool
    duration_ms: float | None
    quality: float | None
    feedback: str
    created_at: str


@dataclass(frozen=True)
class EvaluationVerdict:
    quality: float | None
    feedback: str


class Evaluator(Protocol):
    def evaluate(self, workflow_id: str, execution_id: str, result: dict[str, Any]) -> EvaluationVerdict: ...


class EvaluationStore:
    """Persists workflow evaluations; listens to the event bus."""

    def __init__(self, bus: EventBus, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._started: dict[str, datetime] = {}
        self._subscription = bus.subscribe(None, self._on_event)

    # -- persistence ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    duration_ms REAL,
                    quality REAL,
                    feedback TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_eval_workflow ON evaluations(workflow_id)"
            )

    # -- event handling -------------------------------------------------------

    def _on_event(self, event: Event) -> None:
        if event.type == EventType.WORKFLOW_STARTED:
            execution_id = str(event.payload.get("execution_id") or "")
            if execution_id:
                self._started[execution_id] = event.timestamp
            return
        if event.type in (
            EventType.WORKFLOW_COMPLETED,
            EventType.WORKFLOW_FAILED,
            EventType.WORKFLOW_CANCELLED,
        ):
            execution_id = str(event.payload.get("execution_id") or "")
            workflow_id = str(event.payload.get("plan_id") or "")  # opaque — no prefix parsing
            success = event.type == EventType.WORKFLOW_COMPLETED
            started = self._started.pop(execution_id, None)
            duration_ms = None
            if started is not None:
                duration_ms = (event.timestamp - started).total_seconds() * 1000.0
            self._init_db()
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "INSERT INTO evaluations "
                    "(execution_id, workflow_id, success, duration_ms, quality, feedback, created_at) "
                    "VALUES (?, ?, ?, ?, NULL, '', ?)",
                    (
                        execution_id,
                        workflow_id,
                        1 if success else 0,
                        duration_ms,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )

    # -- queries ---------------------------------------------------------------

    def evaluate(self, execution_id: str, quality: float, feedback: str = "") -> None:
        """Attach quality/feedback to the LATEST row for an execution."""
        self._init_db()
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT id FROM evaluations WHERE execution_id = ? ORDER BY id DESC LIMIT 1",
                (execution_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"no evaluation row for execution: {execution_id}")
            conn.execute(
                "UPDATE evaluations SET quality = ?, feedback = ? WHERE id = ?",
                (quality, feedback, row["id"]),
            )

    def list(self, workflow_id: str | None = None, limit: int = 100) -> list[WorkflowEvaluation]:
        self._init_db()
        sql = ("SELECT execution_id, workflow_id, success, duration_ms, quality, "
               "feedback, created_at FROM evaluations")
        params: list[Any] = []
        if workflow_id is not None:
            sql += " WHERE workflow_id = ?"
            params.append(workflow_id)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            WorkflowEvaluation(
                execution_id=r["execution_id"],
                workflow_id=r["workflow_id"],
                success=bool(r["success"]),
                duration_ms=r["duration_ms"],
                quality=r["quality"],
                feedback=r["feedback"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def average_quality(self, workflow_id: str | None = None) -> float | None:
        self._init_db()
        sql = "SELECT AVG(quality) AS avg FROM evaluations WHERE quality IS NOT NULL"
        params: list[Any] = []
        if workflow_id is not None:
            sql += " AND workflow_id = ?"
            params.append(workflow_id)
        with closing(self._connect()) as conn:
            row = conn.execute(sql, params).fetchone()
        return row["avg"] if row and row["avg"] is not None else None

    def counts(self) -> dict[str, int]:
        self._init_db()
        with closing(self._connect()) as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM evaluations").fetchone()
            success = conn.execute(
                "SELECT COUNT(*) AS n FROM evaluations WHERE success = 1"
            ).fetchone()
        return {
            "success": success["n"] if success else 0,
            "failed": (total["n"] if total else 0) - (success["n"] if success else 0),
            "total": total["n"] if total else 0,
        }

    def close(self) -> None:
        self._subscription.unsubscribe()
