"""Autonomous contracts (M15, TASK-099..102): loop + improvement + certification + trust budget."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class LoopAction(str, Enum):
    CONTINUE = "continue"
    PAUSE = "pause"
    STOP = "stop"
    ASK_HUMAN = "ask_human"
    REPLAN = "replan"
    ROLLBACK = "rollback"


class AutonomyLevel(str, Enum):
    SUPERVISED = "supervised"    # every apply needs human approval
    ASSISTED = "assisted"        # low-risk auto, med/high need approval
    AUTONOMOUS = "autonomous"    # routine auto, high-risk still human


class TrustBudget(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    max_auto_repairs: int = 5
    max_failure_retries: int = 3
    max_consecutive_failures: int = 3
    current_repairs: int = 0
    current_retries: int = 0
    consecutive_failures: int = 0

    @property
    def exceeded(self) -> bool:
        return (self.current_repairs >= self.max_auto_repairs or
                self.consecutive_failures >= self.max_consecutive_failures)


class LoopState(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    iteration: int
    action: LoopAction
    autonomy_level: AutonomyLevel
    budget: TrustBudget
    detail: str


class ImprovementCandidate(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    description: str
    confidence: float
    source: str  # "failure_pattern" | "performance_drift" | "coverage_gap"
    risk_level: str
    evidence: dict


class AutonomousReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    iterations: int
    actions: list[LoopAction]
    improvements: list[ImprovementCandidate]
    budget_used: TrustBudget
    summary: str
    reproducible: dict
