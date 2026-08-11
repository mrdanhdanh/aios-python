"""Context service: scoped key-value store with TTL (monotonic clock)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class ContextScope(str, Enum):
    SYSTEM = "system"
    USER = "user"
    WORKFLOW = "workflow"
    AGENT = "agent"
    EXECUTION = "execution"
    SHARED = "shared"


@dataclass(frozen=True)
class Context:
    scope: ContextScope
    key: str
    value: Any
    ttl_s: float | None = None
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _created_mono: float = 0.0  # set by ContextService at creation (service clock)

    def is_expired(self, clock: Callable[[], float]) -> bool:
        if self.ttl_s is None:
            return False
        return clock() - self._created_mono >= self.ttl_s


class ContextService:
    """Scoped context store with lazy TTL eviction.

    ``clock`` is injectable (monotonic by default) so tests can fake time.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._store: dict[ContextScope, dict[str, Context]] = {scope: {} for scope in ContextScope}

    def set(self, scope: ContextScope, key: str, value: Any, ttl_s: float | None = None) -> Context:
        if not key:
            raise ValueError("key must not be empty")
        ctx = Context(
            scope=scope,
            key=key,
            value=value,
            ttl_s=ttl_s,
            _created_mono=self._clock(),
        )
        self._store[scope][key] = ctx
        return ctx

    def get(self, scope: ContextScope, key: str) -> Any:
        ctx = self._store[scope].get(key)
        if ctx is None:
            return None
        if ctx.is_expired(self._clock):
            del self._store[scope][key]
            return None
        return ctx.value

    def get_context(self, scope: ContextScope, key: str) -> Context | None:
        ctx = self._store[scope].get(key)
        if ctx is None:
            return None
        if ctx.is_expired(self._clock):
            del self._store[scope][key]
            return None
        return ctx

    def delete(self, scope: ContextScope, key: str) -> None:
        self._store[scope].pop(key, None)

    def get_all(self, scope: ContextScope) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, ctx in list(self._store[scope].items()):
            if ctx.is_expired(self._clock):
                del self._store[scope][key]
                continue
            result[key] = ctx.value
        return result
