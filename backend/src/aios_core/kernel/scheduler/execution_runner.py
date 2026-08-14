"""ExecutionService runner (TASK-028 §YC-4): adapter — one GraphNode per
1-node ExecutionPlan via ExecutionService public API (INV-016).

The literal ``execution_service.execute(`` call lives here (AST gate).
"""

from __future__ import annotations

from typing import Any, Callable

from aios_core.kernel.execution_plan import ExecutionPlan, PlanNode, PlanNodeType
from aios_core.kernel.graph import GraphNode
from aios_core.kernel.scheduler.errors import ExecutionNodeError

NodeRunner = Callable[[PlanNode, dict[str, Any]], Any]


def _noop_runner(node: PlanNode, results: dict[str, Any]) -> Any:
    return None


class ExecutionServiceRunner:
    """Envelope adapter: policy check per node + events + state + slot/token
    accounting happen inside ExecutionService; real capability execution is
    caller-injected via ``inner``."""

    def __init__(
        self,
        execution_service: Any,
        *,
        permissions: list[str] | None = None,
        tokens: int = 0,
        inner: NodeRunner | None = None,
    ) -> None:
        self.execution_service = execution_service  # C2-04: literal gate name
        self._permissions = permissions
        self._tokens = tokens
        self._inner = inner

    def __call__(self, node: GraphNode, results: dict[str, Any]) -> Any:
        plan = ExecutionPlan(
            id=f"gnode:{node.id}",  # namespace riêng (C3-03 giữ + giới hạn §7)
            request_ref="",
            nodes=[PlanNode(
                id=node.id,
                type=node.type,
                name=node.name or node.id,
                agent=node.agent,
                capabilities=list(node.capabilities),
                depends_on=[],
                timeout_s=node.timeout_s,
                retries=node.retries,
            )],
            required_permissions=list(self._permissions or []),  # R2-3
            estimated_tokens=self._tokens,
            required_resources={},
        )
        res = self.execution_service.execute(
            plan, {node.id: self._inner or _noop_runner})
        if res.status.value != "completed":
            raise ExecutionNodeError(f"node {node.id}: {res.reason}")
        return res.node_results.get(node.id)
