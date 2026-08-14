"""Goal analyzer (TASK-026 §YC-2): deterministic rule-based analysis.

Keyword tables are LOCAL to this module (C2-02 — no rule_engine import,
allow-list friendly). Known-workflow match uses local tokenizer
``re.split(r"[^a-z0-9]+", ...)`` (C2-06) — no dependence on library.search().
"""

from __future__ import annotations

import re
from typing import Any

from .contracts import GoalAnalysis, GoalComplexity, PlanSource

_WORD_RE = re.compile(r"[^a-z0-9]+")

# Intent keyword table (order matters — first match wins).
_INTENT_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("review", ("review", "analyze", "audit")),
    ("test", ("test", "write tests")),
    ("coding", ("fix", "refactor", "implement", "refactor", "build")),
    ("doctor", ("medical", "doctor", "symptom")),
    ("system", ("system", "status", "health")),
    ("skill", ("skill", "plugin")),
    ("upgrade", ("upgrade", "migrate")),
    ("diagnose", ("diagnose", "diagnostic")),
    ("cyclic", ("cyclic",)),  # test-only intent (cycle validation fixture)
    ("depbad", ("depbad",)),  # test-only intent (dependency validation fixture)
]

# Open-ended flags → OPEN complexity.
_OPEN_FLAGS = ("analyze the whole project", "propose", "design", "kiến trúc", "đề xuất")

# Intent → default complexity bucket.
_SIMPLE_INTENTS = {"chat", "system", "skill", "diagnose"}
_COMPLEX_INTENTS = {"review", "test", "coding"}


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.split(text.lower()))


class GoalAnalyzer:
    """Pure function analyzer — no LLM, no network, deterministic."""

    def analyze(self, request: Any, library: Any) -> GoalAnalysis:
        text = request.text
        lowered = text.lower()

        intent = self._detect_intent(lowered)
        target = self._detect_target(text, intent)
        complexity = self._detect_complexity(intent, target, lowered)

        matched = self._match_workflow(text, library)
        source = PlanSource.WORKFLOW if matched else PlanSource.RULE
        return GoalAnalysis(
            intent=intent,
            target=target,
            complexity=complexity,
            matched_workflow=matched,
            source=source,
        )

    def _detect_intent(self, lowered: str) -> str:
        for intent, keywords in _INTENT_KEYWORDS:
            if any(keyword in lowered for keyword in keywords):
                return intent
        return "chat"

    def _detect_target(self, text: str, intent: str) -> str:
        lowered = text.lower()
        for _, keywords in _INTENT_KEYWORDS:
            for keyword in keywords:
                idx = lowered.find(keyword)
                if idx >= 0:
                    rest = text[idx + len(keyword):].strip(" :,.-")
                    return rest.split(" và")[0].split(" and ")[0].strip() if rest else ""
        return ""

    def _detect_complexity(self, intent: str, target: str, lowered: str) -> GoalComplexity:
        if any(flag in lowered for flag in _OPEN_FLAGS):
            return GoalComplexity.OPEN
        if intent in _SIMPLE_INTENTS and not target:
            return GoalComplexity.SIMPLE
        if intent in _COMPLEX_INTENTS and target:
            return GoalComplexity.COMPLEX
        if intent == "chat":
            return GoalComplexity.SIMPLE
        return GoalComplexity.COMPLEX

    def _match_workflow(self, text: str, library: Any) -> str | None:
        """Local token match: pick the workflow whose name shares the most
        tokens with the request text (tie-break: name asc)."""
        if library is None:
            return None
        text_tokens = _tokens(text)
        best: str | None = None
        best_count = 0
        for name in library.list():
            name_tokens = _tokens(name)
            overlap = len(text_tokens & name_tokens)
            if overlap > 0 and (overlap > best_count or (
                overlap == best_count and (best is None or name < best)
            )):
                best = name
                best_count = overlap
        return best
