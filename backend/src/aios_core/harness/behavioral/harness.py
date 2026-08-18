"""BehavioralConformanceHarness (M13-P0, TASK-089): id="behavioral".

Chạy behavioral conformance qua H1 runner lifecycle (INV-017/018):
run() → engine.run(config) → report; verify() → strict fail-closed (INV-035).
Persist report qua state_service (pattern TestHarness/BenchmarkHarness).
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .contracts import ConformanceConfig, ConformanceReport, ConformanceStatus
from .engine import BehavioralConformanceEngine
from .errors import BehavioralConformanceError

logger = get_logger("aios.harness.behavioral")


class BehavioralConformanceHarness(Harness):
    """M13-P0 harness: id="behavioral" — N lần + repeat + fault + evidence + gate."""

    id = "behavioral"
    name = "Behavioral Conformance"
    version = "1.0.0"
    description = "Run scenario N times + repeat + fault-inject + evidence compare (M13-P0)"

    def __init__(
        self,
        engine: BehavioralConformanceEngine | None = None,
        *,
        state_service: StateService | None = None,
    ) -> None:
        self._engine = engine or BehavioralConformanceEngine()
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        raw = ctx.config.get("config")
        if raw is None:
            raise BehavioralConformanceError(
                "ctx.config['config'] missing (ConformanceConfig)"
            )
        config = (
            raw if isinstance(raw, ConformanceConfig)
            else ConformanceConfig.model_validate(raw)
        )
        report = self._engine.run(config)
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Persist TRƯỚC raise (pattern H2 AC5); strict → fail-closed (INV-035)."""
        report = ctx.config.get("_report")
        if report is None:
            raise BehavioralConformanceError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", True))
        self._persist(ctx, report, strict)
        if report.status != ConformanceStatus.PASS:
            if strict:
                raise BehavioralConformanceError(
                    f"behavioral conformance failed: {report.summary}"
                )
            logger.warning("behavioral warning (strict=False): %s", report.summary)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, report: ConformanceReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, behavioral={
                "profile": report.profile.value,
                "scenario_id": report.scenario_id,
                "iterations_total": report.iterations_total,
                "status": report.status.value,
                "deterministic": report.deterministic,
                "repeat_consistent": report.repeat_consistent,
                "fault_recovery_rate": report.fault_recovery_rate,
                "metrics": report.metrics,
                "findings": report.findings,
                "summary": report.summary,
                "reproducible": report.reproducible,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001 — evidence không chặn verdict
            logger.warning("behavioral state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_report(self, run_id: str) -> dict[str, Any] | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "behavioral" not in state:
            return None
        return state["behavioral"]