"""Long-Horizon Execution (TASK-056 — M9-P2).

Goal → Execution Session → Checkpoint → Context Compaction → Persisted State →
Resume (PLAN §M9-17). Checkpoint: Completed · Current · Pending · State
(§M9-18). **INV-032: execution dài hạn phải checkpoint/resume được** — process
chết → restart → load checkpoint → continue (KHÔNG chạy lại completed).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import Checkpoint, ExecutionSession, SessionStatus
from .errors import LongHorizonError

_MAX_CHECKPOINTS = 50
_MAX_NOTES = 200

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomous_sessions (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL,
    completed_json TEXT NOT NULL DEFAULT '[]',
    current TEXT NOT NULL DEFAULT '',
    pending_json TEXT NOT NULL DEFAULT '[]',
    state_json TEXT NOT NULL DEFAULT '{}',
    notes_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS autonomous_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    completed_json TEXT NOT NULL,
    current TEXT NOT NULL,
    pending_json TEXT NOT NULL,
    state_json TEXT NOT NULL,
    notes_json TEXT NOT NULL,
    at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ckpt_session ON autonomous_checkpoints(session_id, id);
"""

_TERMINAL = {SessionStatus.COMPLETED, SessionStatus.FAILED}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_session_id() -> str:
    return f"session-{uuid.uuid4().hex[:12]}"


class LongHorizonManager:
    """Session + checkpoint + resume — SQLite atomic (C1-01 v1).

    Checkpoint mới nhất nằm trong row session (đọc nhanh); history append vào
    ``autonomous_checkpoints`` bounded 50 (C1-03 v1, audit).
    """

    def __init__(self, event_service: EventService | None, db_path: Path | str) -> None:
        self._events = event_service
        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()

    # -- lifecycle -------------------------------------------------------------

    def create_session(self, goal_id: str = "") -> ExecutionSession:
        with self._lock:
            session = ExecutionSession(id=new_session_id(), goal_id=goal_id)
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "INSERT INTO autonomous_sessions (id, goal_id, status, created_at, updated_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (session.id, goal_id, SessionStatus.ACTIVE.value, _now_iso(), _now_iso()),
                )
            return session

    def get_session(self, session_id: str) -> ExecutionSession:
        with self._lock:
            row = self._row(session_id)
            if row is None:
                raise LongHorizonError(f"session không tồn tại: {session_id}")
            return ExecutionSession(id=row["id"], goal_id=row["goal_id"],
                                    status=SessionStatus(row["status"]),
                                    created_at=row["created_at"])

    def list_sessions(self, goal_id: str | None = None) -> list[ExecutionSession]:
        with self._lock:
            with closing(self._connect()) as conn:
                conn.row_factory = sqlite3.Row
                if goal_id:
                    rows = conn.execute(
                        "SELECT * FROM autonomous_sessions WHERE goal_id=?", (goal_id,)
                    ).fetchall()
                else:
                    rows = conn.execute("SELECT * FROM autonomous_sessions").fetchall()
            out = []
            for row in sorted(rows, key=lambda r: r["id"]):
                out.append(ExecutionSession(id=row["id"], goal_id=row["goal_id"],
                                            status=SessionStatus(row["status"]),
                                            created_at=row["created_at"]))
            return out

    def complete_session(self, session_id: str, failed: bool = False) -> None:
        with self._lock:
            self._require_active(session_id)
            status = SessionStatus.FAILED if failed else SessionStatus.COMPLETED
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_sessions SET status=?, updated_at=? WHERE id=?",
                    (status.value, _now_iso(), session_id),
                )

    # -- checkpoint ------------------------------------------------------------

    def checkpoint(
        self,
        session_id: str,
        completed: list[str] | None = None,
        current: str = "",
        pending: list[str] | None = None,
        state: dict | None = None,
        notes: list[str] | None = None,
    ) -> Checkpoint:
        """Lưu checkpoint — atomic 1 transaction (C1-01 v1/C2-01 v2).

        completed ∩ pending = ∅ (C2-02 v2); notes bounded 200 (FIFO).
        """
        with self._lock:
            self._require_active(session_id)
            done = list(completed or [])
            todo = list(pending or [])
            overlap = set(done) & set(todo)
            if overlap:
                raise LongHorizonError(f"completed ∩ pending ≠ ∅: {overlap}")
            notes_list = list(notes or [])
            if len(notes_list) > _MAX_NOTES:
                del notes_list[: len(notes_list) - _MAX_NOTES]
            state_dict = dict(state or {})
            ckpt = Checkpoint(
                session_id=session_id,
                completed=done,
                current=current,
                pending=todo,
                state=state_dict,
                notes=notes_list,
                at=_now_iso(),
            )
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_sessions SET completed_json=?, current=?, pending_json=?,"
                    " state_json=?, notes_json=?, updated_at=? WHERE id=?",
                    (
                        json.dumps(done), current, json.dumps(todo),
                        json.dumps(state_dict, default=str), json.dumps(notes_list),
                        _now_iso(), session_id,
                    ),
                )
                conn.execute(
                    "INSERT INTO autonomous_checkpoints (session_id, completed_json, current,"
                    " pending_json, state_json, notes_json, at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        session_id, json.dumps(done), current, json.dumps(todo),
                        json.dumps(state_dict, default=str), json.dumps(notes_list), ckpt.at,
                    ),
                )
                # bounded history (R3-1 v2): delete cũ hơn _MAX_CHECKPOINTS mới nhất
                conn.execute(
                    """
                    DELETE FROM autonomous_checkpoints WHERE session_id=? AND id NOT IN (
                        SELECT id FROM autonomous_checkpoints WHERE session_id=?
                        ORDER BY id DESC LIMIT ?
                    )
                    """,
                    (session_id, session_id, _MAX_CHECKPOINTS),
                )
            self._emit(session_id, "checkpoint")
            return ckpt

    def compact_note(self, session_id: str, note: str) -> Checkpoint:
        """Context compaction: thêm structured note (PLAN §M9-17)."""
        with self._lock:
            ckpt = self.resume(session_id)
            return self.checkpoint(
                session_id,
                completed=ckpt.completed,
                current=ckpt.current,
                pending=ckpt.pending,
                state=ckpt.state,
                notes=[*ckpt.notes, note],
            )

    def resume(self, session_id: str) -> Checkpoint:
        """INV-032: trả checkpoint mới nhất — chỉ khi ACTIVE/RESUMED (C2-01 v2)."""
        with self._lock:
            row = self._row(session_id)
            if row is None:
                raise LongHorizonError(f"session không tồn tại: {session_id}")
            status = SessionStatus(row["status"])
            if status in _TERMINAL:
                raise LongHorizonError(f"session terminal ({status.value}) — không resume")
            ckpt = Checkpoint(
                session_id=session_id,
                completed=json.loads(row["completed_json"]),
                current=row["current"],
                pending=json.loads(row["pending_json"]),
                state=json.loads(row["state_json"]),
                notes=json.loads(row["notes_json"]),
                at=row["updated_at"],
            )
            if status != SessionStatus.RESUMED:
                with closing(self._connect()) as conn, conn:
                    conn.execute(
                        "UPDATE autonomous_sessions SET status=?, updated_at=? WHERE id=?",
                        (SessionStatus.RESUMED.value, _now_iso(), session_id),
                    )
            self._emit(session_id, "resume")
            return ckpt

    def checkpoint_history(self, session_id: str) -> list[dict]:
        """History checkpoint (audit, bounded 50)."""
        with self._lock:
            with closing(self._connect()) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT completed_json, current, pending_json, at FROM autonomous_checkpoints"
                    " WHERE session_id=? ORDER BY id DESC LIMIT ?",
                    (session_id, _MAX_CHECKPOINTS),
                ).fetchall()
            return [
                {
                    "completed": json.loads(r["completed_json"]),
                    "current": r["current"],
                    "pending": json.loads(r["pending_json"]),
                    "at": r["at"],
                }
                for r in rows
            ]

    # -- internals -------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(_DB_SCHEMA)

    def _row(self, session_id: str) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM autonomous_sessions WHERE id=?", (session_id,)
            ).fetchone()

    def _require_active(self, session_id: str) -> None:
        row = self._row(session_id)
        if row is None:
            raise LongHorizonError(f"session không tồn tại: {session_id}")
        if SessionStatus(row["status"]) in _TERMINAL:
            raise LongHorizonError("session terminal — không ghi checkpoint")

    def _emit(self, session_id: str, note: str) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_CHECKPOINT,
            {"session_id": session_id, "note": note},
            source="autonomous.long_horizon",
        )
