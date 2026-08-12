"""Vector store: SQLite-backed cosine similarity search (pure Python)."""

from __future__ import annotations

import json
import math
import sqlite3
from abc import ABC, abstractmethod
from contextlib import closing
from pathlib import Path
from typing import Any


class VectorStore(ABC):
    @abstractmethod
    def add(self, id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None: ...

    @abstractmethod
    def search(self, vector: list[float], top_k: int = 5) -> list[tuple[str, float, dict[str, Any]]]: ...

    @abstractmethod
    def delete(self, id: str) -> None: ...

    @abstractmethod
    def count(self) -> int: ...


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("vectors must have non-zero norm")
    return dot / (norm_a * norm_b)


class SQLiteVectorStore(VectorStore):
    """Table ``vectors(id TEXT PK, vector TEXT JSON, metadata TEXT JSON)``."""

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._dim: int | None = None
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS vectors ("
                " id TEXT PRIMARY KEY, vector TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}')"
            )

    def add(self, id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        if not vector or all(v == 0 for v in vector):
            raise ValueError("vector must be non-empty with non-zero norm")
        with closing(self._connect()) as conn, conn:
            row = conn.execute("SELECT id FROM vectors WHERE id = ?", (id,)).fetchone()
            if row is not None:
                raise ValueError(f"vector id already exists: {id!r}")
            if self._dim is None:
                self._dim = len(vector)
            elif len(vector) != self._dim:
                raise ValueError(f"vector dim {len(vector)} != store dim {self._dim}")
            conn.execute(
                "INSERT INTO vectors (id, vector, metadata) VALUES (?, ?, ?)",
                (id, json.dumps(vector), json.dumps(metadata or {}, default=str)),
            )

    def search(self, vector: list[float], top_k: int = 5) -> list[tuple[str, float, dict[str, Any]]]:
        # Precedence: top_k <= 0 → ValueError; zero-vector → ValueError;
        # empty store → []; dim mismatch → ValueError; then scan.
        if top_k <= 0:
            raise ValueError("top_k must be > 0")
        if not vector or all(v == 0 for v in vector):
            raise ValueError("vector must be non-empty with non-zero norm")

        with closing(self._connect()) as conn, conn:
            rows = conn.execute("SELECT id, vector, metadata FROM vectors").fetchall()
        if not rows:
            return []
        if self._dim is None:
            self._dim = len(vector)
        elif len(vector) != self._dim:
            raise ValueError(f"query dim {len(vector)} != store dim {self._dim}")

        scored = []
        for vid, vjson, mjson in rows:
            stored = json.loads(vjson)
            score = _cosine(vector, stored)
            scored.append((vid, score, json.loads(mjson)))
        scored.sort(key=lambda t: (-t[1], t[0]))  # tie-break (-score, id)
        return scored[:top_k]

    def delete(self, id: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM vectors WHERE id = ?", (id,))

    def count(self) -> int:
        with closing(self._connect()) as conn, conn:
            row = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()
        return row[0]
