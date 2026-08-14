"""Graph state machine (TASK-027 §YC-3): pure transitions + readiness.

No I/O — deterministic functions only.
"""

from __future__ import annotations

from .contracts import (
    GraphNode,
    GraphNodeStatus,
    GraphRunStatus,
    JoinPolicy,
)

TRANSITIONS: dict[GraphNodeStatus, frozenset[GraphNodeStatus]] = {
    # READY and RUNNING both reachable from PENDING (C1-02: READY persist flow;
    # RUNNING kept for forward-compat / direct transitions — R3-4).
    GraphNodeStatus.PENDING: frozenset({
        GraphNodeStatus.READY, GraphNodeStatus.RUNNING,
        GraphNodeStatus.SKIPPED, GraphNodeStatus.BLOCKED, GraphNodeStatus.CANCELLED,
    }),
    GraphNodeStatus.READY: frozenset({
        GraphNodeStatus.RUNNING, GraphNodeStatus.SKIPPED,
        GraphNodeStatus.BLOCKED, GraphNodeStatus.CANCELLED,
    }),
    GraphNodeStatus.RUNNING: frozenset({
        GraphNodeStatus.SUCCEEDED, GraphNodeStatus.FAILED, GraphNodeStatus.CANCELLED,
    }),
    # SUCCEEDED/FAILED/SKIPPED/BLOCKED/CANCELLED: terminal.
    GraphNodeStatus.SUCCEEDED: frozenset(),
    GraphNodeStatus.FAILED: frozenset(),
    GraphNodeStatus.SKIPPED: frozenset(),
    GraphNodeStatus.BLOCKED: frozenset(),
    GraphNodeStatus.CANCELLED: frozenset(),
}

_TERMINAL = frozenset({
    GraphNodeStatus.SUCCEEDED, GraphNodeStatus.FAILED,
    GraphNodeStatus.SKIPPED, GraphNodeStatus.BLOCKED, GraphNodeStatus.CANCELLED,
})


class GraphStateMachine:
    """Pure state machine over the 8 graph node states."""

    @staticmethod
    def can_transition(current: GraphNodeStatus, target: GraphNodeStatus) -> bool:
        return target in TRANSITIONS.get(current, frozenset())

    @staticmethod
    def is_terminal(status: GraphNodeStatus) -> bool:
        return status in _TERMINAL

    @staticmethod
    def is_ready(node: GraphNode, dep_statuses: dict[str, GraphNodeStatus]) -> bool:
        if not node.depends_on:
            return True  # root
        if node.join_policy is JoinPolicy.ANY:
            return any(dep_statuses.get(dep.node_id) is GraphNodeStatus.SUCCEEDED
                       for dep in node.depends_on)
        return all(dep_statuses.get(dep.node_id) is GraphNodeStatus.SUCCEEDED
                   for dep in node.depends_on)

    @staticmethod
    def dead_end_status(dep_statuses: dict[str, GraphNodeStatus]) -> GraphNodeStatus:
        """All deps terminal but node cannot become READY."""
        if any(s in (GraphNodeStatus.CANCELLED, GraphNodeStatus.BLOCKED)
               for s in dep_statuses.values()):
            return GraphNodeStatus.BLOCKED  # highest priority
        return GraphNodeStatus.SKIPPED  # deps FAILED/SKIPPED

    @staticmethod
    def graph_outcome(
        node_statuses: dict[str, GraphNodeStatus], cancelled: bool
    ) -> GraphRunStatus:
        if cancelled:
            return GraphRunStatus.CANCELLED
        if any(s in (GraphNodeStatus.FAILED, GraphNodeStatus.BLOCKED)
               for s in node_statuses.values()):
            return GraphRunStatus.FAILED
        return GraphRunStatus.SUCCEEDED
