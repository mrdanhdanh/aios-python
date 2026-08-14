"""Execution planner (TASK-026 §YC-7): build an ExecutionPlan DAG.

Known-workflow path compiles WorkflowDefinition nodes directly (0 LLM);
template/rule path converts TaskSpec -> PlanNode. Plan starts DRAFT; the
engine flips it to READY after validation passes.
"""

from __future__ import annotations

from typing import Any

from ...kernel.execution_plan import ExecutionPlan, ExecutionPlanStatus, PlanNode, PlanNodeType
from .contracts import GoalAnalysis, PlanSource, TaskSpec

_AGENT_PERMISSIONS = {
    "coder": ["filesystem"],
    "doctor": ["filesystem"],
    "general": [],
}


class ExecutionPlanner:
    """Deterministic plan builder."""

    def build(
        self,
        tasks: list[TaskSpec],
        goal: GoalAnalysis,
        request: Any,
        library: Any,
        settings: Any,
    ) -> ExecutionPlan:
        if len(tasks) > settings.max_nodes:
            from ..errors import PlanningError

            raise PlanningError(f"too many nodes: {len(tasks)} > {settings.max_nodes}")

        if goal.matched_workflow and library is not None:
            return self._build_from_workflow(goal, library, request)

        nodes = [
            PlanNode(
                id=task.id,
                type=task.type,
                name=task.name,
                agent=task.agent,
                capabilities=list(task.capabilities),
                depends_on=list(task.depends_on),
                timeout_s=task.timeout_s,
                retries=task.retries,
            )
            for task in tasks
        ]
        permissions = self._permissions_for(tasks)
        estimated_tokens = self._estimate_tokens(nodes)
        return ExecutionPlan(
            id=f"plan:{goal.source.value}:{goal.intent}",
            request_ref=request.text[:200],
            nodes=nodes,
            estimated_cost=0.0,
            estimated_tokens=estimated_tokens,
            required_permissions=permissions,
            required_resources={"max_tokens": settings.max_tokens if hasattr(settings, "max_tokens") else None},
            status=ExecutionPlanStatus.DRAFT,
            created_at="",
        )

    def _build_from_workflow(self, goal: GoalAnalysis, library: Any, request: Any) -> ExecutionPlan:
        definition = library.get(goal.matched_workflow)  # type: ignore[arg-type]
        nodes = [
            PlanNode(
                id=node.id,
                type=PlanNodeType(node.type.value) if hasattr(node.type, "value") else node.type,
                name=node.name,
                agent=getattr(node, "agent", ""),
                capabilities=list(getattr(node, "capabilities", [])),
                depends_on=list(getattr(node, "depends_on", [])),
                timeout_s=node.timeout_s if node.timeout_s is not None else definition.timeout_s,
                retries=node.retries if node.retries is not None else definition.retries,
            )
            for node in definition.nodes
        ]
        permissions = list(getattr(definition, "permissions", []))
        resources = dict(getattr(definition, "resources", {}))
        return ExecutionPlan(
            id=f"plan:{goal.source.value}:{goal.intent}",
            request_ref=request.text[:200],
            nodes=nodes,
            estimated_cost=0.0,
            estimated_tokens=self._estimate_tokens(nodes),
            required_permissions=permissions,
            required_resources=resources,
            status=ExecutionPlanStatus.DRAFT,
            created_at="",
        )

    @staticmethod
    def _estimate_tokens(nodes: list[PlanNode]) -> int:
        return sum(
            2000 if node.type is PlanNodeType.LLM else 200 for node in nodes
        )

    @staticmethod
    def _permissions_for(tasks: list[TaskSpec]) -> list[str]:
        permissions: list[str] = []
        for task in tasks:
            for scope in _AGENT_PERMISSIONS.get(task.agent, []):
                if scope not in permissions:
                    permissions.append(scope)
        return permissions
