"""SimulateHarness (M14-P2, TASK-096): id='simulate'.

Simulation + Meta-Verify Gate — verify fix trong sandbox (KHÔNG relax criteria).
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..heal.contracts import CandidateReport
from ..heal.harness import HealHarness
from ..meta.harness import MetaHarness
from ..registry import Harness
from .contracts import SimulationReport
from .engine import SimulationEngine
from .errors import SimulationError

logger = get_logger("aios.harness.simulate")


class SimulateHarness(Harness):
    """M14-P2 harness: id='simulate' — simulation + meta-verify gate."""

    id = "simulate"
    name = "simulate"
    version = "1.0.0"
    description = "Simulation + Meta-Verify Gate (M14-P2)"

    def __init__(
        self,
        heal_harness: HealHarness | None = None,
        meta_harness: MetaHarness | None = None,
        *,
        state_service: StateService | None = None,
        engine: SimulationEngine | None = None,
    ) -> None:
        self._heal = heal_harness
        self._meta = meta_harness
        self._engine = engine or SimulationEngine()
        self._state = state_service

    def run(self, ctx: HarnessContext) -> Any:
        # Get candidates from heal
        heal_report = None
        if self._heal:
            heal_ctx = HarnessContext(
                run_id=ctx.run_id + ":heal", harness="heal", target="heal",
                started_at=ctx.started_at, config={"strict": False})
            heal_payload = self._heal.run(heal_ctx)
            heal_report = CandidateReport(**heal_payload) if heal_payload else None

        # Get meta report
        meta_report = None
        if self._meta:
            meta_ctx = HarnessContext(
                run_id=ctx.run_id + ":meta", harness="meta", target="meta",
                started_at=ctx.started_at, config={"strict": False})
            meta_payload = self._meta.run(meta_ctx)
            if meta_payload:
                from ..meta.contracts import MetaReport
                meta_report = MetaReport(**meta_payload)

        # Simulate each candidate
        simulations: list[SimulationReport] = []
        if heal_report:
            for candidate in heal_report.candidates:
                sim = self._engine.simulate(candidate, meta_report)
                simulations.append(sim)

        all_pass = all(s.result.value == "pass" for s in simulations) if simulations else True
        payload = {
            "simulations": [s.model_dump() for s in simulations],
            "total": len(simulations),
            "passed": sum(1 for s in simulations if s.result.value == "pass"),
            "all_pass": all_pass,
        }
        ctx.config["_payload"] = payload
        return payload

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        data = ctx.config.get("_payload")
        if data is None:
            raise SimulationError("no payload — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, data, strict)
        if not data.get("all_pass", True):
            if strict:
                raise SimulationError(
                    f"simulation failed: {data['passed']}/{data['total']} passed")

    def _persist(self, ctx: HarnessContext, data: dict, strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, simulate={
                "total": data["total"],
                "passed": data["passed"],
                "all_pass": data["all_pass"],
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("simulate state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "simulate" not in state:
            return None
        return state["simulate"]
