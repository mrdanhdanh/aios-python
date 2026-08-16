"""Verification Kernel — INV-035 Verification Fail-Closed (M11-P0, TASK-078).

Core invariant:
    Không một verification mechanism nào được phép chuyển trạng thái
    UNKNOWN / NOT EXECUTED / MISSING EVIDENCE (non-terminal) thành PASS.

Verification State Model:
  - Terminal success duy nhất: PASS
  - Terminal failure: FAIL | ERROR | BLOCKED
  - Non-terminal (KHÔNG được coi là success): UNKNOWN | NOT_EXECUTED |
    MISSING_EVIDENCE | SKIPPED
  - Cấm chuyển đổi: SKIPPED → PASS, UNKNOWN → PASS, MISSING_EVIDENCE → PASS
"""

from __future__ import annotations

from .contracts import (
    VerificationMechanism,
    VerificationOutcome,
    VerificationVerdict,
)
from .gate import VerificationGate, VerificationGateReport
from .mechanisms import default_mechanisms
from .normalize import fail_closed_normalize
from .state import (
    NON_TERMINAL_STATES,
    VerificationState,
    is_failure,
    is_non_terminal,
    is_terminal,
    is_terminal_success,
)

__all__ = [
    "NON_TERMINAL_STATES",
    "VerificationState",
    "VerificationVerdict",
    "VerificationOutcome",
    "VerificationMechanism",
    "VerificationGate",
    "VerificationGateReport",
    "fail_closed_normalize",
    "default_mechanisms",
    "is_failure",
    "is_non_terminal",
    "is_terminal",
    "is_terminal_success",
]
