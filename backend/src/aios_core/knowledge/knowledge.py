"""Knowledge memory: index text → chunks → vectors; semantic search."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..memory.vector import SQLiteVectorStore
from .chunks import ChunksStore
from .embedder import Embedder

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNK_STEP = CHUNK_SIZE - CHUNK_OVERLAP


@dataclass
class ChunkResult:
    source_id: str
    chunk_index: int
    text: str
    score: float


@dataclass
class ChunkRecord:
    """Read-only chunk listing entry (TASK-023 additive)."""

    id: str
    source_id: str
    chunk_index: int
    text: str


class KnowledgeMemory:
    """Offline knowledge base: same SQLite file for vectors + chunks.

    Vector id == chunk id == ``{source_id}:{chunk_index}``.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._vectors = SQLiteVectorStore(str(self._db_path))
        self._chunks = ChunksStore(str(self._db_path))

    def _chunk_text(self, text: str) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            chunks.append(text[start : start + CHUNK_SIZE])
            start += CHUNK_STEP
        return chunks

    def index_text(self, source_id: str, text: str, embedder: Embedder) -> int:
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        # Re-index (replace): read old ids first, then delete vectors, then
        # replace chunks, then add new vectors.
        old_ids = self._chunks.get_ids_by_source(source_id)
        for old_id in old_ids:
            self._vectors.delete(old_id)

        new_ids = self._chunks.replace_source(source_id, list(enumerate(chunks)))
        for chunk_id, chunk_text in zip(new_ids, chunks):
            self._vectors.add(chunk_id, embedder.embed(chunk_text))
        return len(chunks)

    def search(
        self, query: str, embedder: Embedder, top_k: int = 5
    ) -> list[ChunkResult]:
        query_vector = embedder.embed(query)
        hits = self._vectors.search(query_vector, top_k=top_k)
        results: list[ChunkResult] = []
        with sqlite3.connect(self._db_path) as conn:
            for chunk_id, score, _meta in hits:
                row = conn.execute(
                    "SELECT source_id, chunk_index, text FROM chunks WHERE id = ?", (chunk_id,)
                ).fetchone()
                if row is None:
                    continue
                results.append(
                    ChunkResult(
                        source_id=row[0],
                        chunk_index=row[1],
                        text=row[2],
                        score=score,
                    )
                )
        return results

    def delete_source(self, source_id: str) -> None:
        ids = self._chunks.get_ids_by_source(source_id)
        for chunk_id in ids:
            self._vectors.delete(chunk_id)
        self._chunks.delete_by_source(source_id)

    def list_chunks(self, source_id: str | None = None) -> list[ChunkRecord]:
        """List all chunks (optionally filtered by source), deterministic order.

        Additive read-only method (TASK-023): queries the chunks table
        directly (like ``search``) without touching ChunksStore internals.
        """
        query = "SELECT id, source_id, chunk_index, text FROM chunks"
        params: tuple[Any, ...] = ()
        if source_id is not None:
            query += " WHERE source_id = ?"
            params = (source_id,)
        query += " ORDER BY source_id ASC, chunk_index ASC"
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            ChunkRecord(id=r[0], source_id=r[1], chunk_index=r[2], text=r[3])
            for r in rows
        ]

    def count(self) -> int:
        return self._vectors.count()
