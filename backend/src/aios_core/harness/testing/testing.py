"""TestHarness (TASK-031, H3): chạy scenario simulation qua H1 runner."""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .contracts import SimulationStatus
from .errors import TestError
from .simulation import SimulationRunner

logger = get_logger("aios.harness.testing")


class TestHarness(Harness):
    """H3 harness: id="test" — scenario → simulation → expected match."""

    id = "test"
    name = "Test & Simulation"
    version = "1.0.0"
    description = "Run scenarios in simulation mode (no side effects)"

    def __init__(self, runner: SimulationRunner | None = None, *,
                 state_service: StateService | None = None) -> None:
        self._runner = runner or SimulationRunner()
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        """P2-01: scenario từ ctx.config; runtime override qua config."""
        scenario = ctx.config.get("scenario")
        if scenario is None:
            raise TestError("ctx.config['scenario'] missing (Scenario)")
        runner = ctx.config.get("simulation_runner") or self._runner
        outcome = runner.run(scenario)
        ctx.config["_outcome"] = outcome
        return outcome.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Persist TRƯỚC raise (pattern H2 AC5); strict → raise TestError."""
        outcome = ctx.config.get("_outcome")
        if outcome is None:
            raise TestError("no outcome — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, outcome, strict)
        if outcome.status in (SimulationStatus.MISMATCH, SimulationStatus.ERROR):
            if strict:
                raise TestError(f"test failed: {outcome.summary}")
            logger.warning("test warning (strict=False): %s", outcome.summary)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, outcome, strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, testing={
                "scenario_id": outcome.scenario_id,
                "status": outcome.status.value,
                "matches": outcome.expectation_matches,
                "summary": outcome.summary,
                "metrics": outcome.metrics,
                "tool_calls": outcome.tool_calls[:100],
                "faults_injected": outcome.faults_injected,
                "recovery_events": outcome.recovery_events,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001 — evidence không chặn verdict
            logger.warning("testing state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_outcome(self, run_id: str) -> dict[str, Any] | None:
        """Trả dict compact từ state (P3-05)."""
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "testing" not in state:
            return None
        return state["testing"]
