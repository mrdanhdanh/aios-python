"""Graph executor (TASK-027 §YC-5): DAG execution with deterministic scheduling.

Wave loop: dead-end resolution → ready set (id asc) → PENDING→READY persist →
submit batch → join all futures → failure policy at wave boundary → repeat.
Workers own the READY→RUNNING transition and a start-guard (cancel/status
check before the first attempt). The literal ``validate_dag(`` call here
satisfies the INV-015 AST gate (defense-in-depth pre-validation).
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable

from aios_core.kernel.dag import validate_dag
from aios_core.kernel.services.state import StateService
from .contracts import (
    _DagView,
    ExecutionGraph,
    FailurePolicy,
    GraphNode,
    GraphNodeStatus,
    GraphResult,
    GraphRunStatus,
)
from .errors import GraphExecutionError, GraphValidationError
from .state_machine import GraphStateMachine

GraphNodeRunner = Callable[[GraphNode, dict[str, Any]], Any]


class GraphExecutor:
    """Orchestrates wave-based DAG execution (no God Object — state machine
    and contracts own the semantics)."""

    def __init__(self, state_service: StateService, settings: Any = None) -> None:
        from aios_core.config import GraphSettings  # absolute (scan-safe)

        if settings is None:
            settings = GraphSettings()  # R3-2
        else:
            try:
                if isinstance(settings, str):
                    settings = GraphSettings(default_failure_policy=settings)
            except Exception as exc:  # invalid policy string
                raise GraphValidationError(f"invalid graph settings: {exc}") from exc
        self._state = state_service
        self._settings = settings
        self._cancel_flags: dict[str, threading.Event] = {}
        self._lock = threading.RLock()

    # -- cancel --------------------------------------------------------------

    def cancel(self, execution_id: str) -> None:
        """Flag cancellation — returns immediately (C2-06 v1)."""
        with self._lock:
            flag = self._cancel_flags.setdefault(execution_id, threading.Event())
        flag.set()

    def _is_cancelled(self, execution_id: str) -> bool:
        with self._lock:
            flag = self._cancel_flags.get(execution_id)
        return flag is not None and flag.is_set()

    def _clear_cancel(self, execution_id: str) -> None:
        with self._lock:
            self._cancel_flags.pop(execution_id, None)

    # -- execute ---------------------------------------------------------------

    def execute(
        self,
        graph: ExecutionGraph,
        runner: GraphNodeRunner,
        execution_id: str | None = None,
    ) -> GraphResult:
        started = time.monotonic()
        execution_id = execution_id or f"graph:{graph.id}"  # C2-05 v2 namespace
        if runner is None:
            raise GraphValidationError("runner is required")

        # Pre-validate (INV-015 defense-in-depth) — literal validate_dag (C2-01 v2).
        try:
            validate_dag([_DagView(n.id, [d.node_id for d in n.depends_on])
                          for n in graph.nodes])
        except ValueError as exc:
            raise GraphValidationError(f"cyclic graph: {exc}") from exc
        for node in graph.nodes:
            for dep in node.depends_on:
                if dep.condition is not None:
                    raise GraphValidationError("conditions not supported in v1")

        if self._is_cancelled(execution_id):
            return self._result(graph, execution_id, GraphRunStatus.CANCELLED,
                                cancelled_before=True)

        node_ids = [n.id for n in graph.nodes]
        statuses: dict[str, GraphNodeStatus] = {
            nid: GraphNodeStatus.PENDING for nid in node_ids}
        results: dict[str, Any] = {nid: None for nid in node_ids}  # R2-1: pre-init
        reasons: dict[str, str] = {}
        order: list[str] = []
        max_concurrent = 0

        self._state.set_state(execution_id, {
            "graph": graph.to_dict(),
            "nodes": statuses,
            "results": results,
            "started_at": datetime.now(timezone.utc).isoformat(),  # C2-08
            "execution_order": order,
            "metrics": {},
        })

        cancelled = False
        try:
            while True:
                if self._is_cancelled(execution_id):
                    cancelled = True
                    self._mark_remaining(statuses, GraphNodeStatus.CANCELLED)
                    break

                # Dead-end resolution (PENDING nodes whose deps are all terminal).
                for node in graph.nodes:
                    if statuses[node.id] is not GraphNodeStatus.PENDING:
                        continue
                    deps = {dep.node_id: statuses[dep.node_id]
                            for dep in node.depends_on}
                    if deps and all(GraphStateMachine.is_terminal(s)
                                    for s in deps.values()):
                        if not GraphStateMachine.is_ready(node, deps):
                            statuses[node.id] = GraphStateMachine.dead_end_status(deps)

                ready = sorted(
                    (n for n in graph.nodes
                     if statuses[n.id] is GraphNodeStatus.PENDING
                     and GraphStateMachine.is_ready(
                         n, {dep.node_id: statuses[dep.node_id]
                             for dep in n.depends_on})),
                    key=lambda n: n.id,
                )
                if not ready:
                    if any(not GraphStateMachine.is_terminal(s)
                           for s in statuses.values()):
                        # Stuck READY/RUNNING node (pathological) — no progress.
                        raise GraphExecutionError(
                            "graph cannot make progress (node stuck)")
                    break  # all terminal

                # PENDING→READY persist (C1-02 — 028 reads READY from store).
                for node in ready:
                    statuses[node.id] = GraphNodeStatus.READY
                self._state.update_state(execution_id, nodes=statuses)

                max_concurrent = max(max_concurrent,
                                     min(len(ready), self._settings.max_parallel))
                workers = min(len(ready), self._settings.max_parallel)
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures = []
                    for node in ready:  # submit in id-asc order
                        order.append(node.id)  # main-side submit order (C2-03 v2)
                        futures.append(pool.submit(
                            self._run_node, graph, node, runner, statuses, results,
                            reasons, execution_id))
                    # Join ALL futures incl. queued before policy (R3-3).
                    for future in futures:
                        future.result()

                # Failure policy at wave boundary (C2-02 v1).
                failed = [n for n in graph.nodes
                          if statuses[n.id] is GraphNodeStatus.FAILED]
                if failed:
                    if graph.failure_policy is FailurePolicy.FAIL_FAST:
                        self._mark_remaining(statuses, GraphNodeStatus.BLOCKED)
                        break
                    if graph.failure_policy is FailurePolicy.SKIP_DEPENDENTS:
                        descendants = self._descendants(graph, {n.id for n in failed})
                        for nid in descendants:
                            if statuses[nid] in (GraphNodeStatus.PENDING,
                                                 GraphNodeStatus.READY):
                                statuses[nid] = GraphNodeStatus.SKIPPED
                        # CONTINUE-like: keep going; dead-end resolves next wave.
            # end while
        finally:
            self._clear_cancel(execution_id)

        outcome = GraphStateMachine.graph_outcome(statuses, cancelled)
        result = self._result(
            graph, execution_id, outcome, node_statuses=statuses,
            node_results=results, node_reasons=reasons, order=order,
            max_concurrent=max_concurrent, latency_ms=(
                int((time.monotonic() - started) * 1000)),
            cancelled_before=False,
        )
        self._state.update_state(
            execution_id,
            nodes=statuses,
            results=results,
            execution_order=order,
            metrics={
                "latency_ms": result.latency_ms,
                "max_concurrent_running": max_concurrent,
            },
        )
        return result

    # -- worker ---------------------------------------------------------------

    def _run_node(
        self,
        graph: ExecutionGraph,
        node: GraphNode,
        runner: GraphNodeRunner,
        statuses: dict[str, GraphNodeStatus],
        results: dict[str, Any],
        reasons: dict[str, str],
        execution_id: str,
    ) -> None:
        # Worker start-guard (C2-02 v2): cancel flag / already-terminal check.
        if self._is_cancelled(execution_id):
            statuses[node.id] = GraphNodeStatus.CANCELLED
            return
        if statuses[node.id] is not GraphNodeStatus.READY:
            return  # already terminal (policy raced) — do not overwrite
        statuses[node.id] = GraphNodeStatus.RUNNING  # worker-side (C2-03 v2)
        self._state.update_state(execution_id, nodes=statuses)

        last_error: Exception | None = None
        attempts = node.retries + 1
        for attempt in range(attempts):
            if self._is_cancelled(execution_id):  # before EVERY attempt (C2-09)
                statuses[node.id] = GraphNodeStatus.CANCELLED
                return
            try:
                results[node.id] = runner(node, dict(results))
                statuses[node.id] = GraphNodeStatus.SUCCEEDED
                return
            except Exception as exc:  # noqa: BLE001 — runner failure
                last_error = exc
        statuses[node.id] = GraphNodeStatus.FAILED
        reasons[node.id] = str(last_error)

    # -- helpers ---------------------------------------------------------------

    def _mark_remaining(
        self, statuses: dict[str, GraphNodeStatus], target: GraphNodeStatus
    ) -> None:
        for nid, status in statuses.items():
            if status in (GraphNodeStatus.PENDING, GraphNodeStatus.READY):
                statuses[nid] = target

    def _descendants(self, graph: ExecutionGraph, failed: set[str]) -> set[str]:
        children: dict[str, list[str]] = {}
        for node in graph.nodes:
            for dep in node.depends_on:
                children.setdefault(dep.node_id, []).append(node.id)
        result: set[str] = set()
        stack = list(failed)
        while stack:
            nid = stack.pop()
            for child in children.get(nid, []):
                if child not in result:
                    result.add(child)
                    stack.append(child)
        return result

    def _result(
        self,
        graph: ExecutionGraph,
        execution_id: str,
        status: GraphRunStatus,
        *,
        node_statuses: dict[str, GraphNodeStatus] | None = None,
        node_results: dict[str, Any] | None = None,
        node_reasons: dict[str, str] | None = None,
        order: list[str] | None = None,
        max_concurrent: int = 0,
        latency_ms: int = 0,
        cancelled_before: bool = False,
    ) -> GraphResult:
        reason = ""
        if status is GraphRunStatus.FAILED:
            first_failed = next(
                (nid for nid in (order or [])
                 if node_statuses and node_statuses.get(nid) is GraphNodeStatus.FAILED),
                "",
            )
            reason = (node_reasons or {}).get(first_failed, "graph failed")
        return GraphResult(
            status=status,
            execution_id=execution_id,
            node_statuses=node_statuses or {},
            node_results=node_results or {},
            node_reasons=node_reasons or {},
            execution_order=order or [],
            latency_ms=latency_ms,
            max_concurrent_running=max_concurrent,
            failure_policy=graph.failure_policy,
            reason=reason,
        )
