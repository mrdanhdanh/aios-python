"""HealHarness (M14-P1, TASK-095): id="heal".

Candidate generate + risk scoring từ failure corpus.
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..diagnose.harness import DiagnoseHarness
from ..registry import Harness
from .contracts import CandidateReport
from .engine import HealEngine
from .errors import HealError

logger = get_logger("aios.harness.heal")


class HealHarness(Harness):
    """M14-P1 harness: id='heal' — candidate fixes + risk scoring."""

    id = "heal"
    name = "heal"
    version = "1.0.0"
    description = "Candidate generate + risk scoring (M14-P1)"

    def __init__(
        self,
        diagnose_harness: DiagnoseHarness | None = None,
        *,
        state_service: StateService | None = None,
        engine: HealEngine | None = None,
    ) -> None:
        self._diagnose = diagnose_harness
        self._engine = engine or HealEngine()
        self._state = state_service

    def run(self, ctx: HarnessContext) -> Any:
        corpus = self._diagnose.get_corpus() if self._diagnose else []
        report = self._engine.generate(corpus)
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        report = ctx.config.get("_report")
        if report is None:
            raise HealError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, report, strict)

    def _persist(self, ctx: HarnessContext, report: CandidateReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, heal={
                "total": report.total,
                "by_risk": report.by_risk,
                "summary": report.summary,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("heal state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "heal" not in state:
            return None
        return state["heal"]
