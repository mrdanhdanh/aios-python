"""Session memory: in-memory per-session cache (wrapper over ContextService)."""

from __future__ import annotations

from typing import Any

from ..kernel.services import ContextService, ContextScope


class SessionMemory:
    """Thin wrapper: SHARED scope + ``session:{session_id}:{key}`` namespace.

    TTL semantics delegated to ContextService (``ttl_s=None`` = never expires).
    """

    def __init__(self, context: ContextService, session_id: str) -> None:
        self._context = context
        self._session_id = session_id
        self._prefix = f"session:{session_id}:"

    def set(self, key: str, value: Any, ttl_s: float | None = None) -> None:
        self._context.set(ContextScope.SHARED, self._prefix + key, value, ttl_s=ttl_s)

    def get(self, key: str) -> Any:
        return self._context.get(ContextScope.SHARED, self._prefix + key)

    def delete(self, key: str) -> None:
        self._context.delete(ContextScope.SHARED, self._prefix + key)

    def clear_session(self) -> None:
        for stored_key in list(self._context.get_all(ContextScope.SHARED)):
            if stored_key.startswith(self._prefix):
                self._context.delete(ContextScope.SHARED, stored_key)
