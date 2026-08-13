"""Assistant registry — Worker Plane lookup (TASK-013).

Thread-safe (RLock). Keyed by assistant.name (matches AgentSelector ids:
coder/doctor/system_doctor/general). Intent→assistant mapping stays in the
Control Plane (AgentSelector) — this registry only resolves via an injectable
selector callable (INV-005: no duplicate source of truth).
"""

from __future__ import annotations

import threading
from collections.abc import Callable

from .base import Assistant


class AssistantRegistry:
    def __init__(self, selector: Callable[[str], str | None] | None = None) -> None:
        self._selector = selector
        self._lock = threading.RLock()
        self._assistants: dict[str, Assistant] = {}

    def register(self, assistant: Assistant) -> None:
        with self._lock:
            if assistant.name in self._assistants:
                raise ValueError(f"assistant already registered: {assistant.name}")
            self._assistants[assistant.name] = assistant

    def get(self, name: str) -> Assistant | None:
        with self._lock:
            return self._assistants.get(name)

    def list(self) -> list[Assistant]:
        with self._lock:
            return list(self._assistants.values())

    def resolve_by_intent(self, intent: str) -> Assistant | None:
        """Resolve via the injectable selector (Control Plane owns mapping)."""
        if self._selector is None:
            return None
        name = self._selector(intent)
        if name is None:
            return None
        return self.get(name)
