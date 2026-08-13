"""Metrics service (TASK-021) — event-bus driven counters + durations (SQLite).

Audit (EventService) is the source of truth; this is an aggregate cache.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..kernel.events import Event, EventBus, EventType

# Events we track: (start types, finish types, category)
_WORKFLOW_START = {EventType.WORKFLOW_STARTED}
_WORKFLOW_FINISH = {
    EventType.WORKFLOW_COMPLETED,
    EventType.WORKFLOW_FAILED,
    EventType.WORKFLOW_CANCELLED,
}
_TOOL_START = {EventType.TOOL_STARTED}
_TOOL_FINISH = {EventType.TOOL_FINISHED}

_TRACKED = _WORKFLOW_START | _TOOL_START | _WORKFLOW_FINISH | _TOOL_FINISH


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ms(start: datetime, finish: datetime) -> float:
    return (finish - start).total_seconds() * 1000.0


class MetricsService:
    """Counts and durations of workflow/tool events, persisted in SQLite."""

    def __init__(self, bus: EventBus, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
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
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    execution_id TEXT NOT NULL,
                    node_id TEXT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    duration_ms REAL,
                    ok INTEGER
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_open "
                "ON metrics(category, execution_id, node_id, finished_at)"
            )

    # -- event handling -------------------------------------------------------

    def _on_event(self, event: Event) -> None:
        if event.type not in _TRACKED:
            return  # R3-7: filter only tracked types
        self._init_db()
        category = "workflow" if event.type in (_WORKFLOW_START | _WORKFLOW_FINISH) else "tool"
        payload = event.payload
        execution_id = str(payload.get("execution_id") or "")
        if category == "tool":
            node_id = payload.get("node_id")
        else:
            node_id = None
        if event.type in _WORKFLOW_START or event.type in _TOOL_START:
            name = str(payload.get("plan_id") or payload.get("node_name") or "")
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "INSERT INTO metrics (category, name, execution_id, node_id, started_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (category, name, execution_id, node_id, _iso(event.timestamp)),
                )
        else:
            # finish: update the LATEST unfinished row (re-run safe — P2-2)
            with closing(self._connect()) as conn, conn:
                row = conn.execute(
                    "SELECT id FROM metrics WHERE category = ? AND execution_id = ? "
                    "AND node_id IS ? AND finished_at IS NULL "
                    "ORDER BY id DESC LIMIT 1",
                    (category, execution_id, node_id),
                ).fetchone()
                if row is None:
                    return  # orphan finish — ignore
                # find its start timestamp
                start_row = conn.execute(
                    "SELECT started_at FROM metrics WHERE id = ?", (row["id"],)
                ).fetchone()
                start = datetime.fromisoformat(start_row["started_at"])
                finish = event.timestamp
                ok = None
                if event.type == EventType.TOOL_FINISHED:
                    ok = 1 if payload.get("ok") else 0
                conn.execute(
                    "UPDATE metrics SET finished_at = ?, duration_ms = ?, ok = ? WHERE id = ?",
                    (_iso(finish), _ms(start, finish), ok, row["id"]),
                )

    # -- queries ---------------------------------------------------------------

    def _ensure(self) -> None:
        self._init_db()

    def counts(self) -> dict[str, int]:
        self._ensure()
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT category, COUNT(*) AS n FROM metrics GROUP BY category"
            ).fetchall()
        result = {r["category"]: r["n"] for r in rows}
        result.setdefault("workflow", 0)
        result.setdefault("tool", 0)
        return result

    def average_duration(self, category: str) -> float | None:
        self._ensure()
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT AVG(duration_ms) AS avg FROM metrics "
                "WHERE category = ? AND duration_ms IS NOT NULL",
                (category,),
            ).fetchone()
        return row["avg"] if row and row["avg"] is not None else None

    def slowest(self, category: str, limit: int = 5) -> list[dict[str, Any]]:
        self._ensure()
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT name, execution_id, duration_ms FROM metrics "
                "WHERE category = ? AND duration_ms IS NOT NULL "
                "ORDER BY duration_ms DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        self._ensure()
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT category, name, execution_id, node_id, started_at, "
                "finished_at, duration_ms FROM metrics "
                "ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def tool_failures(self) -> int:
        """Count of TOOL_FINISHED events with ok=false."""
        self._ensure()
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM metrics WHERE category = 'tool' AND ok = 0"
            ).fetchone()
        return row["n"] if row else 0

    def summary(self) -> dict[str, Any]:
        """Keys: counts, avg_duration_ms, tool_failures, total."""
        self._ensure()
        counts = self.counts()
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM metrics").fetchone()
        return {
            "counts": counts,
            "avg_duration_ms": {
                "workflow": self.average_duration("workflow"),
                "tool": self.average_duration("tool"),
            },
            "tool_failures": self.tool_failures(),
            "total": row["n"] if row else 0,
        }

    def close(self) -> None:
        self._subscription.unsubscribe()
