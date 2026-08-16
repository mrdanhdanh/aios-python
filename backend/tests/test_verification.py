"""Tests INV-035 Verification Fail-Closed — M11-P0 (TASK-078).

Cover: state model (8 states), normalize bảng 8×8, gate violations +
exception → BLOCKED, CheckResult skipped/error, security/contract normalize,
integration mechanism thật.
"""

from __future__ import annotations

import pytest

from aios_core.harness.execution.contracts import Check, CheckKind, CheckResult
from aios_core.harness.execution.contracts import Verdict as H2Verdict
from aios_core.harness.execution.pipeline import compute_verdict
from aios_core.security.contracts import SecurityReport, SecurityStatus
from aios_core.security.checks import SecurityChecker, SecurityChecks
from aios_core.verification import (
    VerificationGate,
    VerificationOutcome,
    VerificationState,
    VerificationVerdict,
    default_mechanisms,
    fail_closed_normalize,
    is_failure,
    is_non_terminal,
    is_terminal_success,
)


# -- AC1: state model --------------------------------------------------------

def test_state_model_has_8_states():
    states = {s.value for s in VerificationState}
    assert states == {
        "pass", "fail", "error", "blocked",
        "unknown", "not_executed", "missing_evidence", "skipped",
    }


def test_terminal_success_only_pass():
    for s in VerificationState:
        assert is_terminal_success(s) == (s == VerificationState.PASS)


# -- AC2: classification ------------------------------------------------------

def test_non_terminal_classification():
    non_terminal = {
        VerificationState.UNKNOWN, VerificationState.NOT_EXECUTED,
        VerificationState.MISSING_EVIDENCE, VerificationState.SKIPPED,
    }
    for s in VerificationState:
        assert is_non_terminal(s) == (s in non_terminal)


def test_failure_classification():
    failures = {
        VerificationState.FAIL, VerificationState.ERROR, VerificationState.BLOCKED,
    }
    for s in VerificationState:
        assert is_failure(s) == (s in failures)


# -- AC3: normalize bảng 8×8 --------------------------------------------------

@pytest.mark.parametrize(
    "state,expected",
    [
        (VerificationState.PASS, VerificationVerdict.PASS),
        (VerificationState.FAIL, VerificationVerdict.FAIL),
        (VerificationState.ERROR, VerificationVerdict.ERROR),
        (VerificationState.BLOCKED, VerificationVerdict.BLOCKED),
        (VerificationState.UNKNOWN, VerificationVerdict.INCONCLUSIVE),
        (VerificationState.NOT_EXECUTED, VerificationVerdict.INCONCLUSIVE),
        (VerificationState.MISSING_EVIDENCE, VerificationVerdict.INCONCLUSIVE),
        (VerificationState.SKIPPED, VerificationVerdict.INCONCLUSIVE),
    ],
)
def test_normalize_full_table(state, expected):
    assert fail_closed_normalize(state) == expected


@pytest.mark.parametrize(
    "state,claimed",
    [
        # Claim PASS từ mọi non-terminal → vẫn INCONCLUSIVE (INV-035)
        (VerificationState.SKIPPED, VerificationVerdict.PASS),
        (VerificationState.UNKNOWN, VerificationVerdict.PASS),
        (VerificationState.MISSING_EVIDENCE, VerificationVerdict.PASS),
        (VerificationState.NOT_EXECUTED, VerificationVerdict.PASS),
        # Claim FAIL từ non-terminal → INCONCLUSIVE (fail-closed, không mạnh tay hơn)
        (VerificationState.SKIPPED, VerificationVerdict.FAIL),
        (VerificationState.UNKNOWN, VerificationVerdict.FAIL),
    ],
)
def test_normalize_forbidden_transitions(state, claimed):
    assert fail_closed_normalize(state, claimed) == VerificationVerdict.INCONCLUSIVE


# -- AC4: gate ----------------------------------------------------------------

class _SkipClaimPassMechanism:
    id = "mock-skip-pass"
    name = "Mock: skipped → PASS"
    version = "0.0.0"

    def check(self) -> VerificationOutcome:
        # Vi phạm INV-035: state SKIPPED nhưng claim PASS
        return VerificationOutcome(
            mechanism_id=self.id,
            state=VerificationState.SKIPPED,
            verdict=VerificationVerdict.PASS,
            evidence="mock skip → PASS",
        )


class _GoodMechanism:
    id = "mock-good"
    name = "Mock: pass"
    version = "0.0.0"

    def check(self) -> VerificationOutcome:
        return VerificationOutcome(
            mechanism_id=self.id,
            state=VerificationState.PASS,
            verdict=VerificationVerdict.PASS,
            evidence="ok",
        )


class _ExplodingMechanism:
    id = "mock-explode"
    name = "Mock: raise"
    version = "0.0.0"

    def check(self) -> VerificationOutcome:
        raise RuntimeError("browser failed to launch")


def test_gate_chains_skip_to_pass_violation():
    report = VerificationGate([_SkipClaimPassMechanism()]).check_all()
    assert report.violations == ["mock-skip-pass"]
    assert report.fail_closed is False
    # Verdict bị normalize: INCONCLUSIVE, không PASS
    assert report.outcomes[0].verdict == VerificationVerdict.INCONCLUSIVE


def test_gate_passes_clean_mechanism():
    report = VerificationGate([_GoodMechanism()]).check_all()
    assert report.violations == []
    assert report.fail_closed is True
    assert report.outcomes[0].verdict == VerificationVerdict.PASS


def test_gate_exception_is_blocked():
    report = VerificationGate([_ExplodingMechanism()]).check_all()
    assert report.outcomes[0].state == VerificationState.BLOCKED
    assert report.outcomes[0].verdict == VerificationVerdict.BLOCKED
    assert report.fail_closed is True  # không violation nhưng cũng không PASS


def test_gate_mixed_mechanisms():
    report = VerificationGate([_GoodMechanism(), _SkipClaimPassMechanism()]).check_all()
    assert report.violations == ["mock-skip-pass"]
    assert report.fail_closed is False


# -- AC5: CheckResult skipped/error → không PASS ------------------------------

def _result(skipped: bool = False, passed: bool = False, error: str = "") -> CheckResult:
    return CheckResult(
        check=Check(name="probe", kind=CheckKind.FILE_EXISTS, params={"path": "."}),
        passed=passed, skipped=skipped, error=error,
    )


def test_check_result_skipped_never_pass_even_if_passed_true():
    r = _result(skipped=True, passed=True)
    assert r.effectively_passed is False
    assert compute_verdict([r], has_critical_evidence=True) == H2Verdict.INCONCLUSIVE


def test_check_result_error_never_pass():
    r = _result(passed=True, error="boom")
    assert r.effectively_passed is False
    assert compute_verdict([r], has_critical_evidence=True) == H2Verdict.INCONCLUSIVE


def test_check_result_error_with_passed_false_is_fail():
    r = _result(passed=False, error="boom")
    assert compute_verdict([r], has_critical_evidence=True) == H2Verdict.INCONCLUSIVE


def test_check_result_clean_pass_still_pass():
    r = _result(passed=True)
    assert r.effectively_passed is True
    assert compute_verdict([r], has_critical_evidence=True) == H2Verdict.PASS


# -- AC8: security normalize ----------------------------------------------------

class _BrokenChecks(SecurityChecks):
    def run_all(self):  # type: ignore[override]
        raise RuntimeError("security checks unavailable")


def test_security_checker_exception_is_skipped_not_pass():
    checker = SecurityChecker(checks=_BrokenChecks())
    report = checker.run()
    assert report.skipped == ["all: security checks unavailable"]
    assert "INCONCLUSIVE" in report.summary()  # không báo SECURE


def test_security_report_skipped_field_default_empty():
    report = SecurityReport()
    assert report.skipped == []
    assert "0 skipped" in report.summary()


# -- AC4b: default mechanisms thật --------------------------------------------

def test_default_mechanisms_are_fail_closed():
    """Chạy gate với 3 mechanism thật — phải fail_closed=True."""
    report = VerificationGate(default_mechanisms()).check_all()
    assert len(report.outcomes) == 3
    ids = {o.mechanism_id for o in report.outcomes}
    assert ids == {"security-check", "contract-check", "harness-execution"}
    assert report.fail_closed is True
    for o in report.outcomes:
        # Không mechanism nào PASS khi state non-terminal
        if o.state != VerificationState.PASS:
            assert o.verdict != VerificationVerdict.PASS


def test_harness_execution_mechanism_fail_closed_behavior():
    """Mechanism phát hiện compute_verdict vi phạm nếu có."""
    from aios_core.verification.mechanisms import HarnessExecutionMechanism

    outcome = HarnessExecutionMechanism().check()
    assert outcome.state == VerificationState.PASS  # fail-closed hoạt động
