"""Execution graph contracts (TASK-027): 8-state graph model (PLAN §16-17).

INV-015 build gate lives here: ``ExecutionGraph`` validator calls
``validate_graph_acyclic`` which adapts Dependency edges to ``validate_dag``
(str-id view) — the literal ``validate_dag(`` call stays in this module for
the AST gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aios_core.kernel.dag import validate_dag
from aios_core.kernel.execution_plan import PlanNodeType


class GraphNodeStatus(str, Enum):
    """PLAN §17 — exactly 8 states."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class GraphRunStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JoinPolicy(str, Enum):
    ALL = "all"  # all deps SUCCEEDED (default)
    ANY = "any"  # >= 1 dep SUCCEEDED (join node)


class FailurePolicy(str, Enum):
    FAIL_FAST = "fail_fast"
    CONTINUE = "continue"
    SKIP_DEPENDENTS = "skip_dependents"


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str


class Dependency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    condition: Condition | None = None  # v1: must be None to execute (fail loud)


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: PlanNodeType
    name: str = ""
    agent: str = ""
    capabilities: list[str] = []
    depends_on: list[Dependency] = []  # topology source of truth
    join_policy: JoinPolicy = JoinPolicy.ALL
    timeout_s: float = 300.0
    retries: int = 0
    metadata: dict[str, Any] = {}

    @model_validator(mode="after")
    def _validate(self) -> "GraphNode":
        if self.timeout_s < 0:
            raise ValueError("timeout_s must be >= 0")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        seen: set[str] = set()
        for dep in self.depends_on:
            if dep.node_id == self.id:
                raise ValueError(f"node {self.id!r} cannot depend on itself")
            if dep.node_id in seen:
                raise ValueError(f"duplicate dependency {dep.node_id!r} on node {self.id!r}")
            seen.add(dep.node_id)
        return self


class GraphEdge(BaseModel):
    """Derived view (property of ExecutionGraph) — never a stored field."""

    model_config = ConfigDict(extra="forbid")

    from_id: str
    to_id: str
    condition: Condition | None = None


@dataclass
class _DagView:
    """Adapter: validate_dag expects ``depends_on: list[str]`` (C1-01)."""

    id: str
    depends_on: list[str]


def validate_graph_acyclic(nodes: list[GraphNode]) -> None:
    """INV-015 build gate — adapt Dependency edges to validate_dag (str ids)."""
    validate_dag([_DagView(n.id, [d.node_id for d in n.depends_on]) for n in nodes])


class ExecutionGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    nodes: list[GraphNode] = Field(min_length=1)
    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST
    metadata: dict[str, Any] = {}  # request_ref / permissions / resources / cost / tokens

    @model_validator(mode="after")
    def _validate(self) -> "ExecutionGraph":
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("node ids must be unique")
        validate_graph_acyclic(self.nodes)  # INV-015 build gate
        return self

    @property
    def edges(self) -> list[GraphEdge]:
        return [
            GraphEdge(from_id=dep.node_id, to_id=node.id, condition=dep.condition)
            for node in self.nodes
            for dep in node.depends_on
        ]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class GraphResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: GraphRunStatus
    execution_id: str
    node_statuses: dict[str, GraphNodeStatus] = {}
    node_results: dict[str, Any] = {}
    node_reasons: dict[str, str] = {}  # per-node failure reason
    execution_order: list[str] = []
    latency_ms: int = 0
    max_concurrent_running: int = 0
    failure_policy: FailurePolicy
    reason: str = ""
