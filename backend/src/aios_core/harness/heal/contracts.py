"""Heal contracts (M14-P1, TASK-095): candidate fixes + risk scoring."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class RiskLevel(str, Enum):
    LOW = "low"          # auto-apply allowed (M15)
    MEDIUM = "medium"    # requires human approval
    HIGH = "high"        # always requires human approval
    CRITICAL = "critical"  # never auto-apply


class CandidateFix(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    failure_signature: str
    description: str
    risk_level: RiskLevel
    confidence: float  # 0.0-1.0
    suggested_action: str  # "retry" | "fix_config" | "fix_code" | "skip"
    evidence: dict


class CandidateReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    candidates: list[CandidateFix]
    total: int
    by_risk: dict[str, int]
    summary: str
    reproducible: dict
