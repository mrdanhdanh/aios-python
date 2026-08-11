"""Execution plan: declarative description of a planned workflow run."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanNodeType(str, Enum):
    TASK = "task"
    TOOL = "tool"
    LLM = "llm"
    DECISION = "decision"


class ExecutionPlanStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: PlanNodeType
    name: str
    agent: str = ""
    capabilities: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    timeout_s: int = 300
    retries: int = 0

    @model_validator(mode="after")
    def _validate_non_negative(self) -> "PlanNode":
        if self.timeout_s < 0:
            raise ValueError("timeout_s must be >= 0")
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        return self


class ExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    request_ref: str = ""
    nodes: list[PlanNode] = Field(min_length=1)
    estimated_cost: float = 0.0
    estimated_tokens: int = 0
    required_permissions: list[str] = Field(default_factory=list)
    required_resources: dict[str, Any] = Field(default_factory=dict)
    status: ExecutionPlanStatus = ExecutionPlanStatus.DRAFT
    created_at: str = ""  # ISO-8601, set by the builder

    @model_validator(mode="after")
    def _validate_plan(self) -> "ExecutionPlan":
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be >= 0")
        if self.estimated_tokens < 0:
            raise ValueError("estimated_tokens must be >= 0")

        node_ids = [n.id for n in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("node ids must be unique")

        ids = set(node_ids)
        for node in self.nodes:
            missing = [d for d in node.depends_on if d not in ids]
            if missing:
                raise ValueError(f"node {node.id!r} depends on unknown nodes: {missing}")

        # Cycle detection (3-color DFS, includes self-dependency).
        adj = {n.id: list(n.depends_on) for n in self.nodes}
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
        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ExecutionPlanBuilder:
    """Build an ExecutionPlan from a plain dict (validates strictly)."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionPlan:
        return ExecutionPlan.model_validate(data)
