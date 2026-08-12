"""Knowledge memory: index text → chunks → vectors; semantic search."""

from __future__ import annotations

import sqlite3
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

    def count(self) -> int:
        return self._vectors.count()
