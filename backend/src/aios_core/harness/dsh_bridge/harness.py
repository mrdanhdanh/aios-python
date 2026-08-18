"""DSHBridgeHarness (M16, TASK-104..108): id='dsh'.

Independent verification oracle via DeepSeek Harness (dsh).
Provides truly independent verification path (separate codebase/process).
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .contracts import DSHConfig, OracleReport
from .engine import DSHBridgeEngine
from .errors import DSHBridgeError

logger = get_logger("aios.harness.dsh")


class DSHBridgeHarness(Harness):
    """M16 harness: id='dsh' — independent verification oracle via dsh."""

    id = "dsh"
    name = "dsh"
    version = "1.0.0"
    description = "Independent verification oracle via DeepSeek Harness (M16)"

    def __init__(
        self,
        *,
        state_service: StateService | None = None,
        engine: DSHBridgeEngine | None = None,
        config: DSHConfig | None = None,
    ) -> None:
        self._engine = engine or DSHBridgeEngine(config)
        self._state = state_service

    def run(self, ctx: HarnessContext) -> Any:
        report = self._engine.check_invariants()
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        report = ctx.config.get("_report")
        if report is None:
            raise DSHBridgeError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, report, strict)
        # Fail-closed: if dsh is configured but invariants fail → raise
        if strict and report.invariants_failed > 0:
            raise DSHBridgeError(
                f"dsh oracle: {report.invariants_failed} invariants failed")

    def _persist(self, ctx: HarnessContext, report: OracleReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, dsh={
                "status": report.dsh_status.value,
                "invariants_checked": report.invariants_checked,
                "invariants_passed": report.invariants_passed,
                "is_truly_independent": report.is_truly_independent,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("dsh state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "dsh" not in state:
            return None
        return state["dsh"]
