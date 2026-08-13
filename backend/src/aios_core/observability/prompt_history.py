"""Prompt render history (TASK-021) — SQLite store."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromptRecord:
    id: int
    prompt_id: str
    version: str
    variables: dict[str, Any]
    output: str
    duration_ms: float | None
    created_at: str


class PromptHistory:
    """Persists prompt render records (explicit calls from API/CLI callers)."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)

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
                CREATE TABLE IF NOT EXISTS prompt_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    variables_json TEXT NOT NULL,
                    output TEXT NOT NULL,
                    duration_ms REAL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def record(
        self,
        prompt_id: str,
        version: str,
        variables: dict[str, Any],
        output: str,
        duration_ms: float | None = None,
    ) -> int:
        self._init_db()
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO prompt_history "
                "(prompt_id, version, variables_json, output, duration_ms, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    prompt_id,
                    version,
                    json.dumps(variables, sort_keys=True, ensure_ascii=False),
                    output,
                    duration_ms,
                    created_at,
                ),
            )
            return int(cur.lastrowid)

    def list(self, prompt_id: str | None = None, limit: int = 100) -> list[PromptRecord]:
        self._init_db()
        sql = "SELECT id, prompt_id, version, variables_json, output, duration_ms, created_at " \
              "FROM prompt_history"
        params: list[Any] = []
        if prompt_id is not None:
            sql += " WHERE prompt_id = ?"
            params.append(prompt_id)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            PromptRecord(
                id=r["id"],
                prompt_id=r["prompt_id"],
                version=r["version"],
                variables=json.loads(r["variables_json"]),
                output=r["output"],
                duration_ms=r["duration_ms"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def count(self) -> int:
        self._init_db()
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM prompt_history").fetchone()
        return row["n"] if row else 0
