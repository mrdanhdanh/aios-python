"""Event service: EventBus wrapper + SQLite audit log."""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from ..events import Event, EventBus, EventType
from ...logging import get_logger

logger = get_logger("aios.kernel.services.events")


class EventService:
    """Publish events to the bus and persist an audit trail.

    Order: audit first, publish second (a broken audit never loses the event).
    Uses a fresh connection per call (thread-safe) with busy_timeout.
    """

    def __init__(self, bus: EventBus, db_path: Path | str) -> None:
        self._bus = bus
        self._db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_type_ts ON audit_events(type, timestamp)")

    def emit(
        self,
        event_type: EventType,
        payload: dict | None = None,
        source: str = "",
    ) -> Event:
        event = Event(type=event_type, payload=payload or {}, source=source)
        self._audit(event)
        self._bus.publish(event)
        return event

    def _audit(self, event: Event) -> None:
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "INSERT INTO audit_events (id, type, timestamp, source, payload_json) VALUES (?, ?, ?, ?, ?)",
                    (
                        event.id,
                        event.type.value,
                        event.timestamp.isoformat(),
                        event.source,
                        json.dumps(event.payload, default=str),
                    ),
                )
        except sqlite3.Error as exc:
            logger.warning("Audit insert failed (event still published): %s", exc)

    def query_audit(self, limit: int = 100, event_type: EventType | None = None) -> list[Event]:
        """Return audit events, newest first."""
        try:
            with closing(self._connect()) as conn, conn:
                if event_type is not None:
                    rows = conn.execute(
                        "SELECT id, type, timestamp, source, payload_json FROM audit_events "
                        "WHERE type = ? ORDER BY timestamp DESC LIMIT ?",
                        (event_type.value, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT id, type, timestamp, source, payload_json FROM audit_events "
                        "ORDER BY timestamp DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
        except sqlite3.Error as exc:
            logger.warning("Audit query failed: %s", exc)
            return []

        events: list[Event] = []
        for row in rows:
            event_id, type_str, timestamp, source, payload_json = row
            try:
                event_type = EventType(type_str)
            except ValueError:
                logger.warning("Unknown event type in audit: %s", type_str)
                continue
            try:
                payload = json.loads(payload_json)
            except json.JSONDecodeError:
                payload = {}
            events.append(
                Event(
                    id=event_id,
                    type=event_type,
                    timestamp=__import__("datetime").datetime.fromisoformat(timestamp),
                    source=source,
                    payload=payload,
                )
            )
        return events
