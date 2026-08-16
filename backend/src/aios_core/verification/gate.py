"""VerificationGate — enforce INV-035 (M11-P0, TASK-078).

Gate quy tắc:
  - verdict PASS ⟺ state == PASS
  - state non-terminal mà verdict == PASS → VIOLATION (fail-closed)
  - mechanism check() raise exception → BLOCKED (fail-closed)
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from .contracts import VerificationMechanism, VerificationOutcome
from .normalize import normalize_outcome
from .state import VerificationState, VerificationVerdict


class VerificationGateReport(BaseModel):
    """Kết quả gate toàn bộ mechanisms."""

    model_config = ConfigDict(extra="forbid")

    outcomes: list[VerificationOutcome] = []
    violations: list[str] = []  # mechanism_id có verdict PASS khi state non-terminal
    fail_closed: bool = True  # False nếu có violation


class VerificationGate:
    """Chặn mọi mechanism chuyển non-terminal thành PASS (INV-035)."""

    def __init__(self, mechanisms: list[VerificationMechanism] | None = None) -> None:
        self.mechanisms = list(mechanisms or [])

    def check_mechanism(self, mechanism: VerificationMechanism) -> VerificationOutcome:
        """Check một mechanism — exception → BLOCKED (fail-closed).

        Trả outcome THÔ (chưa normalize) — check_all chịu trách nhiệm
        normalize + detect violation (INV-035).
        """
        try:
            outcome = mechanism.check()
        except Exception as exc:  # noqa: BLE001 — INV-035: exception → BLOCKED
            return VerificationOutcome(
                mechanism_id=getattr(mechanism, "id", "unknown"),
                state=VerificationState.BLOCKED,
                verdict=VerificationVerdict.BLOCKED,
                evidence=f"check raised: {exc}",
            )
        if not isinstance(outcome, VerificationOutcome):
            return VerificationOutcome(
                mechanism_id=getattr(mechanism, "id", "unknown"),
                state=VerificationState.ERROR,
                verdict=VerificationVerdict.ERROR,
                evidence="check() must return VerificationOutcome",
            )
        return outcome

    def check_all(self) -> VerificationGateReport:
        outcomes: list[VerificationOutcome] = []
        violations: list[str] = []
        for m in self.mechanisms:
            raw = self.check_mechanism(m)
            # Detect violation trên raw CLAIM trước khi normalize:
            # state non-terminal mà verdict claim PASS → vi phạm INV-035
            if (
                raw.verdict == VerificationVerdict.PASS
                and raw.state != VerificationState.PASS
            ):
                violations.append(raw.mechanism_id)
            # Fail-closed normalize: non-terminal + claim PASS → INCONCLUSIVE
            verdict, _ = normalize_outcome(raw.state, raw.verdict)
            outcomes.append(raw.model_copy(update={"verdict": verdict}))
        return VerificationGateReport(
            outcomes=outcomes,
            violations=violations,
            fail_closed=len(violations) == 0,
        )

    def is_fail_closed(self) -> bool:
        return self.check_all().fail_closed


def format_gate_report(report: VerificationGateReport) -> str:
    lines = ["Verification Gate — INV-035 fail-closed", "=" * 46]
    for o in report.outcomes:
        sym = "✓" if o.verdict == VerificationVerdict.PASS else "✗"
        lines.append(
            f"{sym} {o.mechanism_id:<24} state={o.state.value:<16} "
            f"verdict={o.verdict.value}"
        )
        if o.evidence:
            lines.append(f"   evidence: {o.evidence}")
    lines.append("")
    if report.violations:
        lines.append(f"VIOLATIONS (non-terminal → PASS): {report.violations}")
        lines.append("FAIL-CLOSED: NO — release blocked (INV-035)")
    else:
        lines.append("FAIL-CLOSED: YES — mọi mechanism tôn trọng INV-035")
    return "\n".join(lines)
