"""Execution service: run ExecutionPlans with retry/timeout/cancel/snapshot."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from ...logging import get_logger
from ..events import EventType
from ..execution_plan import ExecutionPlan, PlanNode
from .events import EventService
from .permissions import PermissionScope
from .policy import PolicyRequest, PolicyService
from .resource import ResourceService
from .state import NODE_COMPLETED, NODE_FAILED, NODE_PENDING, NODE_RUNNING, StateService

logger = get_logger("aios.kernel.services.execution")

NodeRunner = Callable[[PlanNode, dict[str, Any]], Any]


class ExecutionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    status: ExecutionStatus
    execution_id: str
    node_results: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


class ExecutionService:
    """Execute an ExecutionPlan node-by-node.

    Runner contract: ``runner: dict[str, NodeRunner]`` mapping node_id to
    ``fn(node, results_so_far)``; the return value is stored as the node
    result; a missing entry marks the node failed ("no runner for node X").
    """

    def __init__(
        self,
        event_service: EventService,
        policy_service: PolicyService,
        state_service: StateService,
        resource_service: ResourceService,
    ) -> None:
        self._events = event_service
        self._policy = policy_service
        self._state = state_service
        self._resources = resource_service
        self._cancel_flags: dict[str, threading.Event] = {}
        self._lock = threading.RLock()

    # -- public ---------------------------------------------------------------

    def execute(self, plan: ExecutionPlan, runner: dict[str, NodeRunner]) -> ExecutionResult:
        execution_id = plan.id
        with self._lock:
            # Pending cancel checked BEFORE reset → immediate CANCELLED.
            flag = self._cancel_flags.get(execution_id)
            if flag is not None and flag.is_set():
                return ExecutionResult(ExecutionStatus.CANCELLED, execution_id, reason="cancelled")
            # No pending cancel → reset state + flag.
            self._state.delete(execution_id)
            self._cancel_flags[execution_id] = threading.Event()

        return self._run(execution_id, plan, runner, fresh=True)

    def cancel(self, execution_id: str) -> None:
        with self._lock:
            flag = self._cancel_flags.get(execution_id)
            if flag is None:
                # Register a pending-cancel so a future execute() returns
                # CANCELLED immediately (cancel-before-execute semantics).
                flag = threading.Event()
                flag.set()
                self._cancel_flags[execution_id] = flag
            else:
                flag.set()

    def resume(self, execution_id: str, runner: dict[str, NodeRunner]) -> ExecutionResult:
        state = self._state.get_state(execution_id)
        if state is None or "plan" not in state:
            return ExecutionResult(
                ExecutionStatus.FAILED, execution_id, reason="no snapshot state for resume"
            )
        plan = ExecutionPlan.model_validate(state["plan"])
        node_ids = {n.id for n in plan.nodes}
        state_ids = set(state.get("nodes", {}).keys())
        if not state_ids.issubset(node_ids):
            return ExecutionResult(
                ExecutionStatus.FAILED,
                execution_id,
                reason=f"state node ids mismatch plan: {state_ids - node_ids}",
            )
        with self._lock:
            self._cancel_flags[execution_id] = threading.Event()
        return self._run(execution_id, plan, runner, fresh=False, existing_state=state)

    # -- core -----------------------------------------------------------------

    def _run(
        self,
        execution_id: str,
        plan: ExecutionPlan,
        runner: dict[str, NodeRunner],
        fresh: bool,
        existing_state: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        flag = self._cancel_flags[execution_id]
        node_results: dict[str, Any] = {}
        tokens = int(plan.estimated_tokens or 0)
        slot_acquired = False
        tokens_acquired = False

        self._events.emit(
            EventType.WORKFLOW_STARTED,
            payload={"execution_id": execution_id, "plan_id": plan.id},
            source="execution_service",
        )

        try:
            # Pre-check: policy.
            scopes: list[PermissionScope] = []
            for perm in plan.required_permissions:
                try:
                    scopes.append(PermissionScope(perm))
                except ValueError:
                    logger.warning("Unknown permission scope %r (skipped)", perm)
            decision = self._policy.evaluate(
                PolicyRequest(scopes=scopes, tokens=tokens, internet=False)
            )
            if not decision.approved:
                reason = f"policy rejected: {decision.reason} ({decision.policy_version})"
                self._events.emit(
                    EventType.WORKFLOW_FAILED,
                    payload={"execution_id": execution_id, "plan_id": plan.id, "reason": reason},
                    source="execution_service",
                )
                return ExecutionResult(ExecutionStatus.FAILED, execution_id, reason=reason)
            if decision.requires_approval:
                self._events.emit(
                    EventType.WORKFLOW_FAILED,
                    payload={"execution_id": execution_id, "plan_id": plan.id, "reason": "approval required"},
                    source="execution_service",
                )
                return ExecutionResult(
                    ExecutionStatus.FAILED,
                    execution_id,
                    reason="approval required",
                )
            if decision.sandbox_required:
                logger.warning("sandbox_required set but sandboxing not enforced in v1")

            # Resources.
            if tokens and not self._resources.acquire_tokens(tokens):
                self._events.emit(
                    EventType.WORKFLOW_FAILED,
                    payload={"execution_id": execution_id, "plan_id": plan.id, "reason": "resource unavailable"},
                    source="execution_service",
                )
                return ExecutionResult(
                    ExecutionStatus.FAILED, execution_id, reason="resource unavailable"
                )
            tokens_acquired = True
            if not self._resources.acquire_slot():
                self._events.emit(
                    EventType.WORKFLOW_FAILED,
                    payload={"execution_id": execution_id, "plan_id": plan.id, "reason": "resource unavailable"},
                    source="execution_service",
                )
                return ExecutionResult(
                    ExecutionStatus.FAILED, execution_id, reason="resource unavailable"
                )
            slot_acquired = True

            # State init (fresh: from plan; resume: reuse existing nodes).
            if fresh:
                nodes_state = {n.id: NODE_PENDING for n in plan.nodes}
            else:
                nodes_state = dict(existing_state.get("nodes", {})) if existing_state else {}
                for n in plan.nodes:
                    nodes_state.setdefault(n.id, NODE_PENDING)
                # Reset failed/running → pending on resume.
                for node_id in list(nodes_state):
                    if nodes_state[node_id] != NODE_COMPLETED:
                        nodes_state[node_id] = NODE_PENDING
            self._state.set_state(
                execution_id,
                {
                    "plan": plan.to_dict(),
                    "nodes": nodes_state,
                    "results": dict(existing_state.get("results", {})) if existing_state else {},
                    "started_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Topological order: Kahn FIFO by plan.nodes order.
            order = self._topo_order(plan)
            for node_id in order:
                if flag.is_set():
                    self._events.emit(
                        EventType.WORKFLOW_CANCELLED,
                        payload={"execution_id": execution_id, "plan_id": plan.id, "reason": "cancelled"},
                        source="execution_service",
                    )
                    return ExecutionResult(
                        ExecutionStatus.CANCELLED, execution_id, node_results, reason="cancelled"
                    )
                node = next(n for n in plan.nodes if n.id == node_id)
                if nodes_state[node_id] == NODE_COMPLETED:
                    node_results[node_id] = self._state.get_state(execution_id)["results"].get(node_id)
                    continue
                nodes_state[node_id] = NODE_RUNNING
                # M1-only surrogate tool events (real tool events land in M2).
                self._events.emit(
                    EventType.TOOL_STARTED,
                    payload={"execution_id": execution_id, "node_id": node_id, "node_name": node.name},
                    source="execution_service",
                )
                result, ok = self._run_node(node, runner, node_results, flag)
                self._events.emit(
                    EventType.TOOL_FINISHED,
                    payload={"execution_id": execution_id, "node_id": node_id, "node_name": node.name, "ok": ok},
                    source="execution_service",
                )
                if not ok:
                    if result == "cancelled":
                        self._events.emit(
                            EventType.WORKFLOW_CANCELLED,
                            payload={"execution_id": execution_id, "plan_id": plan.id, "reason": result},
                            source="execution_service",
                        )
                    else:
                        self._events.emit(
                            EventType.WORKFLOW_FAILED,
                            payload={"execution_id": execution_id, "plan_id": plan.id, "reason": result},
                            source="execution_service",
                        )
                    return ExecutionResult(
                        ExecutionStatus.FAILED, execution_id, node_results, reason=result
                    )
                node_results[node_id] = result
                nodes_state[node_id] = NODE_COMPLETED
                self._state.update_state(execution_id, nodes=nodes_state, results=node_results)
                self._state.snapshot(execution_id)
                self._events.emit(
                    EventType.SNAPSHOT_SAVED,
                    payload={"execution_id": execution_id},
                    source="execution_service",
                )

            self._events.emit(
                EventType.WORKFLOW_COMPLETED,
                payload={"execution_id": execution_id, "plan_id": plan.id},
                source="execution_service",
            )
            return ExecutionResult(ExecutionStatus.COMPLETED, execution_id, node_results)

        except Exception as exc:  # noqa: BLE001
            logger.exception("Execution %s failed", execution_id)
            reason = f"unexpected: {exc}"
            self._events.emit(
                EventType.WORKFLOW_FAILED,
                payload={"execution_id": execution_id, "plan_id": plan.id, "reason": reason},
                source="execution_service",
            )
            return ExecutionResult(ExecutionStatus.FAILED, execution_id, node_results, reason=reason)
        finally:
            if tokens_acquired:
                self._resources.release_tokens(tokens)
            if slot_acquired:
                self._resources.release_slot()

    def _run_node(
        self, node: PlanNode, runner: dict[str, NodeRunner], results: dict[str, Any], flag: threading.Event
    ) -> tuple[Any, bool]:
        fn = runner.get(node.id)
        if fn is None:
            return f"no runner for node {node.id}", False

        attempts = 1 + node.retries
        for attempt in range(attempts):
            if flag.is_set():
                return "cancelled", False
            try:
                if node.timeout_s > 0:
                    box: dict[str, Any] = {}

                    def _target():
                        try:
                            box["result"] = fn(node, dict(results))
                        except Exception as exc:  # noqa: BLE001 — propagate to main thread
                            box["error"] = exc

                    thread = threading.Thread(target=_target, daemon=True)
                    thread.start()
                    thread.join(node.timeout_s)
                    if thread.is_alive():
                        logger.warning("Node %s timed out after %ss (attempt %d)", node.id, node.timeout_s, attempt + 1)
                        continue  # timeout counts as a retryable failure
                    if "error" in box:
                        raise box["error"]
                    return box.get("result"), True
                return fn(node, dict(results)), True
            except Exception as exc:  # noqa: BLE001
                logger.warning("Node %s failed (attempt %d/%d): %s", node.id, attempt + 1, attempts, exc)
                if attempt + 1 < attempts:
                    time.sleep(0.01)
                    continue
                return f"node {node.id} failed: {exc}", False
        return f"node {node.id} timed out", False

    @staticmethod
    def _topo_order(plan: ExecutionPlan) -> list[str]:
        """Kahn topological sort, FIFO by plan.nodes order."""
        remaining: dict[str, int] = {n.id: len(n.depends_on) for n in plan.nodes}
        dependents: dict[str, list[str]] = {n.id: [] for n in plan.nodes}
        for n in plan.nodes:
            for dep in n.depends_on:
                dependents[dep].append(n.id)
        ready = [n.id for n in plan.nodes if remaining[n.id] == 0]
        order: list[str] = []
        while ready:
            node_id = ready.pop(0)  # FIFO
            order.append(node_id)
            for dependent in dependents[node_id]:
                remaining[dependent] -= 1
                if remaining[dependent] == 0:
                    ready.append(dependent)
        return order
