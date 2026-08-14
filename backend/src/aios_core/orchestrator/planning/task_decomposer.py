"""Task decomposer (TASK-026 §YC-3): deterministic 3-path decomposition.

WORKFLOW -> skipped (compiled directly). TEMPLATE -> TASK_TEMPLATES[intent].
RULE -> minimal skeleton by complexity/intent. OPEN -> empty (engine falls
to the LLM path). Never calls the planner itself.
"""

from __future__ import annotations

from typing import Any

from ...kernel.execution_plan import PlanNodeType
from .contracts import GoalComplexity, GoalAnalysis, PlanSource, TaskSpec
from .templates import get_template


class TaskDecomposer:
    """Deterministic decomposition — no LLM."""

    def decompose(self, goal: GoalAnalysis, request: Any) -> list[TaskSpec]:
        if goal.source is PlanSource.WORKFLOW:
            return []  # compiled directly by ExecutionPlanner (YC-7.1)
        template = get_template(goal.intent)
        if template is not None:
            return template.to_task_specs()  # TEMPLATE path
        if goal.complexity is GoalComplexity.OPEN:
            return []  # engine -> LLM path
        return self._rule_skeleton(goal)  # RULE path

    def _rule_skeleton(self, goal: GoalAnalysis) -> list[TaskSpec]:
        if goal.complexity is GoalComplexity.SIMPLE:
            node_type = (
                PlanNodeType.LLM if goal.intent == "chat" else PlanNodeType.TOOL
            )
            return [
                TaskSpec(
                    id="T1",
                    name=goal.intent,
                    type=node_type,
                    agent=self._agent_for(goal.intent),
                    depends_on=[],
                )
            ]
        # COMPLEX without template -> minimal rule skeleton (R3-3: e.g. test).
        return [
            TaskSpec(id="T1", name=f"{goal.intent}:write", type=PlanNodeType.TASK,
                     agent=self._agent_for(goal.intent), depends_on=[]),
            TaskSpec(id="T2", name=f"{goal.intent}:run", type=PlanNodeType.TOOL,
                     agent=self._agent_for(goal.intent), depends_on=["T1"]),
            TaskSpec(id="T3", name="report", type=PlanNodeType.TASK,
                     agent=self._agent_for(goal.intent), depends_on=["T2"]),
        ]

    @staticmethod
    def _agent_for(intent: str) -> str:
        return {"review": "coder", "test": "coder", "coding": "coder",
                "chat": "general", "doctor": "doctor"}.get(intent, "general")
