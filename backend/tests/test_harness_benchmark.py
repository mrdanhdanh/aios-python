"""TASK-033 — Benchmark + Regression Gate tests (M6-H4): runner, gate,
BenchmarkHarness, wiring (INV-021)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aios_core.config import BenchmarkSettings, Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.benchmark import (
    Baseline,
    BenchmarkError,
    BenchmarkHarness,
    BenchmarkMetric,
    BenchmarkReport,
    BenchmarkRunner,
    GateBlockedError,
    RegressionFinding,
    RegressionGate,
    RegressionRule,
    RunResult,
    default_rules,
)
from aios_core.kernel.services import StateService


def run_result(sid, quality=1.0, cost=0.0, latency=0.0, tokens=0,
               failed=False, violations=0):
    return RunResult(scenario_id=sid, quality=quality, cost=cost,
                     latency_ms=latency, tokens=tokens, failed=failed,
                     policy_violations=violations)


def make_runner(results):
    return BenchmarkRunner(lambda sid: results.get(sid, run_result(sid)))


def baseline(results, version="v1"):
    return Baseline(version=version, runs={r.scenario_id: r for r in results})


def bench_ctx(run_id, ids, bl=None, **config):
    return HarnessContext(run_id=run_id, harness="benchmark", target="bench",
                          started_at=utcnow(),
                          config={"scenario_ids": ids, "baseline": bl, **config})


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_metric_enum_6(self):
        assert {m.value for m in BenchmarkMetric} == {
            "quality", "cost", "latency", "token", "failure_rate",
            "policy_violations"}

    def test_run_result_defaults(self):
        r = RunResult(scenario_id="s")
        assert r.quality == 0.0 and r.failed is False and r.policy_violations == 0

    def test_run_result_extra_forbid(self):
        with pytest.raises(ValidationError):
            RunResult(scenario_id="s", nope=1)

    def test_baseline_defaults(self):
        b = Baseline()
        assert b.version == "v0" and b.runs == {}

    def test_rule_defaults(self):
        r = RegressionRule(metric=BenchmarkMetric.QUALITY, max_delta=-5.0)
        assert r.note == ""

    def test_rule_extra_forbid(self):
        with pytest.raises(ValidationError):
            RegressionRule(metric=BenchmarkMetric.QUALITY, max_delta=-5.0, nope=1)

    def test_finding_defaults(self):
        f = RegressionFinding(metric=BenchmarkMetric.COST, baseline_avg=1.0,
                              new_avg=2.0, delta=1.0)
        assert f.regressed is False and f.rule_note == ""

    def test_report_defaults(self):
        r = BenchmarkReport()
        assert r.gate_passed is True and r.scenarios_total == 0
        assert r.reproducible == {}


# ---------------------------------------------------------------------------
# Runner (T3)
# ---------------------------------------------------------------------------

class TestRunner:
    def test_run_returns_results(self):
        runner = make_runner({"s1": run_result("s1"), "s2": run_result("s2")})
        results, agg = runner.run(["s1", "s2"])
        assert [r.scenario_id for r in results] == ["s1", "s2"]

    def test_aggregate_quality_avg(self):
        runner = make_runner({"s1": run_result("s1", quality=1.0),
                              "s2": run_result("s2", quality=0.5)})
        _, agg = runner.run(["s1", "s2"])
        assert agg["quality"] == 0.75

    def test_aggregate_failure_rate(self):
        runner = make_runner({"s1": run_result("s1", failed=True),
                              "s2": run_result("s2"),
                              "s3": run_result("s3")})
        _, agg = runner.run(["s1", "s2", "s3"])
        assert agg["failure_rate"] == pytest.approx(1 / 3)

    def test_aggregate_violations_sum_avg(self):
        runner = make_runner({"s1": run_result("s1", violations=2),
                              "s2": run_result("s2", violations=0)})
        _, agg = runner.run(["s1", "s2"])
        assert agg["policy_violations"] == 1.0  # per-scenario avg

    def test_aggregate_empty(self):
        _, agg = BenchmarkRunner(lambda s: run_result(s)).run([])
        assert agg["scenarios"] == 0
        assert agg["quality"] == 0.0

    def test_dedup_and_sort(self):
        runner = make_runner({"s2": run_result("s2"), "s1": run_result("s1")})
        results, _ = runner.run(["s2", "s1", "s2"])
        assert [r.scenario_id for r in results] == ["s1", "s2"]

    def test_max_scenarios_cap(self):
        runner = BenchmarkRunner(lambda s: run_result(s), max_scenarios=2)
        results, _ = runner.run([f"s{i}" for i in range(5)])
        assert len(results) == 2

    def test_aggregate_latency_token(self):
        runner = make_runner({"s1": run_result("s1", latency=10, tokens=100),
                              "s2": run_result("s2", latency=20, tokens=300)})
        _, agg = runner.run(["s1", "s2"])
        assert agg["latency"] == 15.0
        assert agg["token"] == 200.0


# ---------------------------------------------------------------------------
# RegressionGate (T4)
# ---------------------------------------------------------------------------

class TestGate:
    def test_default_rules_3(self):
        rules = default_rules()
        assert {r.metric for r in rules} == {
            BenchmarkMetric.QUALITY, BenchmarkMetric.FAILURE_RATE,
            BenchmarkMetric.POLICY_VIOLATIONS}

    def test_no_regression_pass(self):
        gate = RegressionGate()
        new = [run_result("s1", quality=0.9), run_result("s2", quality=0.8)]
        base = baseline([run_result("s1", quality=0.9), run_result("s2", quality=0.8)])
        report = gate.evaluate(new, base)
        assert report.gate_passed is True
        assert report.summary == "gate-passed"

    def test_quality_drop_blocks(self):
        gate = RegressionGate(default_rules(quality_max_delta=-5.0))
        new = [run_result("s1", quality=0.8), run_result("s2", quality=0.7)]
        base = baseline([run_result("s1", quality=1.0), run_result("s2", quality=1.0)])
        report = gate.evaluate(new, base)
        assert report.gate_passed is False
        quality_finding = next(f for f in report.findings
                               if f.metric == BenchmarkMetric.QUALITY)
        assert quality_finding.regressed is True
        assert quality_finding.delta == pytest.approx(-25.0)  # (0.75-1.0)/1.0*100
        assert report.summary == "gate-blocked (1 regressions)"

    def test_small_quality_drop_ok(self):
        gate = RegressionGate(default_rules(quality_max_delta=-5.0))
        new = [run_result("s1", quality=0.97)]
        base = baseline([run_result("s1", quality=1.0)])
        report = gate.evaluate(new, base)
        assert report.gate_passed is True  # -3% < 5% ngưỡng

    def test_failure_rate_increase_blocks(self):
        gate = RegressionGate(default_rules(failure_rate_max_delta=0.02))
        new = [run_result("s1", failed=True), run_result("s2")]
        base = baseline([run_result("s1"), run_result("s2")])
        report = gate.evaluate(new, base)
        assert report.gate_passed is False
        failure = next(f for f in report.findings
                       if f.metric == BenchmarkMetric.FAILURE_RATE)
        assert failure.regressed is True
        assert failure.delta == pytest.approx(0.5)  # pp: 0.5 - 0.0

    def test_policy_violations_any_increase_blocks(self):
        gate = RegressionGate()
        new = [run_result("s1", violations=1)]
        base = baseline([run_result("s1", violations=0)])
        report = gate.evaluate(new, base)
        assert report.gate_passed is False

    def test_cost_latency_token_tracked_not_blocked(self):
        gate = RegressionGate()  # chỉ 3 rules — cost/latency/token không block
        new = [run_result("s1", cost=5.0, latency=100, tokens=1000)]
        base = baseline([run_result("s1", cost=1.0, latency=10, tokens=100)])
        report = gate.evaluate(new, base)
        assert report.gate_passed is True  # không rule → không block
        metrics = report.metrics
        assert metrics["cost"] == 5.0 and metrics["latency"] == 100.0

    def test_subset_common_scenarios_only(self):
        gate = RegressionGate()
        new = [run_result("s1", quality=0.5), run_result("new-only", quality=0.0)]
        base = baseline([run_result("s1", quality=1.0)])
        report = gate.evaluate(new, base)
        assert report.scenarios_total == 1  # chỉ s1
        assert report.findings  # có findings (s1 regress quality)

    def test_empty_baseline_no_block(self):
        gate = RegressionGate()
        new = [run_result("s1", quality=0.5)]
        report = gate.evaluate(new, Baseline())  # P1-01
        assert report.gate_passed is True
        assert report.findings == []
        assert report.summary == "gate-passed (no baseline comparison)"

    def test_empty_new_results(self):
        gate = RegressionGate()
        report = gate.evaluate([], baseline([run_result("s1")]))
        assert report.gate_passed is True  # không subset

    def test_zero_baseline_delta_zero(self):
        gate = RegressionGate()
        new = [run_result("s1", quality=0.5)]
        base = baseline([run_result("s1", quality=0.0)])
        report = gate.evaluate(new, base)
        quality = next(f for f in report.findings
                       if f.metric == BenchmarkMetric.QUALITY)
        assert quality.delta == 0.0  # C1-01: baseline 0 → delta 0

    def test_can_release(self):
        gate = RegressionGate()
        ok = gate.evaluate([run_result("s1")], baseline([run_result("s1")]))
        assert gate.can_release(ok) is True
        bad = gate.evaluate([run_result("s1", quality=0.5)],
                            baseline([run_result("s1", quality=1.0)]))
        assert gate.can_release(bad) is False

    def test_report_metrics_count(self):
        gate = RegressionGate()
        report = gate.evaluate([run_result("s1", quality=0.5)],
                               baseline([run_result("s1", quality=1.0)]))
        assert report.metrics_count == {"scenarios": 1, "findings": 3,
                                        "regressed": 1}

    def test_reproducible_baseline_version(self):
        gate = RegressionGate()
        report = gate.evaluate([run_result("s1")], baseline([run_result("s1")], version="v9"))
        assert report.baseline_version == "v9"
        assert report.reproducible == {"baseline_version": "v9"}

    def test_quality_improvement_no_block(self):
        gate = RegressionGate()
        report = gate.evaluate([run_result("s1", quality=1.0)],
                               baseline([run_result("s1", quality=0.5)]))
        assert report.gate_passed is True

    def test_deterministic_repeat(self):
        gate = RegressionGate()
        new = [run_result("s1", quality=0.8), run_result("s2", quality=0.7)]
        base = baseline([run_result("s1", quality=1.0), run_result("s2", quality=1.0)])
        a = gate.evaluate(new, base).model_dump()
        b = gate.evaluate(new, base).model_dump()
        assert a == b

    def test_quality_exact_boundary_not_regressed(self):
        gate = RegressionGate(default_rules(quality_max_delta=-5.0))
        # delta = -5.0 đúng ngưỡng → KHÔNG regress (strict less-than)
        report = gate.evaluate([run_result("s1", quality=0.95)],
                               baseline([run_result("s1", quality=1.0)]))
        assert report.gate_passed is True

    def test_quality_below_boundary_regressed(self):
        gate = RegressionGate(default_rules(quality_max_delta=-5.0))
        report = gate.evaluate([run_result("s1", quality=0.949)],
                               baseline([run_result("s1", quality=1.0)]))
        assert report.gate_passed is False

    def test_failure_rate_boundary(self):
        gate = RegressionGate(default_rules(failure_rate_max_delta=0.02))
        new = [run_result("s1", failed=True), run_result("s2", failed=True),
               run_result("s3")]
        base = baseline([run_result("s1", failed=True), run_result("s2"),
                         run_result("s3")])
        report = gate.evaluate(new, base)
        # failure_rate: 2/3 (0.667) vs 1/3 (0.333) → delta 0.333pp > 0.02 → block
        assert report.gate_passed is False

    def test_improved_latency_no_block(self):
        gate = RegressionGate()
        new = [run_result("s1", latency=5.0)]
        base = baseline([run_result("s1", latency=50.0)])
        report = gate.evaluate(new, base)
        assert report.gate_passed is True

    def test_findings_count_matches_rules(self):
        gate = RegressionGate()
        report = gate.evaluate([run_result("s1")], baseline([run_result("s1")]))
        assert len(report.findings) == 3  # quality/failure_rate/policy_violations

    def test_rule_notes_present(self):
        gate = RegressionGate()
        report = gate.evaluate([run_result("s1", quality=0.5)],
                               baseline([run_result("s1", quality=1.0)]))
        blocked = [f for f in report.findings if f.regressed][0]
        assert blocked.rule_note != ""

    def test_baseline_extra_forbid(self):
        with pytest.raises(ValidationError):
            Baseline(version="v", runs={}, nope=1)

    def test_run_result_type_validation(self):
        with pytest.raises(ValidationError):
            RunResult(scenario_id="s", tokens="many")  # int required

    def test_report_extra_forbid(self):
        with pytest.raises(ValidationError):
            BenchmarkReport(nope=1)


# ---------------------------------------------------------------------------
# BenchmarkHarness (T5)
# ---------------------------------------------------------------------------

class TestBenchmarkHarness:
    def test_id_name_version(self):
        h = BenchmarkHarness(make_runner({}), RegressionGate())
        assert h.id == "benchmark"
        assert h.name == "Benchmark"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = BenchmarkHarness(make_runner({}), RegressionGate())
        reg.register(h)
        assert reg.get("benchmark") is h

    def test_run_without_ids_raises(self):
        h = BenchmarkHarness(make_runner({}), RegressionGate())
        ctx = HarnessContext(run_id="r", harness="benchmark", target="x",
                             started_at=utcnow())
        with pytest.raises(BenchmarkError):
            h.run(ctx)

    def test_run_returns_report(self):
        h = BenchmarkHarness(make_runner({"s1": run_result("s1")}), RegressionGate())
        ctx = bench_ctx("r", ["s1"], baseline([run_result("s1")]))
        payload = h.run(ctx)
        assert payload["scenarios_total"] == 1
        assert payload["gate_passed"] is True

    def test_verify_pass(self):
        state = StateService()
        h = BenchmarkHarness(make_runner({"s1": run_result("s1")}),
                             RegressionGate(), state_service=state)
        ctx = bench_ctx("r-pass", ["s1"], baseline([run_result("s1")]), strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-pass")["benchmark"]["gate_passed"] is True

    def test_verify_gate_blocked_raises_and_persists(self):
        state = StateService()
        results = {"s1": run_result("s1", quality=0.5)}
        h = BenchmarkHarness(make_runner(results), RegressionGate(),
                             state_service=state)
        ctx = bench_ctx("r-block", ["s1"],
                        baseline([run_result("s1", quality=1.0)]), strict=True)
        h.run(ctx)
        with pytest.raises(GateBlockedError):
            h.verify(ctx, None)
        # persist TRƯỚC raise (INV-021d / evidence-first)
        assert state.get_state("r-block")["benchmark"]["gate_passed"] is False

    def test_gate_blocked_is_benchmark_error(self):
        assert issubclass(GateBlockedError, BenchmarkError)

    def test_verify_not_strict_warning(self):
        state = StateService()
        h = BenchmarkHarness(make_runner({"s1": run_result("s1", quality=0.5)}),
                             RegressionGate(), state_service=state)
        ctx = bench_ctx("r-warn", ["s1"],
                        baseline([run_result("s1", quality=1.0)]), strict=False)
        h.run(ctx)
        h.verify(ctx, None)  # không raise
        assert state.get_state("r-warn")["benchmark"]["strict"] is False

    def test_verify_without_run_raises(self):
        h = BenchmarkHarness(make_runner({}), RegressionGate())
        ctx = bench_ctx("r", ["s1"])
        with pytest.raises(BenchmarkError):
            h.verify(ctx, None)

    def test_get_report(self):
        state = StateService()
        h = BenchmarkHarness(make_runner({"s1": run_result("s1")}),
                             RegressionGate(), state_service=state)
        ctx = bench_ctx("r-g", ["s1"], baseline([run_result("s1")]), strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        report = h.get_report("r-g")
        assert report["baseline_version"] == "v1"
        assert report["gate_passed"] is True

    def test_get_report_unknown(self):
        h = BenchmarkHarness(make_runner({}), RegressionGate(),
                             state_service=StateService())
        assert h.get_report("nope") is None

    def test_full_runner_execute_gate_blocked(self):
        state = StateService()
        h = BenchmarkHarness(make_runner({"s1": run_result("s1", quality=0.5)}),
                             RegressionGate(), state_service=state)
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, "bench", config={
            "scenario_ids": ["s1"],
            "baseline": baseline([run_result("s1", quality=1.0)]),
            "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.FAILED
        assert state.get_state(ctx.run_id)["benchmark"]["gate_passed"] is False

    def test_full_runner_execute_pass(self):
        state = StateService()
        h = BenchmarkHarness(make_runner({"s1": run_result("s1")}),
                             RegressionGate(), state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "bench", config={
            "scenario_ids": ["s1"],
            "baseline": baseline([run_result("s1")]), "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


# ---------------------------------------------------------------------------
# Config + wiring (T6)
# ---------------------------------------------------------------------------

class TestConfigWiring:
    def test_benchmark_settings_defaults(self):
        b = BenchmarkSettings()
        assert b.max_scenarios == 100
        assert b.strict is True
        assert b.quality_max_delta == -5.0
        assert b.failure_rate_max_delta == 0.02

    def test_benchmark_settings_extra_forbid(self):
        with pytest.raises(ValidationError):
            BenchmarkSettings(nope=1)

    def test_settings_has_benchmark(self):
        assert Settings().benchmark.max_scenarios == 100

    def test_runtime_kernel_wires_benchmark_harness(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        h = kernel.container.resolve(BenchmarkHarness)
        assert h.id == "benchmark"
        reg = kernel.container.resolve(HarnessRegistry)
        assert "benchmark" in reg.list()

    def test_harness_registry_all_m6(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        reg = kernel.container.resolve(HarnessRegistry)
        assert set(reg.list()) == {"verification", "test", "evaluation",
                                   "benchmark", "doctor", "readiness",
                                   "behavioral", "coverage", "meta",
                                   "release", "diagnose"}  # M13+M14
