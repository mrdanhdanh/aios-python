"""Regression gate (TASK-033, INV-021): so baseline → block release."""

from __future__ import annotations

from .contracts import (
    Baseline, BenchmarkMetric, BenchmarkReport, RegressionFinding,
    RegressionRule, RunResult,
)

#: hướng xấu: quality giảm; cost/latency/token/failure_rate/violations tăng
_WORSE_DIRECTION: dict[BenchmarkMetric, str] = {
    BenchmarkMetric.QUALITY: "down",
    BenchmarkMetric.COST: "up",
    BenchmarkMetric.LATENCY: "up",
    BenchmarkMetric.TOKEN: "up",
    BenchmarkMetric.FAILURE_RATE: "up",
    BenchmarkMetric.POLICY_VIOLATIONS: "up",
}

#: delta dạng % (tương đối) hay pp (tuyệt đối)
_PERCENT_METRICS = {BenchmarkMetric.QUALITY, BenchmarkMetric.COST,
                    BenchmarkMetric.LATENCY, BenchmarkMetric.TOKEN}


def default_rules(
    *, quality_max_delta: float = -5.0, failure_rate_max_delta: float = 0.02,
) -> list[RegressionRule]:
    """P2-01: 3 rules mặc định — cost/latency/token chỉ theo dõi (không block)."""
    return [
        RegressionRule(metric=BenchmarkMetric.QUALITY,
                       max_delta=quality_max_delta,
                       note="quality drop > threshold blocks release"),
        RegressionRule(metric=BenchmarkMetric.FAILURE_RATE,
                       max_delta=failure_rate_max_delta,
                       note="failure rate increase > threshold blocks release"),
        RegressionRule(metric=BenchmarkMetric.POLICY_VIOLATIONS,
                       max_delta=0.0,
                       note="any policy violation increase blocks release"),
    ]


class RegressionGate:
    """Thuần (không raise) — BenchmarkHarness quyết định block (P1-02)."""

    def __init__(self, rules: list[RegressionRule] | None = None) -> None:
        self._rules = rules if rules else default_rules()

    def evaluate(self, new_results: list[RunResult],
                 baseline: Baseline) -> BenchmarkReport:
        new_by_id = {r.scenario_id: r for r in new_results}
        subset = sorted(set(new_by_id) & set(baseline.runs))  # C1-02
        report = BenchmarkReport(
            baseline_version=baseline.version,
            scenarios_total=len(subset),
            reproducible={"baseline_version": baseline.version},
        )
        if not subset:  # P1-01: baseline rỗng → không regress
            report.summary = "gate-passed (no baseline comparison)"
            report.metrics_count = {"scenarios": 0, "findings": 0, "regressed": 0}
            return report

        new_avg = _avg(subset, new_by_id)
        base_avg = _avg(subset, baseline.runs)
        report.metrics = {
            "quality": new_avg["quality"], "cost": new_avg["cost"],
            "latency": new_avg["latency"], "token": new_avg["token"],
            "failure_rate": new_avg["failure_rate"],
            "policy_violations": new_avg["policy_violations"],
            "scenarios": len(subset),
        }
        findings: list[RegressionFinding] = []
        for rule in self._rules:
            metric = rule.metric
            base_value = base_avg[metric.value]
            new_value = new_avg[metric.value]
            delta = _delta(metric, base_value, new_value)
            regressed = _is_regressed(metric, delta, rule.max_delta)
            findings.append(RegressionFinding(
                metric=metric, baseline_avg=base_value, new_avg=new_value,
                delta=delta, regressed=regressed, rule_note=rule.note))
        report.findings = findings
        report.gate_passed = not any(f.regressed for f in findings)  # P2-03
        regressed_count = sum(1 for f in findings if f.regressed)
        report.metrics_count = {"scenarios": len(subset),
                                "findings": len(findings),
                                "regressed": regressed_count}
        report.summary = ("gate-passed" if report.gate_passed else
                          f"gate-blocked ({regressed_count} regressions)")
        return report

    def can_release(self, report: BenchmarkReport) -> bool:
        return report.gate_passed


def _avg(ids: list[str], runs: dict[str, RunResult]) -> dict[str, float]:
    total = len(ids)
    return {
        "quality": sum(runs[i].quality for i in ids) / total,
        "cost": sum(runs[i].cost for i in ids) / total,
        "latency": sum(runs[i].latency_ms for i in ids) / total,
        "token": sum(runs[i].tokens for i in ids) / total,
        "failure_rate": sum(1 for i in ids if runs[i].failed) / total,
        "policy_violations": sum(runs[i].policy_violations for i in ids) / total,
    }


def _delta(metric: BenchmarkMetric, base: float, new: float) -> float:
    if metric in _PERCENT_METRICS:
        if base == 0:  # C1-01: chia 0 → 0
            return 0.0
        return (new - base) / base * 100.0
    return new - base  # pp


_EPS = 1e-9  # float precision at boundary (TASK-033 test)


def _is_regressed(metric: BenchmarkMetric, delta: float,
                  max_delta: float) -> bool:
    if _WORSE_DIRECTION[metric] == "down":
        return delta < max_delta - _EPS  # quality giảm quá ngưỡng
    return delta > max_delta + _EPS  # tăng quá ngưỡng
