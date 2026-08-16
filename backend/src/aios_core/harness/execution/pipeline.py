"""Check pipeline + verdict computation (TASK-030, H2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .contracts import (
    Check, CheckKind, CheckResult, VerificationResult, Verdict,
)

Runner = Callable[[str], tuple[bool, float]]  # path → (success, line_coverage_pct)


def run_checks(
    checks: list[Check],
    base_dir: str,
    runners: dict[CheckKind, Runner] | None = None,
) -> list[CheckResult]:
    """Execute deterministic checks; unsupported/skipped → skipped=True (C1-03).

    INV-035 (M11-P0): exception → error field (không pass, fail-closed).
    """
    results: list[CheckResult] = []
    for check in checks:
        try:
            ok, detail = _run_one(check, base_dir, runners or {})
        except Exception as exc:  # noqa: BLE001 — check-level isolation
            results.append(CheckResult(check=check, passed=False,
                                       detail=f"error: {exc}",
                                       error=str(exc)))
            continue
        if ok is None:
            results.append(CheckResult(check=check, skipped=True,
                                       detail="skipped: runner unavailable"))
        else:
            results.append(CheckResult(check=check, passed=ok, detail=detail))
    return results


def _run_one(
    check: Check, base_dir: str, runners: dict[CheckKind, Runner],
) -> tuple[bool | None, str]:
    kind = check.kind
    if kind == CheckKind.FILE_EXISTS:
        path = Path(base_dir) / check.params.get("path", "")
        return path.exists(), f"exists={path.exists()}: {path}"
    if kind == CheckKind.CONTAINS:
        path = Path(base_dir) / check.params.get("path", "")
        needle = check.params.get("text", "")
        if not path.exists():
            return False, f"missing: {path}"
        content = path.read_text(encoding="utf-8", errors="replace")
        return needle in content, f"contains={needle in content}: {path}"
    if kind == CheckKind.TEST_RUN:
        runner = runners.get(CheckKind.TEST_RUN)
        if runner is None:
            return None, ""
        ok, _ = runner(check.params.get("path", ""))
        return ok, f"test_run={ok}"
    if kind == CheckKind.COVERAGE:
        runner = runners.get(CheckKind.COVERAGE)
        if runner is None:
            return None, ""
        ok, pct = runner(check.params.get("path", ""))
        threshold = float(check.params.get("min_coverage", 0.0))
        return (ok and pct >= threshold), f"coverage={pct:.2f}% (min {threshold:.2f}%)"
    if kind == CheckKind.CUSTOM:
        fn = check.params.get("fn")
        if callable(fn):
            result = fn(check.params)
            if isinstance(result, tuple):
                return bool(result[0]), str(result[1])
            return bool(result), ""
        return None, "custom fn unavailable"
    return None, f"unknown kind: {kind}"


def compute_verdict(
    check_results: list[CheckResult],
    has_critical_evidence: bool,
    truncated: bool = False,  # R3-6
) -> Verdict:
    """C2-06: FAIL (check-derived) > INCONCLUSIVE (thiếu evidence) > PASS.
    INV-035 (M11-P0): bất kỳ FAIL nào → FAIL; skipped/error → INCONCLUSIVE
    (KHÔNG PASS — fail-closed, kể cả nếu passed=True); thiếu evidence →
    INCONCLUSIVE; else PASS/PASS_WITH_WARNING."""
    failures = [r for r in check_results
                if not r.effectively_passed and not r.skipped and not r.error]
    if failures:
        return Verdict.FAIL
    skipped = [r for r in check_results if r.skipped or r.error]
    if skipped:
        return Verdict.INCONCLUSIVE
    if not has_critical_evidence or truncated:
        return Verdict.INCONCLUSIVE
    if not check_results:
        return Verdict.PASS_WITH_WARNING
    return Verdict.PASS


def build_result(
    execution_ref: str,
    check_results: list[CheckResult],
    has_critical_evidence: bool,
    truncated: bool = False,
) -> VerificationResult:
    """Deterministic metrics (R3-7: counts only — no timing)."""
    verdict = compute_verdict(check_results, has_critical_evidence, truncated)
    by_kind: dict[str, int] = {}
    for r in check_results:
        by_kind[r.check.kind.value] = by_kind.get(r.check.kind.value, 0) + 1
    summary = _summarize(verdict, check_results, has_critical_evidence, truncated)
    return VerificationResult(
        execution_ref=execution_ref,
        verdict=verdict,
        check_results=check_results,
        summary=summary,
        metrics={
            "checks_total": len(check_results),
            # INV-035: passed chỉ tính khi effectively_passed (không skip/error)
            "checks_passed": sum(1 for r in check_results if r.effectively_passed),
            "checks_failed": len([r for r in check_results
                                  if not r.effectively_passed and not r.skipped
                                  and not r.error]),
            "checks_skipped": sum(1 for r in check_results if r.skipped or r.error),
            "critical_evidence": bool(has_critical_evidence),
            "truncated": bool(truncated),
            "by_kind": by_kind,
        },
    )


def _summarize(
    verdict: Verdict, results: list[CheckResult],
    has_critical_evidence: bool, truncated: bool,
) -> str:
    if verdict == Verdict.FAIL:
        failed = [r for r in results if not r.passed and not r.skipped]
        return f"FAIL: {failed[0].check.name} -> {failed[0].detail}" if failed else "FAIL"
    if verdict == Verdict.INCONCLUSIVE:
        if truncated:
            return "INCONCLUSIVE: event window truncated"
        if not has_critical_evidence:
            return "INCONCLUSIVE: missing critical evidence"
        skipped = [r for r in results if r.skipped]
        return f"INCONCLUSIVE: {len(skipped)} check(s) skipped"
    if verdict == Verdict.PASS_WITH_WARNING:
        return "PASS_WITH_WARNING: no checks defined"
    return f"PASS: {sum(1 for r in results if r.passed)}/{len(results)} checks passed"
