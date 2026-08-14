"""Execution verification package (TASK-030, H2)."""

from .contracts import (
    Check, CheckKind, CheckResult, EvidenceServices, VerificationResult,
    VerificationTask, Verdict,
)
from .errors import VerificationError
from .evidence import collect_evidence, has_critical_evidence
from .pipeline import build_result, compute_verdict, run_checks
from .replay import replay_verdict
from .verification import VerificationHarness

__all__ = [
    "Check", "CheckKind", "CheckResult", "EvidenceServices",
    "VerificationResult", "VerificationTask", "Verdict",
    "VerificationError",
    "collect_evidence", "has_critical_evidence",
    "build_result", "compute_verdict", "run_checks",
    "replay_verdict", "VerificationHarness",
]
