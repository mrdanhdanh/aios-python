"""DAG validation helper (shared by ExecutionPlan and WorkflowDefinition).

Raises ValueError (pydantic wraps it into ValidationError). Order of checks:
unique ids → unknown dependencies → cycle.
"""

from __future__ import annotations

from typing import Any, Iterable


def validate_dag(nodes: Iterable[Any]) -> None:
    """Validate a node list: unique ids, existing deps, acyclic (incl. self)."""
    node_ids = [n.id for n in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("node ids must be unique")

    ids = set(node_ids)
    for node in nodes:
        missing = [d for d in node.depends_on if d not in ids]
        if missing:
            raise ValueError(f"node {node.id!r} depends on unknown nodes: {missing}")

    # Cycle detection (3-color DFS, includes self-dependency).
    adj = {n.id: list(n.depends_on) for n in nodes}
    state: dict[str, int] = {}  # 0=unvisited, 1=in-progress, 2=done

    def visit(node_id: str) -> None:
        s = state.get(node_id, 0)
        if s == 2:
            return
        if s == 1:
            raise ValueError(f"cycle detected in node dependencies: {node_id}")
        state[node_id] = 1
        for dep in adj[node_id]:
            visit(dep)
        state[node_id] = 2

    for node_id in ids:
        visit(node_id)
