"""Normalizer: text → NormalizedRequest (no LLM)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..workflow.library import WorkflowLibrary

_PARAM_RE = re.compile(r"(\w+)=([^\s]+)")

DEFAULT_ALIASES = {
    "create api": "generate api",
    "khám bệnh": "medical",
    "xin chào": "hello",
}


@dataclass
class NormalizedRequest:
    intent: str | None = None  # None except special cases (#, !skill)
    params: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    source: str = "cli"
    confidence: float = 0.5


class Normalizer:
    """Lowercase/strip → params → alias → macro.

    Sets ``intent`` ONLY for two special cases: ``#...`` → chat (direct),
    ``!skill`` → skill. Everything else stays None (RuleEngine decides).
    """

    def __init__(
        self,
        alias: dict[str, str] | None = None,
        library: WorkflowLibrary | None = None,
    ) -> None:
        merged = dict(DEFAULT_ALIASES)
        if alias:
            merged.update(alias)  # custom overrides defaults
        self._aliases = merged
        self._library = library

    def normalize(self, text: str, source: str = "cli") -> NormalizedRequest:
        params: dict[str, Any] = {}
        stripped = text.strip().lower()

        # Direct chat marker: # at the start of the sentence.
        if re.match(r"^#", stripped):
            return NormalizedRequest(
                intent="chat",
                params={"content": stripped[1:].strip()},
                raw=text,
                source=source,
                confidence=1.0,
            )

        # Skill macro.
        if stripped.startswith("!"):
            skill = stripped[1:].strip()
            return NormalizedRequest(
                intent="skill",
                params={"skill": skill},
                raw=text,
                source=source,
                confidence=1.0,
            )

        # Extract key=value params (v1: no spaces in values).
        remaining = stripped
        for key, value in _PARAM_RE.findall(stripped):
            params[key] = value
            remaining = re.sub(rf"\b{key}={re.escape(value)}\b", "", remaining)
        remaining = re.sub(r"\s+", " ", remaining).strip()

        # Alias expansion (longest key first).
        for alias_key in sorted(self._aliases, key=len, reverse=True):
            if alias_key in remaining:
                remaining = remaining.replace(alias_key, self._aliases[alias_key])
                return NormalizedRequest(
                    intent=None,
                    params=params,
                    raw=text,
                    source=source,
                    confidence=1.0,
                )

        # Workflow macro: anchor ^@ (marker only; matcher validates).
        if remaining.startswith("@"):
            return NormalizedRequest(
                intent=None,
                params=params,
                raw=text,
                source=source,
                confidence=1.0,
            )

        return NormalizedRequest(
            intent=None,
            params=params,
            raw=text,
            source=source,
            confidence=0.5,
        )
