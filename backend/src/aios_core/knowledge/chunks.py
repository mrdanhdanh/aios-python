"""Chunk store: keeps chunk text for retrieval (same DB file as vectors)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


class ChunksStore:
    """Table ``chunks(id PK, source_id, chunk_index, text)``.

    Chunk id convention: ``{source_id}:{chunk_index}`` (matches vector ids).
    """

    def __init__(self, db_path: str = "aios/data/knowledge.db") -> None:
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
                "CREATE TABLE IF NOT EXISTS chunks ("
                " id TEXT PRIMARY KEY, source_id TEXT NOT NULL, chunk_index INTEGER NOT NULL,"
                " text TEXT NOT NULL)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id)")

    def add(self, chunk_id: str, source_id: str, chunk_index: int, text: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO chunks (id, source_id, chunk_index, text) VALUES (?, ?, ?, ?)",
                (chunk_id, source_id, chunk_index, text),
            )

    def get(self, chunk_id: str) -> dict | None:
        with closing(self._connect()) as conn, conn:
            row = conn.execute(
                "SELECT id, source_id, chunk_index, text FROM chunks WHERE id = ?", (chunk_id,)
            ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "source_id": row[1], "chunk_index": row[2], "text": row[3]}

    def get_ids_by_source(self, source_id: str) -> list[str]:
        with closing(self._connect()) as conn, conn:
            rows = conn.execute(
                "SELECT id FROM chunks WHERE source_id = ?", (source_id,)
            ).fetchall()
        return [r[0] for r in rows]

    def replace_source(self, source_id: str, chunks: list[tuple[int, str]]) -> list[str]:
        """Replace all chunks of a source; returns the NEW chunk ids.

        Caller is responsible for deleting old vectors (via get_ids_by_source
        BEFORE calling this) and adding new vectors afterwards.
        """
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
            new_ids: list[str] = []
            for index, text in chunks:
                chunk_id = f"{source_id}:{index}"
                conn.execute(
                    "INSERT INTO chunks (id, source_id, chunk_index, text) VALUES (?, ?, ?, ?)",
                    (chunk_id, source_id, index, text),
                )
                new_ids.append(chunk_id)
        return new_ids

    def delete_by_source(self, source_id: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
