"""Verification State Model — INV-035 (M11-P0, TASK-078).

Terminal success duy nhất: PASS.
Terminal failure: FAIL | ERROR | BLOCKED.
Non-terminal (KHÔNG được coi là success): UNKNOWN | NOT_EXECUTED |
MISSING_EVIDENCE | SKIPPED.
"""

from __future__ import annotations

from enum import Enum


class VerificationState(str, Enum):
    """Trạng thái verification — INV-035 (R2 proposal M11)."""

    # Terminal
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    BLOCKED = "blocked"
    # Non-terminal — KHÔNG được coi là success
    UNKNOWN = "unknown"
    NOT_EXECUTED = "not_executed"
    MISSING_EVIDENCE = "missing_evidence"
    SKIPPED = "skipped"


class VerificationVerdict(str, Enum):
    """Verdict fail-closed sau normalize.

    PASS là verdict duy nhất biểu thị success. INCONCLUSIVE dành cho
    mọi non-terminal (fail-closed: không bao giờ map thành PASS).
    """

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"


TERMINAL_SUCCESS_STATES: frozenset[str] = frozenset({VerificationState.PASS.value})
TERMINAL_FAILURE_STATES: frozenset[str] = frozenset({
    VerificationState.FAIL.value,
    VerificationState.ERROR.value,
    VerificationState.BLOCKED.value,
})
NON_TERMINAL_STATES: frozenset[str] = frozenset({
    VerificationState.UNKNOWN.value,
    VerificationState.NOT_EXECUTED.value,
    VerificationState.MISSING_EVIDENCE.value,
    VerificationState.SKIPPED.value,
})
#: Chuyển đổi bị cấm theo INV-035 (non-terminal → PASS).
FORBIDDEN_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    (s, VerificationState.PASS.value) for s in NON_TERMINAL_STATES
)


def is_terminal_success(state: VerificationState | str) -> bool:
    """Chỉ PASS mới là terminal success (INV-035)."""
    value = state.value if isinstance(state, VerificationState) else state
    return value in TERMINAL_SUCCESS_STATES


def is_failure(state: VerificationState | str) -> bool:
    """FAIL | ERROR | BLOCKED là terminal failure."""
    value = state.value if isinstance(state, VerificationState) else state
    return value in TERMINAL_FAILURE_STATES


def is_non_terminal(state: VerificationState | str) -> bool:
    """UNKNOWN | NOT_EXECUTED | MISSING_EVIDENCE | SKIPPED — không phải success."""
    value = state.value if isinstance(state, VerificationState) else state
    return value in NON_TERMINAL_STATES


def is_terminal(state: VerificationState | str) -> bool:
    """Terminal = success (PASS) hoặc failure (FAIL/ERROR/BLOCKED)."""
    value = state.value if isinstance(state, VerificationState) else state
    return value in TERMINAL_SUCCESS_STATES or value in TERMINAL_FAILURE_STATES


def state_verdict_map(state: VerificationState | str) -> VerificationVerdict:
    """Map state → verdict fail-closed (không bao giờ non-terminal → PASS)."""
    value = state.value if isinstance(state, VerificationState) else state
    if value == VerificationState.PASS.value:
        return VerificationVerdict.PASS
    if value == VerificationState.FAIL.value:
        return VerificationVerdict.FAIL
    if value == VerificationState.ERROR.value:
        return VerificationVerdict.ERROR
    if value == VerificationState.BLOCKED.value:
        return VerificationVerdict.BLOCKED
    return VerificationVerdict.INCONCLUSIVE  # mọi non-terminal
