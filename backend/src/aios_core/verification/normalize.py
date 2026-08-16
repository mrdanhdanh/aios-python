"""Fail-closed normalization — INV-035 (M11-P0, TASK-078).

Bảng chuyển đổi 8×8: mọi non-terminal (UNKNOWN/NOT_EXECUTED/
MISSING_EVIDENCE/SKIPPED) → INCONCLUSIVE (không bao giờ PASS);
PASS → PASS; FAIL/ERROR/BLOCKED giữ nguyên.
"""

from __future__ import annotations

from .state import VerificationState, VerificationVerdict, state_verdict_map


def fail_closed_normalize(
    state: VerificationState | str,
    verdict: VerificationVerdict | str | None = None,
) -> VerificationVerdict:
    """Chuẩn hóa (state, verdict) → verdict fail-closed.

    Rules (INV-035):
      1. state non-terminal → INCONCLUSIVE (bất kể verdict claim PASS).
      2. state PASS → PASS.
      3. state FAIL/ERROR/BLOCKED → giữ nguyên.
      4. verdict truyền vào chỉ được coi là hợp lệ khi state tương thích;
         nếu verdict == PASS mà state != PASS → non-terminal rule thắng.
    """
    value = state.value if isinstance(state, VerificationState) else state
    if value == VerificationState.PASS.value:
        return VerificationVerdict.PASS
    if value == VerificationState.FAIL.value:
        return VerificationVerdict.FAIL
    if value == VerificationState.ERROR.value:
        return VerificationVerdict.ERROR
    if value == VerificationState.BLOCKED.value:
        return VerificationVerdict.BLOCKED
    # Non-terminal — fail-closed: không bao giờ thành PASS
    return VerificationVerdict.INCONCLUSIVE


def normalize_outcome(
    state: VerificationState | str,
    claimed_verdict: VerificationVerdict | str | None = None,
) -> tuple[VerificationVerdict, bool]:
    """Trả về (verdict fail-closed, violation?) — violation = claim PASS
    khi state non-terminal (bị cấm theo INV-035)."""
    verdict = fail_closed_normalize(state, claimed_verdict)
    claimed = (
        claimed_verdict.value
        if isinstance(claimed_verdict, VerificationVerdict)
        else (claimed_verdict or "")
    )
    value = state.value if isinstance(state, VerificationState) else state
    violation = (
        claimed == VerificationVerdict.PASS.value
        and value != VerificationState.PASS.value
    )
    return verdict, violation


def describe_transition_table() -> str:
    """Mô tả bảng chuyển đổi cho CLI `aiagent verify-state`."""
    lines = [
        "INV-035 — Verification Fail-Closed (state → verdict)",
        "=" * 46,
        f"{'state':<18}{'verdict':<14}{'terminal success':<18}",
    ]
    for s in VerificationState:
        verdict = fail_closed_normalize(s)
        success = "yes" if verdict == VerificationVerdict.PASS else "no"
        lines.append(f"{s.value:<18}{verdict.value:<14}{success:<18}")
    lines.append("")
    lines.append("Cấm: SKIPPED/UNKNOWN/NOT_EXECUTED/MISSING_EVIDENCE → PASS")
    return "\n".join(lines)
