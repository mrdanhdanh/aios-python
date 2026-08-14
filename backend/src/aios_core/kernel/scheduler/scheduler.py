"""Graph scheduler (TASK-028 §YC-3): resource-aware scheduling via public API.

WRAPS GraphExecutor (027) — gating lives in the runner wrapper at the exact
injection point 027 reserved. Never owns Resource/Execution implementation
(INV-016): only calls acquire_slot_wait/release_slot/stats/pending.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable

from aios_core.config import GraphSettings, SchedulerSettings
from aios_core.kernel.execution_plan import ExecutionPlan
from aios_core.kernel.graph import (
    ExecutionGraph,
    FailurePolicy,
    GraphExecutor,
    GraphNode,
    plan_to_graph,
)
from aios_core.kernel.scheduler.contracts import (
    NodeResourceMetrics,
    ScheduledGraphResult,
)
from aios_core.kernel.scheduler.errors import ResourceUnavailableError

GraphNodeRunner = Callable[[GraphNode, dict[str, Any]], Any]


class GraphScheduler:
    """Resource-gated DAG scheduling — orchestrates GraphExecutor + ResourceService."""

    def __init__(
        self,
        resource_service: Any,
        state_service: Any,
        *,
        executor: GraphExecutor | None = None,
        settings: SchedulerSettings | None = None,
        graph_settings: GraphSettings | None = None,
    ) -> None:
        self._resources = resource_service
        self._state = state_service
        self._settings = settings or SchedulerSettings()
        self._graph_settings = graph_settings or GraphSettings()
        # C2-06 v2: default executor honors graph settings (max_parallel).
        self._executor = executor or GraphExecutor(
            state_service, settings=self._graph_settings)
        self._lock = threading.RLock()

    def cancel(self, execution_id: str) -> None:
        """Delegate to GraphExecutor.cancel (C2-05)."""
        self._executor.cancel(execution_id)

    # -- schedule ---------------------------------------------------------------

    def schedule(
        self,
        graph: ExecutionGraph,
        runner: GraphNodeRunner,
        *,
        execution_id: str | None = None,
    ) -> ScheduledGraphResult:
        node_metrics: dict[str, NodeResourceMetrics] = {
            n.id: NodeResourceMetrics() for n in graph.nodes}  # pre-init (GIL-atomic)
        slots_held = 0
        peak = 0

        def gated(node: GraphNode, results_so_far: dict[str, Any]) -> Any:
            nonlocal slots_held, peak
            t0 = time.monotonic()
            acquired = False
            try:
                if not self._resources.acquire_slot_wait(
                        timeout=self._settings.resource_wait_timeout_s):
                    raise ResourceUnavailableError(
                        f"node {node.id}: resource wait timeout")
                acquired = True
                with self._lock:
                    node_metrics[node.id].resource_wait_ms += int(
                        (time.monotonic() - t0) * 1000)
                    node_metrics[node.id].slots_acquired += 1
                    slots_held += 1
                    peak = max(peak, slots_held)
                return runner(node, results_so_far)
            finally:
                if acquired:
                    with self._lock:
                        slots_held -= 1  # decrement BEFORE release (C3-06)
                    self._resources.release_slot()

        graph_result = self._executor.execute(
            graph, gated, execution_id=execution_id)
        queue_time_ms = max(
            (m.resource_wait_ms for m in node_metrics.values()), default=0)
        resource_stats = dict(self._resources.stats())
        metrics = {
            "node_metrics": {k: v.model_dump() for k, v in node_metrics.items()},
            "queue_time_ms": queue_time_ms,
            "peak_slots_used": peak,
            "resource_stats": resource_stats,
        }
        self._state.update_state(
            graph_result.execution_id, scheduler_metrics=metrics)
        return ScheduledGraphResult(
            execution_id=graph_result.execution_id,
            graph=graph_result,
            node_metrics=node_metrics,
            queue_time_ms=queue_time_ms,
            peak_slots_used=peak,
            resource_stats=resource_stats,
        )

    def schedule_plan(
        self,
        plan: ExecutionPlan,
        runner: GraphNodeRunner,
        *,
        failure_policy: FailurePolicy | None = None,
        execution_id: str | None = None,
    ) -> ScheduledGraphResult:
        if failure_policy is None:
            # C2-01 v2: resolve from graph settings (str → FailurePolicy).
            failure_policy = FailurePolicy(self._graph_settings.default_failure_policy)
        graph = plan_to_graph(plan, failure_policy=failure_policy)
        return self.schedule(graph, runner, execution_id=execution_id)
