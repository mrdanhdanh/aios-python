"""MetaHarness (M13-P2, TASK-091): id="meta".

Verify the verifier qua H1 runner lifecycle (INV-017/018): run() →
engine.run() → report; verify() → strict fail-closed (INV-035). Persist
report qua state_service (pattern behavioral/coverage harness).
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .contracts import MetaReport, MetaStatus
from .engine import MetaHarnessEngine
from .errors import MetaError

logger = get_logger("aios.harness.meta")


class MetaHarness(Harness):
    """M13-P2 harness: id="meta" — verify the verifier (independent oracle)."""

    id = "meta"
    name = "meta-harness"  # P2-3: abstract name bắt buộc
    version = "1.0.0"
    description = "Verify the verifier — adversarial fail-closed (M13-P2)"

    def __init__(
        self,
        engine: MetaHarnessEngine | None = None,
        *,
        state_service: StateService | None = None,
        registry_ids: list[str] | None = None,
    ) -> None:
        # P2-2: route state_service vào engine cho case 8
        self._engine = engine or MetaHarnessEngine(
            state_service, registry_ids=registry_ids)
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        report = self._engine.run()
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Persist TRƯỚC raise (pattern H2 AC5); strict → fail-closed (INV-035)."""
        report = ctx.config.get("_report")
        if report is None:
            raise MetaError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", True))
        self._persist(ctx, report, strict)
        if report.status != MetaStatus.PASS:
            if strict:
                raise MetaError(f"meta-harness failed: {report.summary}")
            logger.warning("meta warning (strict=False): %s", report.summary)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, report: MetaReport, strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, meta={
                "status": report.status.value,
                "all_fail_closed": report.all_fail_closed,
                "summary": report.summary,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001 — never break verify
            logger.warning("meta state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "meta" not in state:
            return None
        return state["meta"]
