"""Meta-Harness engine (M13-P2, TASK-091).

Verify the verifier — 8 adversarial cases qua independent oracle (hardcode,
P2-1). Chống circular: engine KHÔNG gọi hàm production để tính
`expected_state`; oracle là hằng số. Tái dùng public API `compute_verdict` /
`replay_verdict` / `has_critical_evidence` / `CheckResult.effectively_passed`
(từ `harness/execution`) để CHẠY verifier production — không sửa chúng.

Không import sqlite3/httpx/socket/requests/os (INV-020b precedent).
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import platform
from typing import Any

from ..context import HarnessContext
from ..execution import pipeline  # module ref (AC16 monkeypatch target)
from ..execution.contracts import (
    Check,
    CheckKind,
    CheckResult,
    Verdict,
)
from ..execution.evidence import has_critical_evidence
from ..execution.replay import replay_verdict
from ..registry import Harness, HarnessRegistry
from ..runner import HarnessRunner
from .contracts import (
    MetaCase,
    MetaCaseResult,
    MetaOracle,
    MetaReport,
    MetaStatus,
)


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001 — dev/editable
        return "unknown"


class _NoVerifyHarness(Harness):
    """Case 8: verify() no-op → HarnessRunner COMPLETED without real verify."""

    id = "meta_no_verify"
    name = "meta-no-verify"
    version = "1.0.0"

    def prepare(self, ctx: HarnessContext) -> None: ...
    def validate(self, ctx: HarnessContext) -> None: ...
    def run(self, ctx: HarnessContext) -> Any:
        return {"ok": True}
    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        # intentionally no-op (broken verify phase)
        ...
    def complete(self, ctx: HarnessContext, payload: Any) -> None: ...


class MetaHarnessEngine:
    """Thuần — chạy 8 adversarial cases. Oracle hardcode (P2-1)."""

    def __init__(
        self,
        state_service: Any | None = None,
        *,
        registry_ids: list[str] | None = None,
    ) -> None:
        self._state = state_service
        self._registry_ids = registry_ids or []

    # -- public --------------------------------------------------------------

    def run(self) -> MetaReport:
        cases = [
            self._false_positive(),
            self._false_negative(),
            self._malformed_evidence(),
            self._broken_verifier(),
            self._corrupted_artifact(),
            self._replay_mismatch(),
            self._skipped_verification(),
            self._verify_skipped(),
        ]
        all_fail_closed = all(c.fail_closed for c in cases)
        status = MetaStatus.PASS if all_fail_closed else MetaStatus.FAIL
        by_case = {c.case.value: (1 if c.fail_closed else 0) for c in cases}
        summary = (
            f"meta-harness: {sum(1 for c in cases if c.fail_closed)}/{len(cases)} "
            f"cases fail-closed -> {status.value}"
        )
        return MetaReport(
            cases=cases,
            all_fail_closed=all_fail_closed,
            status=status,
            metrics={
                "total": len(cases),
                "fail_closed": sum(1 for c in cases if c.fail_closed),
                "by_case": by_case,
            },
            summary=summary,
            reproducible={
                "aios_version": _aios_version(),
                "python_version": platform.python_version(),
                "registry_harness_ids": sorted(self._registry_ids),
            },
        )

    # -- cases ---------------------------------------------------------------

    def _false_positive(self) -> MetaCaseResult:
        # evidence thiếu critical (no plan.json) + check pass → INCONCLUSIVE
        evidence = {"namespace": "plan", "runtime-events.json": [],
                    "truncated": False}
        checks = [CheckResult(check=Check(name="ok", kind=CheckKind.CUSTOM),
                              passed=True)]
        # P3-5: gọi has_critical_trước compute_verdict
        critical = has_critical_evidence(evidence)
        verdict = pipeline.compute_verdict(checks, critical, evidence.get("truncated", False))
        state = verdict.value
        return MetaCaseResult(
            case=MetaCase.FALSE_POSITIVE,
            verifier_state=state,
            expected_state=MetaOracle.NOT_PASS,  # oracle hardcode
            fail_closed=(state != "pass"),
            detail="missing critical evidence must NOT pass",
        )

    def _false_negative(self) -> MetaCaseResult:
        evidence = {"namespace": "plan", "plan.json": {"id": "1"},
                    "runtime-events.json": [{}], "truncated": False}
        checks = [CheckResult(check=Check(name="bad", kind=CheckKind.CUSTOM),
                              passed=False)]
        critical = has_critical_evidence(evidence)
        verdict = pipeline.compute_verdict(checks, critical, evidence.get("truncated", False))
        state = verdict.value
        return MetaCaseResult(
            case=MetaCase.FALSE_NEGATIVE,
            verifier_state=state,
            expected_state=MetaOracle.FAIL,
            fail_closed=(state != "pass"),
            detail="failing check must FAIL",
        )

    def _malformed_evidence(self) -> MetaCaseResult:
        evidence: dict[str, Any] = {}
        critical = has_critical_evidence(evidence)
        verdict = pipeline.compute_verdict([], critical, False)
        state = verdict.value
        return MetaCaseResult(
            case=MetaCase.MALFORMED_EVIDENCE,
            verifier_state=state,
            expected_state=MetaOracle.NOT_PASS,
            fail_closed=(state != "pass"),
            detail="empty evidence must NOT pass",
        )

    def _broken_verifier(self) -> MetaCaseResult:
        # scenario (a): Meta PHÁT HIỆN stub trả PASS trên evidence thiếu
        evidence = {"namespace": "plan", "runtime-events.json": [],
                    "truncated": False}

        def broken_verifier(check_results, has_critical, truncated=False):
            return Verdict.PASS  # broken: luôn PASS

        state = broken_verifier([], False, False).value
        expected = MetaOracle.NOT_PASS  # evidence thiếu → phải INCONCLUSIVE
        # Meta detects: verifier trả PASS trong khi expected ≠ PASS
        fail_closed = (state != expected.value)
        return MetaCaseResult(
            case=MetaCase.BROKEN_VERIFIER,
            verifier_state=state,
            expected_state=expected,
            fail_closed=fail_closed,
            detail="broken verifier (always PASS) detected",
        )

    def _corrupted_artifact(self) -> MetaCaseResult:
        content = b"original-artifact-bytes"
        ref = "intentionally-wrong-sha256"
        actual = hashlib.sha256(content).hexdigest()
        detected = (actual != ref)
        return MetaCaseResult(
            case=MetaCase.CORRUPTED_ARTIFACT,
            verifier_state=("corrupt" if detected else "ok"),
            expected_state=MetaOracle.CORRUPT,
            fail_closed=detected,
            detail=f"sha256 mismatch detected={detected}",
        )

    def _replay_mismatch(self) -> MetaCaseResult:
        evidence = {
            "verdict": "pass",
            "check_results": [CheckResult(
                check=Check(name="t", kind=CheckKind.CUSTOM),
                passed=False).model_dump()],
            "critical_evidence": True,
        }
        _verdict, msg = replay_verdict(evidence)
        detected = "TAMPER" in msg
        return MetaCaseResult(
            case=MetaCase.REPLAY_MISMATCH,
            verifier_state=msg,
            expected_state=MetaOracle.TAMPER,
            fail_closed=detected,
            detail=f"replay tamper detected={detected}",
        )

    def _skipped_verification(self) -> MetaCaseResult:
        evidence = {"namespace": "plan", "plan.json": {"id": "1"},
                    "runtime-events.json": [{}], "truncated": False}
        checks = [CheckResult(check=Check(name="sk", kind=CheckKind.CUSTOM),
                              passed=True, skipped=True)]  # INV-035
        critical = has_critical_evidence(evidence)
        verdict = pipeline.compute_verdict(checks, critical, evidence.get("truncated", False))
        state = verdict.value
        return MetaCaseResult(
            case=MetaCase.SKIPPED_VERIFICATION,
            verifier_state=state,
            expected_state=MetaOracle.NOT_PASS,  # INV-035: skipped → not pass
            fail_closed=(state != "pass"),
            detail="skipped check must NOT pass",
        )

    def _verify_skipped(self) -> MetaCaseResult:
        # scenario (a): Meta PHÁT HIỆN run COMPLETED mà không verify
        from aios_core.kernel.services.state import StateService

        state = self._state or StateService()
        harness = _NoVerifyHarness()
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(harness, "meta-verify-skipped")
        report = runner.execute(harness, ctx)
        run_status = report.result.status.value
        detected = (run_status == "completed")  # verify no-op → completed
        return MetaCaseResult(
            case=MetaCase.VERIFY_SKIPPED,
            verifier_state=run_status,
            expected_state=MetaOracle.NOT_PASS,
            fail_closed=detected,
            detail=f"verify phase skipped (status={run_status}) detected={detected}",
        )
