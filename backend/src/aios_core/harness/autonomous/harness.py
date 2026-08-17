"""AutonomousHarness (M15, TASK-099..102): id='autonomous'.

Autonomous loop orchestrator + trust budget + improvement suggestions.
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..certify.harness import CertifyHarness
from ..context import HarnessContext
from ..diagnose.harness import DiagnoseHarness
from ..heal.harness import HealHarness
from ..registry import Harness
from .contracts import AutonomousReport, LoopAction, LoopState, TrustBudget
from .engine import AutonomousEngine
from .errors import AutonomousError

logger = get_logger("aios.harness.autonomous")


class AutonomousHarness(Harness):
    """M15 harness: id='autonomous' — loop orchestrator + trust budget."""

    id = "autonomous"
    name = "autonomous"
    version = "1.0.0"
    description = "Autonomous loop + trust budget + improvement (M15)"

    def __init__(
        self,
        diagnose_harness: DiagnoseHarness | None = None,
        heal_harness: HealHarness | None = None,
        certify_harness: CertifyHarness | None = None,
        *,
        state_service: StateService | None = None,
        engine: AutonomousEngine | None = None,
    ) -> None:
        self._diagnose = diagnose_harness
        self._heal = heal_harness
        self._certify = certify_harness
        self._engine = engine or AutonomousEngine()
        self._state = state_service

    def run(self, ctx: HarnessContext) -> Any:
        budget = TrustBudget()
        failures = self._diagnose.get_corpus() if self._diagnose else []
        candidates_report = None
        if self._heal:
            from ..heal.engine import HealEngine
            candidates_report = HealEngine().generate(failures)
        else:
            from ..heal.contracts import CandidateReport
            candidates_report = CandidateReport(
                candidates=[], total=0, by_risk={}, summary="no heal",
                reproducible={})
        certifications = self._certify.get_records() if self._certify else []

        state = LoopState(
            iteration=0, action=LoopAction.CONTINUE,
            autonomy_level=self._engine._level, budget=budget,
            detail="initial state")
        action = self._engine.decide(state, failures, candidates_report,
                                     certifications)
        improvements = self._engine.suggest_improvements(failures, candidates_report)

        payload = {
            "action": action.value,
            "budget": budget.model_dump(),
            "failures": len(failures),
            "candidates": candidates_report.total,
            "improvements": [i.model_dump() for i in improvements],
            "autonomy_level": self._engine._level.value,
        }
        ctx.config["_payload"] = payload
        return payload

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        data = ctx.config.get("_payload")
        if data is None:
            raise AutonomousError("no payload — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, data, strict)

    def _persist(self, ctx: HarnessContext, data: dict, strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, autonomous={
                "action": data["action"],
                "autonomy_level": data["autonomy_level"],
                "failures": data["failures"],
                "candidates": data["candidates"],
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("autonomous state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "autonomous" not in state:
            return None
        return state["autonomous"]
