"""Execution graph (TASK-027): DAG execution + 8-state graph model (INV-015)."""

from .contracts import (
    Condition,
    Dependency,
    ExecutionGraph,
    FailurePolicy,
    GraphEdge,
    GraphNode,
    GraphNodeStatus,
    GraphResult,
    GraphRunStatus,
    JoinPolicy,
    validate_graph_acyclic,
)
from .converter import plan_to_graph
from .errors import GraphError, GraphExecutionError, GraphValidationError
from .executor import GraphExecutor, GraphNodeRunner
from .state_machine import GraphStateMachine

__all__ = [
    "Condition",
    "Dependency",
    "ExecutionGraph",
    "FailurePolicy",
    "GraphEdge",
    "GraphError",
    "GraphExecutionError",
    "GraphExecutor",
    "GraphNode",
    "GraphNodeRunner",
    "GraphNodeStatus",
    "GraphResult",
    "GraphRunStatus",
    "GraphStateMachine",
    "GraphValidationError",
    "JoinPolicy",
    "plan_to_graph",
    "validate_graph_acyclic",
]
