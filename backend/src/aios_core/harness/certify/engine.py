"""Certify engine (M14-P3, TASK-097): apply + rollback + certified baseline."""

from __future__ import annotations

import hashlib
import importlib.metadata
import platform
from datetime import datetime, timezone

from ..heal.contracts import CandidateFix
from .contracts import (
    CertifiedBaseline,
    CertifyReport,
    RemediationRecord,
    RemediationStatus,
)


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001
        return "unknown"


def _make_cert_id(sig: str) -> str:
    return hashlib.sha256(f"cert:{sig}:{datetime.now(timezone.utc).isoformat()}"
                          .encode()).hexdigest()[:12]


class CertifyEngine:
    """Thuần — apply + rollback + certified baseline (v1: deterministic)."""

    def apply(
        self,
        candidate: CandidateFix,
        *,
        before_version: str = "1.1.0",
    ) -> RemediationRecord:
        """Apply a candidate fix (v1: always succeeds for low/medium risk)."""
        now = datetime.now(timezone.utc)
        cert_id = _make_cert_id(candidate.failure_signature)

        baseline = CertifiedBaseline(
            before_version=before_version,
            candidate_version=f"{before_version}-fix-{candidate.failure_signature[:8]}",
            certification_id=cert_id,
            rollback_point=f"rollback:{before_version}",
            timestamp=now,
        )

        # v1: low/medium risk → applied; high/critical → failed (need human)
        if candidate.risk_level.value in ("high", "critical"):
            return RemediationRecord(
                failure_signature=candidate.failure_signature,
                candidate_description=candidate.description,
                risk_level=candidate.risk_level.value,
                status=RemediationStatus.FAILED,
                detail="high/critical risk — requires human approval",
                timestamp=now,
            )

        return RemediationRecord(
            failure_signature=candidate.failure_signature,
            candidate_description=candidate.description,
            risk_level=candidate.risk_level.value,
            status=RemediationStatus.APPLIED,
            baseline=baseline,
            detail=f"applied fix, cert_id={cert_id}",
            timestamp=now,
        )

    def rollback(self, record: RemediationRecord) -> RemediationRecord:
        """Rollback an applied fix."""
        if record.status != RemediationStatus.APPLIED:
            return record
        now = datetime.now(timezone.utc)
        return RemediationRecord(
            failure_signature=record.failure_signature,
            candidate_description=record.candidate_description,
            risk_level=record.risk_level,
            status=RemediationStatus.ROLLED_BACK,
            baseline=record.baseline,
            detail=f"rolled back from {record.baseline.rollback_point if record.baseline else 'unknown'}",
            timestamp=now,
        )

    def certify(self, record: RemediationRecord) -> RemediationRecord:
        """Certify an applied fix."""
        if record.status != RemediationStatus.APPLIED:
            return record
        now = datetime.now(timezone.utc)
        baseline = record.baseline
        if baseline:
            baseline = baseline.model_copy(update={
                "after_version": f"{baseline.before_version}-certified"})
        return RemediationRecord(
            failure_signature=record.failure_signature,
            candidate_description=record.candidate_description,
            risk_level=record.risk_level,
            status=RemediationStatus.CERTIFIED,
            baseline=baseline,
            detail="certified",
            timestamp=now,
        )

    def build_report(self, records: list[RemediationRecord]) -> CertifyReport:
        by_status: dict[str, int] = {}
        for r in records:
            by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return CertifyReport(
            total=len(records),
            applied=by_status.get("applied", 0),
            rolled_back=by_status.get("rolled_back", 0),
            certified=by_status.get("certified", 0),
            failed=by_status.get("failed", 0),
            records=records,
            summary=f"{len(records)} remediations: "
                    f"{by_status.get('certified', 0)} certified",
            reproducible={"aios_version": _aios_version(),
                          "python_version": platform.python_version()},
        )
