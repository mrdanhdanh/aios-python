"""Execution graph converter (TASK-027 §YC-4): ExecutionPlan → ExecutionGraph."""

from __future__ import annotations

from typing import Any

from aios_core.kernel.execution_plan import ExecutionPlan, PlanNode
from .contracts import (
    Dependency,
    ExecutionGraph,
    FailurePolicy,
    GraphNode,
)
from .errors import GraphValidationError


def plan_to_graph(
    plan: ExecutionPlan,
    *,
    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST,
) -> ExecutionGraph:
    """Deterministic convert (TASK-026 output → graph). Never returns a
    cyclic graph — wraps build errors as GraphValidationError (INV-015)."""
    nodes = []
    for raw in plan.nodes:
        node = raw if isinstance(raw, PlanNode) else PlanNode.model_validate(raw)
        nodes.append(
            GraphNode(
                id=node.id,
                type=node.type,
                name=node.name,
                agent=node.agent,
                capabilities=list(node.capabilities),
                depends_on=[Dependency(node_id=dep) for dep in node.depends_on],
                timeout_s=node.timeout_s,
                retries=node.retries,
            )
        )
    try:
        return ExecutionGraph(
            id=plan.id,
            nodes=nodes,
            failure_policy=failure_policy,
            metadata={
                "source": "execution_plan",
                "request_ref": plan.request_ref,
                "required_permissions": list(plan.required_permissions),
                "required_resources": dict(plan.required_resources),
                "estimated_cost": plan.estimated_cost,
                "estimated_tokens": plan.estimated_tokens,
            },
        )
    except Exception as exc:  # ValidationError (cycle/unknown/duplicate ids)
        raise GraphValidationError(f"invalid plan for graph: {exc}") from exc
