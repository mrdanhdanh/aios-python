"""ReleaseGateHarness (M13-P3, TASK-092): id="release".

Tách System Readiness ≠ Harness Trust — tổ hợp 2 score ĐỘC LẬP thành 1
release verdict. run() chạy CoverageHarness + MetaHarness qua public API
(HarnessRunner.create_context + harness.run) → capture payload → engine.
verify() strict fail-closed (INV-035). Persist qua state_service.
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from ..runner import HarnessRunner
from ..coverage.contracts import HarnessReadinessReport, HarnessReadinessStatus
from ..meta.contracts import MetaReport, MetaStatus
from .contracts import ReleaseGateReport, ReleaseGateStatus
from .engine import ReleaseGateEngine
from .errors import ReleaseGateError

logger = get_logger("aios.harness.release")


class ReleaseGateHarness(Harness):
    """M13-P3 harness: id="release" — System Readiness + Harness Trust gate."""

    id = "release"
    name = "release-gate"
    version = "1.0.0"
    description = "Release gate — System Readiness + Harness Trust (M13-P3)"

    def __init__(
        self,
        coverage_harness: Harness,
        meta_harness: Harness,
        *,
        state_service: StateService | None = None,
        engine: ReleaseGateEngine | None = None,
    ) -> None:
        # Dependency injection 2 sub-harness (KHÔNG import concrete class —
        # tuân INV-017; chỉ type Harness ABC). Engine default pure combiner.
        self._coverage_harness = coverage_harness
        self._meta_harness = meta_harness
        self._engine = engine or ReleaseGateEngine()
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        runner = HarnessRunner(state_service=self._state)
        readiness_payload = self._run_sub_payload(
            runner, self._coverage_harness, "coverage")
        readiness_model = self._build_readiness(readiness_payload)
        meta_payload = self._run_sub_payload(runner, self._meta_harness, "meta")
        meta_model = self._build_meta(meta_payload)
        release = self._engine.evaluate(readiness_model, meta_model)
        ctx.config["_report"] = release
        return release.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Persist TRƯỚC raise (pattern H2 AC5); strict → fail-closed (INV-035)."""
        report = ctx.config.get("_report")
        if report is None:
            raise ReleaseGateError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", True))
        self._persist(ctx, report, strict)
        if report.status != ReleaseGateStatus.PASS:
            if strict:
                raise ReleaseGateError(f"release blocked: {report.summary}")
            logger.warning("release warning (strict=False): %s", report.summary)

    # -- sub-harness orchestration ------------------------------------------

    def _run_sub_payload(
        self, runner: HarnessRunner, harness: Harness, target: str,
    ) -> dict | None:
        """Chạy sub-harness qua public API, capture payload.run() return.

        Fail-closed (critique-1 P1 + critique-2 P1): bất kỳ exception → None
        → caller coi như score FAIL → gate BLOCKED (KHÔNG crash).
        """
        try:
            sub_ctx = runner.create_context(
                harness, target, config={"strict": False})
            payload = harness.run(sub_ctx)
            if payload is None:
                raise RuntimeError("sub-harness run() returned None")
            return payload
        except Exception as exc:  # noqa: BLE001 — fail-closed: BLOCKED
            logger.warning("release gate sub-harness %s failed: %s",
                           target, exc)
            return None

    @staticmethod
    def _build_readiness(payload: dict | None) -> HarnessReadinessReport:
        if payload is None or "readiness" not in payload:
            return ReleaseGateHarness._failed_readiness()
        try:
            return HarnessReadinessReport(**payload["readiness"])
        except Exception:  # noqa: BLE001 — malformed → coi như NOT_READY
            return ReleaseGateHarness._failed_readiness()

    @staticmethod
    def _build_meta(payload: dict | None) -> MetaReport:
        if payload is None:
            return ReleaseGateHarness._failed_meta()
        try:
            return MetaReport(**payload)
        except Exception:  # noqa: BLE001 — malformed → coi như FAIL
            return ReleaseGateHarness._failed_meta()

    @staticmethod
    def _failed_readiness() -> HarnessReadinessReport:
        return HarnessReadinessReport(
            dimensions={}, overall=0.0,
            status=HarnessReadinessStatus.NOT_READY,
            hard_gates=[], summary="sub-harness failed",
            metrics={}, reproducible={})

    @staticmethod
    def _failed_meta() -> MetaReport:
        return MetaReport(
            cases=[], all_fail_closed=False, status=MetaStatus.FAIL,
            metrics={}, summary="sub-harness failed", reproducible={})

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, report: ReleaseGateReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, release={
                "status": report.status.value,
                "both_pass": report.both_pass,
                "system_readiness": report.system_readiness,
                "harness_trust": report.harness_trust,
                "summary": report.summary,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001 — never break verify
            logger.warning("release state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "release" not in state:
            return None
        return state["release"]
