"""Planning engine contracts (TASK-026): goal analysis, tasks, risks,
validation report, planning result. All pydantic extra="forbid"."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ...kernel.execution_plan import ExecutionPlan, PlanNodeType


class PlanSource(str, Enum):
    """Planning ladder (PLAN §13): workflow → template → rule → llm."""

    WORKFLOW = "workflow"
    TEMPLATE = "template"
    RULE = "rule"
    LLM = "llm"


class GoalComplexity(str, Enum):
    SIMPLE = "simple"  # 1-2 steps, no decomposition needed
    COMPLEX = "complex"  # needs deterministic decomposition
    OPEN = "open"  # open-ended, needs LLM


class GoalAnalysis(BaseModel):
    """Deterministic analysis of a planning request."""

    model_config = ConfigDict(extra="forbid")

    intent: str  # normalized: chat|coding|review|test|doctor|system|skill|upgrade|diagnose
    target: str = ""
    complexity: GoalComplexity
    requirements: list[str] = []
    matched_workflow: str | None = None
    source: PlanSource = PlanSource.RULE  # R3-1: analyzer default RULE (engine may override)


class TaskSpec(BaseModel):
    """A decomposed task (pre-PlanNode)."""

    model_config = ConfigDict(extra="forbid")

    id: str  # "T1".."Tn"
    name: str
    type: PlanNodeType  # reuse kernel.execution_plan.PlanNodeType
    description: str = ""
    capabilities: list[str] = []
    agent: str = ""
    depends_on: list[str] = []
    timeout_s: float = 300.0
    retries: int = 0


class RiskItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: Literal["low", "medium", "high"]
    kind: str  # unknown_capability|missing_agent|high_cost|many_nodes|open_goal
    message: str


class RiskReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RiskItem] = []

    @property
    def highest(self) -> str | None:
        for level in ("high", "medium", "low"):
            if any(item.level == level for item in self.items):
                return level
        return None


class ValidationRule(str, Enum):
    """8 validation categories (PLAN §14 / INV-014)."""

    CONTRACT = "contract"
    CAPABILITY = "capability"
    PERMISSION = "permission"
    POLICY = "policy"
    DEPENDENCY = "dependency"
    RESOURCE = "resource"
    CYCLE = "cycle"
    TIMEOUT = "timeout"


class PlanValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: ValidationRule
    node_id: str = ""  # "" = plan-level
    message: str
    fatal: bool


class PlanValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[PlanValidationIssue] = []

    @property
    def valid(self) -> bool:
        return not any(issue.fatal for issue in self.issues)


class PlanningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: ExecutionPlan  # always present — invalid plans raise instead (C3-02)
    source: PlanSource
    llm_calls: int
    validation: PlanValidationReport
    needs_approval: bool = False
    reasoning: str = ""
    goal: GoalAnalysis | None = None
    risks: RiskReport = RiskReport()
    latency_ms: int = 0
