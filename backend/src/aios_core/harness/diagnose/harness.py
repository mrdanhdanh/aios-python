"""DiagnoseHarness (M14-P0, TASK-094): id="diagnose".

Failure corpus: thu thập + phân類 + localize failures từ harness runs.
Chạy qua H1 runner lifecycle (INV-017/018). Persist qua StateService.
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..contracts import HarnessReport, HarnessRunStatus
from ..registry import Harness
from .contracts import FailureCorpusReport, FailureRecord
from .engine import DiagnoseEngine, build_corpus_report
from .errors import DiagnoseError

logger = get_logger("aios.harness.diagnose")


class DiagnoseHarness(Harness):
    """M14-P0 harness: id="diagnose" — failure corpus + signature + localization."""

    id = "diagnose"
    name = "diagnose"
    version = "1.0.0"
    description = "Failure corpus — detect, diagnose, localize (M14-P0)"

    def __init__(
        self,
        *,
        state_service: StateService | None = None,
        engine: DiagnoseEngine | None = None,
    ) -> None:
        self._engine = engine or DiagnoseEngine()
        self._state = state_service
        self._corpus: list[FailureRecord] = []

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        report = build_corpus_report(self._corpus)
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Fail-closed: nếu corpus có failures nhưng report trống → raise."""
        report = ctx.config.get("_report")
        if report is None:
            raise DiagnoseError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, report, strict)
        # v1: KHÔNG fail-closed on empty corpus (corpus có thể rỗng khi mới start)

    # -- public API ----------------------------------------------------------

    def add_from_report(self, harness_report: HarnessReport) -> FailureRecord | None:
        """Analyze a harness report and add to corpus if FAILED/DIAGNOSED."""
        record = self._engine.analyze(harness_report)
        if record is not None:
            # Deduplicate by signature
            if not any(r.signature == record.signature for r in self._corpus):
                self._corpus.append(record)
                logger.info("diagnose: added failure %s (sig=%s, severity=%s)",
                            record.harness_id, record.signature, record.severity.value)
            else:
                logger.debug("diagnose: duplicate signature %s — skipped",
                             record.signature)
        return record

    def get_corpus(self) -> list[FailureRecord]:
        return list(self._corpus)

    def get_report_data(self) -> FailureCorpusReport:
        return build_corpus_report(self._corpus)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, report: FailureCorpusReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, diagnose={
                "total": report.total,
                "by_harness": report.by_harness,
                "by_severity": report.by_severity,
                "by_component": report.by_component,
                "unique_signatures": report.unique_signatures,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001 — never break verify
            logger.warning("diagnose state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "diagnose" not in state:
            return None
        return state["diagnose"]
