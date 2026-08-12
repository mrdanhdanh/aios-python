"""Execution plan: declarative description of a planned workflow run."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .dag import validate_dag


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
    timeout_s: float = 300.0
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
        validate_dag(self.nodes)
        return self

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ExecutionPlanBuilder:
    """Build an ExecutionPlan from a plain dict (validates strictly)."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionPlan:
        return ExecutionPlan.model_validate(data)
