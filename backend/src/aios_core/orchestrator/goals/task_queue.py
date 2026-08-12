"""Task Queue: the Orchestrator's LOGICAL queue (not the technical Scheduler).

Persisted in the shared ``goals.db`` (``queue_items`` table) so a fresh process
can keep dequeuing queued work. Enqueue is atomic (single INSERT..SELECT for
position), dequeue is a single UPDATE..RETURNING statement (SQLite >= 3.35) —
no double-dequeue, no spurious empty result (review R3/C2-05).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...kernel.events import EventType
from ...kernel.services.events import EventService
from .errors import QueueError
from .schema import SCHEMA_SQL

_ITEM_FIELDS = "id, workflow_name, priority, status, payload_json, task_id, goal_id, position, created_at, updated_at"


class QueueItemStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class QueueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    workflow_name: str
    priority: int = 0
    status: QueueItemStatus = QueueItemStatus.QUEUED
    payload: dict = Field(default_factory=dict)
    task_id: str | None = None
    goal_id: str | None = None
    position: int = 0
    created_at: str
    updated_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_payload(raw: str) -> dict:
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


class TaskQueue:
    """Logical queue with priority + FIFO ordering, pause/resume/reorder/clear.

    MUST share the same ``db_path`` as the GoalManager that links queue items to
    goals (cancel_goal cascade). Single-writer single-process assumption
    (recover_stale_running may requeue items a second process is really running).
    """

    def __init__(self, event_service: EventService, db_path: Path | str) -> None:
        self._events = event_service
        self._db_path = Path(db_path)
        self._init_db()
        # C1-03: requeue items stuck in `running` from a crashed session.
        self.recover_stale_running()

    # -- persistence helpers -------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(SCHEMA_SQL)

    def _row_to_item(self, row: tuple) -> QueueItem:
        return QueueItem(
            id=row[0],
            workflow_name=row[1],
            priority=row[2],
            status=QueueItemStatus(row[3]),
            payload=_parse_payload(row[4]),
            task_id=row[5],
            goal_id=row[6],
            position=row[7],
            created_at=row[8],
            updated_at=row[9],
        )

    def _emit(self, action: str, item: QueueItem | None, extra: dict | None = None) -> None:
        payload = {
            "action": action,
            "item_id": item.id if item else None,
            "workflow_name": item.workflow_name if item else "",
        }
        if extra:
            payload.update(extra)
        self._events.emit(EventType.QUEUE_UPDATED, payload, source="task_queue")

    # -- public API ----------------------------------------------------------

    def enqueue(
        self,
        workflow_name: str,
        priority: int = 0,
        payload: dict | None = None,
        task_id: str | None = None,
        goal_id: str | None = None,
    ) -> QueueItem:
        """Append an item. Position is computed atomically (single statement) —
        concurrent enqueues never collide (UNIQUE(position) is the guard).

        Does NOT validate goal_id/task_id existence (queue is decoupled from
        goals — C1-16); links are metadata for supervisors/reports.
        """
        item_id = uuid.uuid4().hex
        now = _now_iso()
        payload_json = json.dumps(payload or {}, default=str)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO queue_items (id, workflow_name, priority, status, payload_json, task_id,"
                " goal_id, position, created_at, updated_at)"
                " SELECT ?, ?, ?, 'queued', ?, ?, ?, COALESCE(MAX(position), -1) + 1, ?, ? FROM queue_items",
                (item_id, workflow_name, priority, payload_json, task_id, goal_id, now, now),
            )
        item = QueueItem(
            id=item_id,
            workflow_name=workflow_name,
            priority=priority,
            status=QueueItemStatus.QUEUED,
            payload=payload or {},
            task_id=task_id,
            goal_id=goal_id,
            position=0,
            created_at=now,
            updated_at=now,
        )
        self._emit("enqueue", item)
        return item

    def dequeue(self) -> QueueItem | None:
        """Atomically claim the highest-priority queued item (single
        UPDATE..RETURNING — no double-dequeue, no spurious None)."""
        now = _now_iso()
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "UPDATE queue_items SET status='running', updated_at=?"
                " WHERE id = (SELECT id FROM queue_items WHERE status='queued'"
                "              ORDER BY priority DESC, position ASC LIMIT 1)"
                " RETURNING " + _ITEM_FIELDS,
                (now,),
            ).fetchone()
        if row is None:
            return None
        item = self._row_to_item(row)
        self._emit("dequeue", item)
        return item

    def _transition(self, item_id: str, target: QueueItemStatus, action: str) -> QueueItem:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                f"SELECT {_ITEM_FIELDS} FROM queue_items WHERE id=?", (item_id,)
            ).fetchone()
            if row is None:
                raise QueueError(f"queue item not found: {item_id}")
            current = QueueItemStatus(row[3])
            allowed = {
                QueueItemStatus.QUEUED: {QueueItemStatus.PAUSED},
                QueueItemStatus.PAUSED: {QueueItemStatus.QUEUED},
            }.get(current)
            if allowed is None or target not in allowed:
                raise QueueError(f"invalid queue transition: {current.value} -> {target.value}")
            now = _now_iso()
            conn.execute(
                "UPDATE queue_items SET status=?, updated_at=? WHERE id=?",
                (target.value, now, item_id),
            )
        item = self._row_to_item(row)
        item.status = target
        item.updated_at = now
        self._emit(action, item)
        return item

    def pause(self, item_id: str) -> QueueItem:
        """queued -> paused. Anything else raises QueueError (no event emitted)."""
        return self._transition(item_id, QueueItemStatus.PAUSED, "pause")

    def resume(self, item_id: str) -> QueueItem:
        """paused -> queued. Anything else raises QueueError (no event emitted)."""
        return self._transition(item_id, QueueItemStatus.QUEUED, "resume")

    def reorder(self, item_ids: list[str]) -> None:
        """Re-assign positions 0..n-1 following ``item_ids`` order.

        MUST list ALL currently-queued items (else QueueError). Two-phase swap
        inside one transaction because UNIQUE(position) is immediate (C2-01):
        phase 1 moves listed items to a negative range, phase 2 to 0..n-1.
        Ordering only matters within the same priority — priority wins.
        """
        with closing(self._connect()) as conn, conn:
            queued_ids = {
                r[0]
                for r in conn.execute(
                    "SELECT id FROM queue_items WHERE status='queued'"
                ).fetchall()
            }
            if set(item_ids) != queued_ids:
                raise QueueError("reorder requires exactly all queued items")
            if len(item_ids) != len(set(item_ids)):
                raise QueueError("reorder item_ids must be unique")
            # Phase 1: negative temporary positions (never collide with real ones).
            for offset, item_id in enumerate(item_ids):
                conn.execute(
                    "UPDATE queue_items SET position=?, updated_at=? WHERE id=?",
                    (-(offset + 1), _now_iso(), item_id),
                )
            # Phase 2: final positions.
            for position, item_id in enumerate(item_ids):
                conn.execute(
                    "UPDATE queue_items SET position=?, updated_at=? WHERE id=?",
                    (position, _now_iso(), item_id),
                )
        for item_id in item_ids:
            with closing(self._connect()) as conn:
                row = conn.execute(
                    f"SELECT {_ITEM_FIELDS} FROM queue_items WHERE id=?", (item_id,)
                ).fetchone()
            if row is not None:
                self._emit("reorder", self._row_to_item(row))

    def list_items(self, status: QueueItemStatus | None = None, limit: int = 100) -> list[QueueItem]:
        with closing(self._connect()) as conn:
            if status is None:
                rows = conn.execute(
                    f"SELECT {_ITEM_FIELDS} FROM queue_items ORDER BY priority DESC, position ASC LIMIT ?",
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    f"SELECT {_ITEM_FIELDS} FROM queue_items WHERE status=? ORDER BY priority DESC,"
                    " position ASC LIMIT ?",
                    (status.value, limit),
                ).fetchall()
        return [self._row_to_item(r) for r in rows]

    def clear(self, status: QueueItemStatus = QueueItemStatus.QUEUED) -> int:
        """Delete items by status (default queued only — never touches running)."""
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "DELETE FROM queue_items WHERE status=?", (status.value,)
            )
        self._emit("clear", None, {"count": cur.rowcount})
        return cur.rowcount

    def recover_stale_running(self, threshold_s: float = 3600.0) -> int:
        """Requeue items stuck in `running` older than threshold (crash recovery).

        Emits QUEUE_UPDATED (action="recover") per requeued item (R4 — audit).
        """
        cutoff = datetime.now(timezone.utc).timestamp() - threshold_s
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT id, workflow_name, updated_at FROM queue_items WHERE status='running'"
            ).fetchall()
            stale: list[tuple] = []
            for item_id, workflow_name, updated_at in rows:
                try:
                    updated_ts = datetime.fromisoformat(updated_at).timestamp()
                except ValueError:
                    updated_ts = 0.0  # unparseable -> treat as stale
                if updated_ts <= cutoff:
                    stale.append((item_id, workflow_name))
            now = _now_iso()
            for item_id, _ in stale:
                conn.execute(
                    "UPDATE queue_items SET status='queued', updated_at=? WHERE id=? AND status='running'",
                    (now, item_id),
                )
        for item_id, workflow_name in stale:
            self._emit("recover", QueueItem(id=item_id, workflow_name=workflow_name,
                                            created_at="", updated_at=""))
        return len(stale)
