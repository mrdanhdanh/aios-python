"""Readiness (TASK-034, H5): overall score + hard gates (INV — policy gate)."""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .checks import DoctorChecks
from .contracts import DoctorResult, DoctorStatus, HardGate, ReadinessReport
from .errors import ReadinessError

logger = get_logger("aios.harness.readiness")


class ReadinessScorer:
    """Thuần — dimensions + overall + hard gates (policy → overall order)."""

    def __init__(self, *, min_overall: float = 0.0,
                 policy_gate: bool = True) -> None:
        self._min_overall = min_overall
        self._policy_gate = policy_gate

    def score(self, results: list[DoctorResult],
              policy_violations: int = 0) -> ReadinessReport:
        dimensions: dict[str, float] = {}
        status_counts = {"passed": 0, "warning": 0, "error": 0, "unknown": 0}
        for result in results:
            dimensions[result.kind.value] = result.score
            status_counts[result.status.value] = \
                status_counts.get(result.status.value, 0) + 1
        overall = (sum(dimensions.values()) / len(dimensions)
                   if dimensions else 0.0)  # UNKNOWN → 0.0 (C1-02)
        gates: list[HardGate] = []
        if self._policy_gate:  # P2-02: policy gate trước
            policy_ok = policy_violations == 0
            gates.append(HardGate(
                name="policy",
                passed=policy_ok,
                detail=("no policy violations"
                        if policy_ok else
                        f"{policy_violations} policy violation(s)")))
        overall_ok = overall >= self._min_overall
        gates.append(HardGate(
            name="overall",
            passed=overall_ok,
            detail=f"overall {overall:.3f} >= {self._min_overall}"))
        ready = all(g.passed for g in gates)
        summary = self._summarize(ready, gates, overall)
        return ReadinessReport(
            dimensions=dimensions,
            overall=overall,
            hard_gates=gates,
            ready=ready,
            summary=summary,
            metrics={"doctors_run": len(results), **status_counts,
                     "hard_gates_total": len(gates),
                     "hard_gates_passed": sum(1 for g in gates if g.passed)},
            reproducible={"min_overall": self._min_overall,
                          "policy_gate": self._policy_gate},
        )

    @staticmethod
    def _summarize(ready: bool, gates: list[HardGate], overall: float) -> str:
        if ready:
            return f"READY (overall {overall:.1%})"
        if any(g.name == "policy" and not g.passed for g in gates):
            return f"RELEASE BLOCKED (policy gate): {overall:.1%}"  # P1-02
        return f"NOT READY (overall {overall:.1%})"


class ReadinessHarness(Harness):
    """H5 harness: id="readiness" — readiness score + hard gates."""

    id = "readiness"
    name = "Readiness"
    version = "1.0.0"
    description = "Overall readiness score with hard gates (policy first)"

    def __init__(self, checks: DoctorChecks, scorer: ReadinessScorer, *,
                 state_service: StateService | None = None) -> None:
        self._checks = checks
        self._scorer = scorer
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        policy_violations = int(ctx.config.get("policy_violations", 0))
        results = self._checks.run_all()
        report = self._scorer.score(results, policy_violations)
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        report = ctx.config.get("_report")
        if report is None:
            raise ReadinessError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, report, strict)
        if not report.ready:  # hard gate fail
            if strict:
                raise ReadinessError(f"RELEASE BLOCKED: {report.summary}")
            logger.warning("readiness warning (strict=False): %s", report.summary)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, report: ReadinessReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, readiness={
                "overall": report.overall,
                "ready": report.ready,
                "dimensions": report.dimensions,
                "hard_gates": [g.model_dump(mode="json")
                               for g in report.hard_gates],
                "summary": report.summary,
                "metrics": report.metrics,
                "reproducible": report.reproducible,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("readiness state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_report(self, run_id: str) -> dict[str, Any] | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "readiness" not in state:
            return None
        return state["readiness"]
