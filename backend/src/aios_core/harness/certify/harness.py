"""CertifyHarness (M14-P3, TASK-097): id='certify'.

Apply + rollback + certified baseline + audit.
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..heal.harness import HealHarness
from ..registry import Harness
from .contracts import CertifyReport, RemediationRecord
from .engine import CertifyEngine
from .errors import CertifyError

logger = get_logger("aios.harness.certify")


class CertifyHarness(Harness):
    """M14-P3 harness: id='certify' — apply + rollback + certified baseline."""

    id = "certify"
    name = "certify"
    version = "1.0.0"
    description = "Apply + rollback + certified baseline (M14-P3)"

    def __init__(
        self,
        heal_harness: HealHarness | None = None,
        *,
        state_service: StateService | None = None,
        engine: CertifyEngine | None = None,
    ) -> None:
        self._heal = heal_harness
        self._engine = engine or CertifyEngine()
        self._state = state_service
        self._records: list[RemediationRecord] = []

    def run(self, ctx: HarnessContext) -> Any:
        report = self._engine.build_report(self._records)
        ctx.config["_report"] = report
        return report.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        report = ctx.config.get("_report")
        if report is None:
            raise CertifyError("no report — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, report, strict)

    def apply_candidate(self, candidate) -> RemediationRecord:
        record = self._engine.apply(candidate)
        self._records.append(record)
        return record

    def rollback_record(self, record: RemediationRecord) -> RemediationRecord:
        rolled = self._engine.rollback(record)
        # Replace in records
        for i, r in enumerate(self._records):
            if r.failure_signature == record.failure_signature:
                self._records[i] = rolled
                break
        return rolled

    def certify_record(self, record: RemediationRecord) -> RemediationRecord:
        cert = self._engine.certify(record)
        for i, r in enumerate(self._records):
            if r.failure_signature == record.failure_signature:
                self._records[i] = cert
                break
        return cert

    def get_records(self) -> list[RemediationRecord]:
        return list(self._records)

    def _persist(self, ctx: HarnessContext, report: CertifyReport,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, certify={
                "total": report.total,
                "applied": report.applied,
                "certified": report.certified,
                "failed": report.failed,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("certify state persist failed: %s", exc)

    def get_report(self, run_id: str) -> dict | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "certify" not in state:
            return None
        return state["certify"]
