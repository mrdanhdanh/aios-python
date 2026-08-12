"""Conversation memory: SQLite-backed chat history."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

VALID_ROLES = ("system", "user", "assistant")


class ConversationMemory:
    """Persist conversations and messages (SQLite, connection-per-call)."""

    def __init__(self, db_path: str = "aios/data/conversations.db") -> None:
        self._db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS conversations ("
                " id TEXT PRIMARY KEY, session_id TEXT NOT NULL, created_at TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS messages ("
                " id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),"
                " role TEXT NOT NULL CHECK (role IN ('system','user','assistant')),"
                " content TEXT NOT NULL, created_at TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at)"
            )

    def create_conversation(self, session_id: str) -> str:
        conversation_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO conversations (id, session_id, created_at) VALUES (?, ?, ?)",
                (conversation_id, session_id, now),
            )
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> str:
        if role not in VALID_ROLES:
            raise ValueError(f"role must be one of {VALID_ROLES}, got {role!r}")
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"unknown conversation: {conversation_id!r}")
            message_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (message_id, conversation_id, role, content, now),
            )
        return message_id

    def get_messages(self, conversation_id: str, limit: int | None = None) -> list[dict]:
        """Always ascending (created_at, id); limit = N newest, ascending."""
        with closing(self._connect()) as conn, conn:
            if limit is not None:
                rows = conn.execute(
                    "SELECT * FROM (SELECT id, role, content, created_at FROM messages "
                    " WHERE conversation_id = ? ORDER BY created_at DESC, id DESC LIMIT ?) "
                    " ORDER BY created_at ASC, id ASC",
                    (conversation_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? "
                    " ORDER BY created_at ASC, id ASC",
                    (conversation_id,),
                ).fetchall()
        return [
            {"id": r[0], "role": r[1], "content": r[2], "created_at": r[3]}
            for r in rows
        ]

    def list_conversations(self, session_id: str) -> list[str]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT id FROM conversations WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [r[0] for r in rows]
