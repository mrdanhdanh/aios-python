"""Rule engine: deterministic intent matching (no LLM)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RuleMatch:
    intent: str
    agent: str | None
    matched_pattern: str
    priority: int


class RuleEngine:
    """Match text to intents via word-boundary patterns.

    Total ordering: priority desc → longest pattern → insertion asc.
    """

    def __init__(self) -> None:
        self._rules: list[tuple[list[str], str, str | None, int]] = []

    def add_rule(
        self,
        patterns: list[str],
        intent: str,
        agent: str | None = None,
        priority: int = 0,
    ) -> None:
        self._rules.append((patterns, intent, agent, priority))

    def match(self, text: str) -> RuleMatch | None:
        lowered = text.lower()
        best: RuleMatch | None = None
        best_priority = -1
        best_length = -1
        best_order = 10**9
        for order, (patterns, intent, agent, priority) in enumerate(self._rules):
            for pattern in patterns:
                if re.search(rf"\b{re.escape(pattern)}\b", lowered):
                    length = len(pattern)
                    if (priority, length, -order) > (best_priority, best_length, -best_order):
                        best = RuleMatch(intent, agent, pattern, priority)
                        best_priority, best_length, best_order = priority, length, order
                    break  # one pattern per rule is enough
        return best


def default_rules() -> RuleEngine:
    """8 default rules (bảng đầy đủ từ spec TASK-010)."""
    engine = RuleEngine()
    engine.add_rule(["generate api", "create api"], "coding", "coder", priority=10)
    engine.add_rule(["medical", "doctor", "khám bệnh", "triệu chứng"], "medical", "doctor", priority=10)
    engine.add_rule(["system status", "system health"], "system", "system_doctor", priority=8)
    engine.add_rule(["install skill"], "skill", None, priority=8)
    engine.add_rule(["upgrade", "update system"], "upgrade", None, priority=8)
    engine.add_rule(["diagnose", "phân tích lỗi"], "diagnose", None, priority=8)
    engine.add_rule(["chat", "hello", "hi", "xin chào"], "chat", None, priority=5)
    engine.add_rule(["crud", "api generator"], "workflow", None, priority=4)
    return engine
