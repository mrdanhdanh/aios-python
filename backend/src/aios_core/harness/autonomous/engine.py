"""Autonomous engine (M15, TASK-099..102): loop orchestrator + trust budget."""

from __future__ import annotations

import importlib.metadata
import platform

from ..diagnose.contracts import FailureRecord
from ..heal.contracts import CandidateReport
from ..certify.contracts import RemediationRecord
from .contracts import (
    AutonomyLevel,
    ImprovementCandidate,
    LoopAction,
    LoopState,
    TrustBudget,
)


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001
        return "unknown"


class AutonomousEngine:
    """Thuần — autonomous loop orchestrator + trust budget enforcement."""

    def __init__(
        self,
        *,
        autonomy_level: AutonomyLevel = AutonomyLevel.SUPERVISED,
        budget: TrustBudget | None = None,
    ) -> None:
        self._level = autonomy_level
        self._budget = budget or TrustBudget()

    def decide(self, state: LoopState, failures: list[FailureRecord],
               candidates: CandidateReport,
               certifications: list[RemediationRecord]) -> LoopAction:
        """Decide next action based on current state + evidence."""
        budget = state.budget

        # Kill-switch: budget exceeded → STOP
        if budget.exceeded:
            return LoopAction.STOP

        # No failures → done
        if not failures and not candidates.candidates:
            return LoopAction.STOP

        # High-risk candidates need human approval
        high_risk = [c for c in candidates.candidates
                     if c.risk_level.value in ("high", "critical")]
        if high_risk and self._level == AutonomyLevel.SUPERVISED:
            return LoopAction.ASK_HUMAN

        # Low-risk + assisted/autonomous → continue
        if self._level in (AutonomyLevel.ASSISTED, AutonomyLevel.AUTONOMOUS):
            return LoopAction.CONTINUE

        # Supervised default → ask human
        return LoopAction.ASK_HUMAN

    def record_repair(self, budget: TrustBudget) -> TrustBudget:
        return budget.model_copy(update={
            "current_repairs": budget.current_repairs + 1})

    def record_failure(self, budget: TrustBudget) -> TrustBudget:
        return budget.model_copy(update={
            "consecutive_failures": budget.consecutive_failures + 1,
            "current_retries": budget.current_retries + 1})

    def record_success(self, budget: TrustBudget) -> TrustBudget:
        return budget.model_copy(update={"consecutive_failures": 0})

    def suggest_improvements(self, failures: list[FailureRecord],
                             candidates: CandidateReport
                             ) -> list[ImprovementCandidate]:
        improvements: list[ImprovementCandidate] = []
        if failures:
            sig_count: dict[str, int] = {}
            for f in failures:
                sig_count[f.signature] = sig_count.get(f.signature, 0) + 1
            for sig, count in sig_count.items():
                if count >= 2:
                    improvements.append(ImprovementCandidate(
                        description=f"Repeated failure pattern: {sig}",
                        confidence=min(0.5 + count * 0.1, 1.0),
                        source="failure_pattern",
                        risk_level="medium",
                        evidence={"occurrence_count": count}))
        return improvements
