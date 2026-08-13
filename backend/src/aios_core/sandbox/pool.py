"""SandboxPool — reusable mock sandbox pool per language (TASK-015).

Deterministic, offline, no threads. warm=True means "reused from pool this
time" (monotonic — C2-05). acquire/release must happen on the same thread
(C2-04 — no ownership token in v1).
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .errors import SandboxPoolError


class SandboxState(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    DESTROYED = "destroyed"


@dataclass
class Sandbox:
    id: str
    language: str
    state: SandboxState = SandboxState.IDLE
    warm: bool = False  # True = reused from pool (not cold-start this time); monotonic (C2-05)
    created_at: float = field(default_factory=time.monotonic)
    last_used_at: float = field(default_factory=time.monotonic)


class SandboxResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    sandbox_id: str
    language: str
    warm: bool
    result: Any = None
    error: str = ""


class SandboxPool:
    def __init__(self, max_size: int = 4, idle_timeout_s: float = 300.0) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be > 0")
        if idle_timeout_s < 0:
            raise ValueError("idle_timeout_s must be >= 0")
        self._max_size = max_size
        self._idle_timeout_s = idle_timeout_s
        self._lock = threading.RLock()
        self._sandboxes: list[Sandbox] = []

    # -- helpers --------------------------------------------------------------

    def _normalize_language(self, language: str) -> str:
        if not language or not language.strip():
            raise SandboxPoolError("language must not be empty")
        return language.strip().lower()  # C1-11: normalize for lookup

    def _find_idle(self, language: str) -> Sandbox | None:
        for sb in self._sandboxes:
            if sb.state == SandboxState.IDLE and sb.language == language:
                return sb
        return None

    # -- public API -----------------------------------------------------------

    def acquire(self, language: str, now: float | None = None) -> Sandbox:
        lang = self._normalize_language(language)
        now = time.monotonic() if now is None else now
        with self._lock:
            idle = self._find_idle(lang)
            if idle is not None:  # warm reuse
                idle.state = SandboxState.BUSY
                idle.last_used_at = now
                idle.warm = True
                return idle
            if len(self._sandboxes) >= self._max_size:
                self._evict_idle_locked(now)
                if len(self._sandboxes) >= self._max_size:
                    raise SandboxPoolError(f"pool full ({self._max_size})")
            sb = Sandbox(id=uuid.uuid4().hex, language=lang, state=SandboxState.BUSY,
                         created_at=now, last_used_at=now)
            self._sandboxes.append(sb)
            return sb

    def execute(self, sandbox_id: str, code: str) -> SandboxResult:
        """Mock execution — NEVER executes code (deterministic stub)."""
        with self._lock:
            sb = self._find_by_id(sandbox_id)
            if sb is None:
                raise SandboxPoolError(f"sandbox not found: {sandbox_id}")
            if sb.state != SandboxState.BUSY:
                raise SandboxPoolError(f"sandbox not busy: {sandbox_id}")
        return SandboxResult(
            ok=True, sandbox_id=sandbox_id, language=sb.language, warm=sb.warm,
            result={"mode": "stub", "executed": False, "stdout": "stub: no execution"},
        )

    def release(self, sandbox_id: str, now: float | None = None) -> None:
        """Reset state between runs (state back to idle). Same-thread v1 (C2-04)."""
        now = time.monotonic() if now is None else now
        with self._lock:
            sb = self._find_by_id(sandbox_id)
            if sb is None:
                raise SandboxPoolError(f"sandbox not found: {sandbox_id}")
            if sb.state != SandboxState.BUSY:
                raise SandboxPoolError(f"sandbox not busy: {sandbox_id}")
            sb.state = SandboxState.IDLE
            sb.last_used_at = now

    def destroy(self, sandbox_id: str) -> None:
        with self._lock:
            sb = self._find_by_id(sandbox_id)
            if sb is None:
                raise SandboxPoolError(f"sandbox not found: {sandbox_id}")
            sb.state = SandboxState.DESTROYED
            self._sandboxes.remove(sb)

    def health(self) -> dict:
        with self._lock:
            total = len(self._sandboxes)
            idle = sum(1 for s in self._sandboxes if s.state == SandboxState.IDLE)
            busy = total - idle
            return {"total": total, "idle": idle, "busy": busy, "max_size": self._max_size}

    def evict_idle(self, now: float | None = None) -> int:
        """Evict idle sandboxes whose last_used_at is older than idle_timeout_s."""
        now = time.monotonic() if now is None else now
        with self._lock:
            return self._evict_idle_locked(now)

    # -- internals ------------------------------------------------------------

    def _find_by_id(self, sandbox_id: str) -> Sandbox | None:
        for sb in self._sandboxes:
            if sb.id == sandbox_id:
                return sb
        return None

    def _evict_idle_locked(self, now: float) -> int:
        kept = []
        evicted = 0
        for sb in self._sandboxes:
            if sb.state == SandboxState.IDLE and (now - sb.last_used_at) >= self._idle_timeout_s:
                evicted += 1
            else:
                kept.append(sb)
        self._sandboxes = kept
        return evicted

    def _stats_for_test(self) -> dict:  # C1-12: not public API
        with self._lock:
            return {
                "total": len(self._sandboxes),
                "languages": sorted({s.language for s in self._sandboxes}),
                "warm_count": sum(1 for s in self._sandboxes if s.warm),
            }
