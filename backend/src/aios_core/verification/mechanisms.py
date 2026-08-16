"""Default verification mechanisms — INV-035 (M11-P0, TASK-078).

Ba mechanism mặc định (fail-closed với component thật):
  1. security-check   — SecurityChecker → blocking/failures → FAIL/BLOCKED
  2. contract-check   — ContractChecker → breaking → FAIL
  3. harness-execution — compute_verdict: skipped → INCONCLUSIVE (KHÔNG PASS)
"""

from __future__ import annotations

from typing import Any

from .contracts import VerificationOutcome
from .state import VerificationState, VerificationVerdict


class SecurityMechanism:
    """security-check (M10-F3): blocking → BLOCKED; failures → FAIL."""

    id = "security-check"
    name = "Security Baseline 1.0"
    version = "1.0.0"

    def check(self) -> VerificationOutcome:
        from ..security import SecurityChecker

        report = SecurityChecker().run()
        if report.blocking:
            return VerificationOutcome(
                mechanism_id=self.id,
                state=VerificationState.BLOCKED,
                verdict=VerificationVerdict.BLOCKED,
                evidence=report.summary(),
            )
        failures = report.failures
        if failures:
            return VerificationOutcome(
                mechanism_id=self.id,
                state=VerificationState.FAIL,
                verdict=VerificationVerdict.FAIL,
                evidence=report.summary(),
            )
        return VerificationOutcome(
            mechanism_id=self.id,
            state=VerificationState.PASS,
            verdict=VerificationVerdict.PASS,
            evidence=report.summary(),
        )


class ContractMechanism:
    """contract-check (M10-F2): breaking → FAIL."""

    id = "contract-check"
    name = "Contract 1.0 Matrix"
    version = "1.0.0"

    def check(self) -> VerificationOutcome:
        from ..contracts.check import ContractChecker

        report = ContractChecker().check_all()
        if report.breaking_count:
            return VerificationOutcome(
                mechanism_id=self.id,
                state=VerificationState.FAIL,
                verdict=VerificationVerdict.FAIL,
                evidence=(f"breaking={report.breaking_count}, "
                          f"warnings={report.warning_count}"),
            )
        return VerificationOutcome(
            mechanism_id=self.id,
            state=VerificationState.PASS,
            verdict=VerificationVerdict.PASS,
            evidence=(f"breaking=0, warnings={report.warning_count}"),
        )


class HarnessExecutionMechanism:
    """harness-execution (H2): compute_verdict phải fail-closed.

    Structural + behavioral: build CheckResult(skipped=True) → compute_verdict
    phải trả INCONCLUSIVE (KHÔNG PASS) — nếu trả PASS → FAIL (vi phạm INV-035).
    """

    id = "harness-execution"
    name = "Execution Verification H2"
    version = "1.0.0"

    def check(self) -> VerificationOutcome:
        from ..harness.execution.contracts import Check, CheckKind, CheckResult
        from ..harness.execution.contracts import Verdict as H2Verdict
        from ..harness.execution.pipeline import compute_verdict

        check = Check(name="probe", kind=CheckKind.FILE_EXISTS, params={"path": "."})
        skipped = CheckResult(check=check, passed=False, skipped=True,
                              detail="skipped: probe")
        verdict = compute_verdict([skipped], has_critical_evidence=True)
        if verdict == H2Verdict.PASS:
            return VerificationOutcome(
                mechanism_id=self.id,
                state=VerificationState.FAIL,
                verdict=VerificationVerdict.FAIL,
                evidence="compute_verdict trả PASS khi check skipped — INV-035 VIOLATION",
            )
        return VerificationOutcome(
            mechanism_id=self.id,
            state=VerificationState.PASS,
            verdict=VerificationVerdict.PASS,
            evidence=f"compute_verdict(skipped) → {verdict.value} (fail-closed ✓)",
        )


def default_mechanisms() -> list[Any]:
    """Ba mechanism mặc định cho VerificationGate."""
    return [SecurityMechanism(), ContractMechanism(), HarnessExecutionMechanism()]
