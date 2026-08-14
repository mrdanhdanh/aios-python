"""Risk analyzer (TASK-026 §YC-6): deterministic risk assessment."""

from __future__ import annotations

from typing import Any

from ...kernel.execution_plan import PlanNodeType
from .contracts import GoalComplexity, GoalAnalysis, RiskItem, RiskReport, TaskSpec

_LLM_TOKENS = 2000
_OTHER_TOKENS = 200


class RiskAnalyzer:
    """Pure function — no LLM, deterministic (C2-03 v2)."""

    def analyze(self, goal: GoalAnalysis, tasks: list[TaskSpec], settings: Any) -> RiskReport:
        items: list[RiskItem] = []
        if goal.complexity is GoalComplexity.OPEN and not goal.matched_workflow:
            items.append(RiskItem(level="high", kind="open_goal",
                                  message="open-ended goal — LLM planning required"))
        if len(tasks) > settings.max_nodes // 2:
            items.append(RiskItem(level="medium", kind="many_nodes",
                                  message=f"{len(tasks)} nodes exceed half of max_nodes"))
        estimated = sum(
            _LLM_TOKENS if task.type is PlanNodeType.LLM else _OTHER_TOKENS
            for task in tasks
        )
        if estimated > settings.warn_token_threshold:
            items.append(RiskItem(level="medium", kind="high_cost",
                                  message=f"estimated {estimated} tokens > threshold"))
        if any(not task.agent for task in tasks):
            items.append(RiskItem(level="medium", kind="missing_agent",
                                  message="some tasks have no agent"))
        items.sort(key=lambda item: (item.level, item.kind))
        return RiskReport(items=items)
