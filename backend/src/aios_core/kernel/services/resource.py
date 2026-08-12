"""Resource service: token budget + concurrent workflow slots."""

from __future__ import annotations

import threading
from typing import Any

from ...config import ResourcesSettings


class ResourceService:
    """Track token and concurrency usage.

    ``max_tokens``/``max_concurrent`` of ``None`` mean unlimited.
    Releases clamp at zero (never negative). Slot acquisition offers both a
    non-blocking ``acquire_slot`` (reject when full) and a blocking
    ``acquire_slot_wait`` (FIFO queue) for callers that may block.
    """

    def __init__(self, limits: ResourcesSettings | None = None) -> None:
        self._limits = limits or ResourcesSettings()
        self._used_tokens = 0
        self._running = 0
        self._lock = threading.RLock()
        self._slot_cond = threading.Condition(self._lock)
        self._queue: list[threading.Event] = []

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
            # Wake the next queued acquirer (FIFO).
            if self._queue:
                waiter = self._queue.pop(0)
                waiter.set()

    def acquire_slot_wait(self, timeout: float | None = None) -> bool:
        """Blocking slot acquisition with FIFO queue.

        Returns ``True`` once a slot is granted (may block). Returns ``False``
        on timeout. Unbounded ``max_concurrent`` grants immediately.

        The wait on the per-waiter ``Event`` happens *outside* the condition
        lock so that ``pending()`` and ``release_slot()`` can run concurrently
        while a caller is blocked.
        """
        with self._slot_cond:
            if self._limits.max_concurrent is None:
                self._running += 1
                return True
            if self._running < self._limits.max_concurrent:
                self._running += 1
                return True
            waiter = threading.Event()
            self._queue.append(waiter)
        # Block WITHOUT holding the condition lock so release_slot/pending work.
        if not waiter.wait(timeout):
            with self._slot_cond:
                if waiter in self._queue:
                    self._queue.remove(waiter)
            return False
        # Woken by release_slot: it already decremented _running, so claim it.
        with self._slot_cond:
            self._running += 1
        return True

    def pending(self) -> int:
        """Number of callers currently blocked waiting for a slot."""
        with self._lock:
            return len(self._queue)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "used_tokens": self._used_tokens,
                "running": self._running,
                "max_tokens": self._limits.max_tokens,
                "max_concurrent": self._limits.max_concurrent,
            }
