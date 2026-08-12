"""Agent selector: intent → agent id."""

from __future__ import annotations

DEFAULT_MAP = {
    "coding": "coder",
    "medical": "doctor",
    "system": "system_doctor",
    "chat": "general",
}


class AgentSelector:
    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        merged = dict(DEFAULT_MAP)
        if mapping:
            merged.update(mapping)
        self._mapping = merged

    def select(self, intent: str) -> str | None:
        return self._mapping.get(intent)
