"""BenchmarkHarness (TASK-033, H4): benchmark + regression gate (INV-021)."""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .contracts import Baseline, BenchmarkReport
from .errors import BenchmarkError, GateBlockedError
from .gate import RegressionGate
from .runner import BenchmarkRunner

logger = get_logger("aios.harness.benchmark")


class BenchmarkHarness(Harness):
    """H4 harness: id="benchmark" — chạy scenarios, so baseline, gate release."""

    id = "benchmark"
    name = "Benchmark"
    version = "1.0.0"
    description = "Benchmark scenarios and block release on regression (INV-021)"

    def __init__(self, runner: BenchmarkRunner, gate: RegressionGate, *,
                 state_service: StateService | None = None) -> None:
        self._runner = runner
        self._gate = gate
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        scenario_ids = ctx.config.get("scenario_ids")
        if not scenario_ids:
            raise BenchmarkError("ctx.config['scenario_ids'] missing (list[str])")
        baseline = ctx.config.get("baseline") or Baseline()
        results, aggregate = self._runner.run(scenario_ids)
        report = self._gate.evaluate(results, baseline)
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        report = ctx.config.get("_report")
        if report is None:
            raise BenchmarkError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, report, strict)
        if not report.gate_passed:  # INV-021: block release
            if strict:
                raise GateBlockedError(
                    f"release blocked: {report.summary}")
            logger.warning("benchmark warning (strict=False): %s", report.summary)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, report: BenchmarkReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, benchmark={
                "baseline_version": report.baseline_version,
                "gate_passed": report.gate_passed,
                "scenarios_total": report.scenarios_total,
                "metrics": report.metrics,
                "findings": [f.model_dump(mode="json") for f in report.findings],
                "summary": report.summary,
                "metrics_count": report.metrics_count,
                "reproducible": report.reproducible,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("benchmark state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_report(self, run_id: str) -> dict[str, Any] | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "benchmark" not in state:
            return None
        return state["benchmark"]
