"""Replay (TASK-030, AC6 / P2-03): round-trip integrity check của verdict."""

from __future__ import annotations

from typing import Any

from .contracts import Check, CheckKind, CheckResult, Verdict
from .evidence import has_critical_evidence
from .pipeline import compute_verdict


def replay_verdict(evidence: dict[str, Any]) -> tuple[Verdict, str]:
    """P2-03: tái tính verdict từ persisted evidence và so với verdict đã ghi.

    - evidence chứa `check_results` (persisted VerificationResult dict):
      recompute từ chúng + flags (critical_evidence/truncated) → so sánh
      với `verdict` ghi → lệch = TAMPER (R3-4: kiểm tra ở mức dict).
    - evidence chỉ chứa `tool-results`: dựng checks tương đương rồi tính
      (fallback khi không có check_results).
    """
    stored = evidence.get("verdict")
    check_results: list[CheckResult] = []
    raw_results = evidence.get("check_results")
    if isinstance(raw_results, list):
        for raw in raw_results:
            if isinstance(raw, dict):
                check_results.append(CheckResult(**raw))
    if not check_results:
        check_results = _checks_from_tool_results(evidence.get("tool-results"))

    critical = evidence.get("critical_evidence")
    if critical is None:  # evidence thuần (không flag): tái tính từ package
        critical = has_critical_evidence(evidence)
    verdict = compute_verdict(
        check_results,
        critical,
        evidence.get("truncated", False),
    )
    if stored is not None and verdict.value != stored:
        return verdict, f"TAMPER: stored={stored} != recomputed={verdict.value}"
    return verdict, "ok"


def _checks_from_tool_results(tool_results: Any) -> list[CheckResult]:
    results: list[CheckResult] = []
    if not isinstance(tool_results, dict):
        return results
    for key, value in tool_results.items():
        check = Check(name=f"tool_result:{key}", kind=CheckKind.CUSTOM)
        ok = bool(value.get("status") == "success") if isinstance(value, dict) else bool(value)
        results.append(CheckResult(check=check, passed=ok))
    return results
