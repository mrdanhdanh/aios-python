"""Backup store for upgrade pipeline (TASK-020) — SQLite snapshot/restore."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BackupRecord:
    id: int
    kind: str
    component_id: str
    version: str
    created_at: str


class BackupStore:
    """Persists component payload snapshots before migration."""

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
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    component_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def backup(self, kind: str, component_id: str, version: str, payload: dict[str, Any]) -> int:
        """Snapshot a payload; returns the backup id."""
        self._init_db()
        created_at = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO backups (kind, component_id, version, payload, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (kind, component_id, version, json.dumps(payload, sort_keys=True), created_at),
            )
            return int(cur.lastrowid)

    def restore(self, backup_id: int) -> dict[str, Any]:
        """Return the payload of a backup (raises KeyError when missing)."""
        self._init_db()
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT payload FROM backups WHERE id = ?", (backup_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"backup not found: {backup_id}")
        return json.loads(row["payload"])

    def list(self, kind: str | None = None, component_id: str | None = None) -> list[BackupRecord]:
        self._init_db()
        sql = "SELECT id, kind, component_id, version, created_at FROM backups"
        params: list[Any] = []
        where: list[str] = []
        if kind is not None:
            where.append("kind = ?")
            params.append(kind)
        if component_id is not None:
            where.append("component_id = ?")
            params.append(component_id)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            BackupRecord(
                id=row["id"],
                kind=row["kind"],
                component_id=row["component_id"],
                version=row["version"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
