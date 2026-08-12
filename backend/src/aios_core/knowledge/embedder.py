"""Embedders: deterministic offline mock (sha256-based)."""

from __future__ import annotations

import hashlib
from typing import Protocol


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class MockEmbedder:
    """Deterministic 32-dim vector in [0,1] from sha256 (stable cross-process).

    ``digest = sha256(text).digest()`` (32 bytes) → ``[b / 255 for b in digest]``.
    """

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in digest]
