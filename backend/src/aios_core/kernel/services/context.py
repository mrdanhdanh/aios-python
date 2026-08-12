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


# Inheritance chain: a scope falls back to its parent when a key is missing.
# SHARED is a root-shared scope (no upward inheritance). Mirrors the runtime
# layering SYSTEM <- USER <- WORKFLOW <- AGENT <- EXECUTION.
PARENT: dict[ContextScope, ContextScope | None] = {
    ContextScope.EXECUTION: ContextScope.AGENT,
    ContextScope.AGENT: ContextScope.WORKFLOW,
    ContextScope.WORKFLOW: ContextScope.USER,
    ContextScope.USER: ContextScope.SYSTEM,
    ContextScope.SYSTEM: None,
    ContextScope.SHARED: None,
}


class ContextService:
    """Scoped context store with lazy TTL eviction.

    ``clock`` is injectable (monotonic by default) so tests can fake time.
    Reads support optional parent-scope inheritance via ``inherit=True``.
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

    def get(self, scope: ContextScope, key: str, inherit: bool = False) -> Any:
        ctx = self._lookup(scope, key, inherit)
        return ctx.value if ctx is not None else None

    def get_context(self, scope: ContextScope, key: str, inherit: bool = False) -> Context | None:
        return self._lookup(scope, key, inherit)

    def _lookup(self, scope: ContextScope, key: str, inherit: bool) -> Context | None:
        current: ContextScope | None = scope
        visited: set[ContextScope] = set()
        while current is not None and current not in visited:
            visited.add(current)
            ctx = self._store[current].get(key)
            if ctx is not None and not ctx.is_expired(self._clock):
                return ctx
            if ctx is not None and ctx.is_expired(self._clock):
                del self._store[current][key]
            if not inherit:
                break
            current = PARENT.get(current)
        return None

    def delete(self, scope: ContextScope, key: str) -> None:
        self._store[scope].pop(key, None)

    def get_all(self, scope: ContextScope, inherit: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        current: ContextScope | None = scope
        visited: set[ContextScope] = set()
        while current is not None and current not in visited:
            visited.add(current)
            for key, ctx in list(self._store[current].items()):
                if ctx.is_expired(self._clock):
                    del self._store[current][key]
                    continue
                # First (most-specific) scope wins; don't shadow.
                result.setdefault(key, ctx.value)
            if not inherit:
                break
            current = PARENT.get(current)
        return result
