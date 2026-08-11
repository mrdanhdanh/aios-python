"""Resource service: token budget + concurrent workflow slots."""

from __future__ import annotations

import threading
from typing import Any

from ...config import ResourcesSettings


class ResourceService:
    """Track token and concurrency usage.

    ``max_tokens``/``max_concurrent`` of ``None`` mean unlimited.
    Releases clamp at zero (never negative).
    """

    def __init__(self, limits: ResourcesSettings | None = None) -> None:
        self._limits = limits or ResourcesSettings()
        self._used_tokens = 0
        self._running = 0
        self._lock = threading.RLock()

    @property
    def limits(self) -> ResourcesSettings:
        return self._limits

    def acquire_tokens(self, tokens: int) -> bool:
        with self._lock:
            if tokens < 0:
                return False
            if self._limits.max_tokens is None:
                self._used_tokens += tokens
                return True
            if self._used_tokens + tokens > self._limits.max_tokens:
                return False
            self._used_tokens += tokens
            return True

    def release_tokens(self, tokens: int) -> None:
        with self._lock:
            self._used_tokens = max(0, self._used_tokens - tokens)

    def acquire_slot(self) -> bool:
        with self._lock:
            if self._limits.max_concurrent is None:
                self._running += 1
                return True
            if self._running >= self._limits.max_concurrent:
                return False
            self._running += 1
            return True

    def release_slot(self) -> None:
        with self._lock:
            self._running = max(0, self._running - 1)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "used_tokens": self._used_tokens,
                "running": self._running,
                "max_tokens": self._limits.max_tokens,
                "max_concurrent": self._limits.max_concurrent,
            }
