"""Heal engine (M14-P1, TASK-095): generate candidate fixes + risk scoring."""

from __future__ import annotations

import importlib.metadata
import platform

from ..diagnose.contracts import FailureRecord, FailureSeverity
from .contracts import CandidateFix, CandidateReport, RiskLevel


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001
        return "unknown"


# Severity → RiskLevel mapping
_SEVERITY_RISK: dict[str, RiskLevel] = {
    "low": RiskLevel.LOW,
    "medium": RiskLevel.MEDIUM,
    "high": RiskLevel.HIGH,
    "critical": RiskLevel.CRITICAL,
}


class HealEngine:
    """Thuần — generate candidate fixes from failure corpus + risk scoring."""

    def generate(self, corpus: list[FailureRecord]) -> CandidateReport:
        if not corpus:
            return CandidateReport(
                candidates=[], total=0, by_risk={},
                summary="no failures — nothing to fix",
                reproducible={"aios_version": _aios_version(),
                              "python_version": platform.python_version()})

        # Group by signature to detect repeated failures
        sig_counts: dict[str, int] = {}
        for r in corpus:
            sig_counts[r.signature] = sig_counts.get(r.signature, 0) + 1

        candidates: list[CandidateFix] = []
        seen_sigs: set[str] = set()

        for record in corpus:
            if record.signature in seen_sigs:
                continue
            seen_sigs.add(record.signature)

            count = sig_counts[record.signature]
            risk = _SEVERITY_RISK.get(record.severity.value, RiskLevel.LOW)
            # Repeated failures → higher confidence
            confidence = min(0.5 + count * 0.1, 1.0)
            # HIGH/CRITICAL severity → bump risk
            if record.severity in (FailureSeverity.HIGH, FailureSeverity.CRITICAL):
                confidence = min(confidence + 0.2, 1.0)

            action = self._suggest_action(record)
            candidates.append(CandidateFix(
                failure_signature=record.signature,
                description=f"{record.error_type} in {record.component}",
                risk_level=risk,
                confidence=confidence,
                suggested_action=action,
                evidence={"error_type": record.error_type,
                          "component": record.component,
                          "occurrence_count": count},
            ))

        by_risk: dict[str, int] = {}
        for c in candidates:
            by_risk[c.risk_level.value] = by_risk.get(c.risk_level.value, 0) + 1

        return CandidateReport(
            candidates=candidates,
            total=len(candidates),
            by_risk=by_risk,
            summary=f"{len(candidates)} candidates from {len(corpus)} failures",
            reproducible={"aios_version": _aios_version(),
                          "python_version": platform.python_version()})

    def _suggest_action(self, record: FailureRecord) -> str:
        if record.severity == FailureSeverity.LOW:
            return "retry"
        if record.severity == FailureSeverity.MEDIUM:
            return "fix_config"
        return "fix_code"
