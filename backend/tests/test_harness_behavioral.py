"""TASK-089 — Behavioral Conformance tests (M13-P0): engine (N lần + repeat +
fault + evidence + gate), harness, wiring, CLI (INV-035 fail-closed)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from aios_core.config import Settings
from aios_core.harness import (
    HarnessContext,
    HarnessRegistry,
    HarnessRunner,
    HarnessRunStatus,
)
from aios_core.harness.contracts import utcnow
from aios_core.harness.behavioral import (
    BehavioralConformanceEngine,
    BehavioralConformanceError,
    BehavioralConformanceHarness,
    ConformanceConfig,
    ConformanceIterationSummary,
    ConformanceProfile,
    ConformanceReport,
    ConformanceStatus,
    PROFILE_ITERATIONS,
)
from aios_core.harness.benchmark import Baseline, RunResult
from aios_core.harness.testing import (
    ExpectedResult,
    Fault,
    FaultType,
    Scenario,
    SimulationStatus,
)
from aios_core.kernel.services import StateService


def scenario(sid="s1", request="review the auth module", intent="coding",
             agent="coder", caps=None, policy=None):
    return Scenario(
        id=sid,
        input={"request": request},
        expect=ExpectedResult(intent=intent, agent=agent,
                              required_capabilities=caps or [],
                              policy=policy),
    )


def config(sid="s1", profile="quick", iterations=None, faults=None,
           fault_iterations=None, baseline=None, repeat_samples=3,
           duration_s=0.0, strict=True, **kw):
    return ConformanceConfig(
        profile=profile,
        scenario=scenario(sid, **kw),
        iterations=iterations,
        duration_s=duration_s,
        faults=faults or [],
        fault_iterations=fault_iterations or [],
        repeat_samples=repeat_samples,
        baseline=baseline,
        strict=strict,
    )


def ctx_for(run_id, cfg, strict=True):
    return HarnessContext(run_id=run_id, harness="behavioral", target="beh",
                          started_at=utcnow(),
                          config={"config": cfg, "strict": strict})


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_profile_enum_4(self):
        assert {p.value for p in ConformanceProfile} == {
            "quick", "standard", "stress", "soak"}

    def test_profile_iterations_map(self):
        assert PROFILE_ITERATIONS == {
            ConformanceProfile.QUICK: 100,
            ConformanceProfile.STANDARD: 1000,
            ConformanceProfile.STRESS: 10000,
        }

    def test_status_enum(self):
        assert {s.value for s in ConformanceStatus} == {"pass", "fail", "error"}

    def test_config_defaults(self):
        c = config()
        assert c.profile == ConformanceProfile.QUICK
        assert c.iterations is None and c.duration_s == 0.0
        assert c.faults == [] and c.fault_iterations == []
        assert c.repeat_samples == 3 and c.strict is True

    def test_config_extra_forbid(self):
        with pytest.raises(ValidationError):
            ConformanceConfig(profile="quick", scenario=scenario(), nope=1)

    def test_config_iterations_positive(self):
        with pytest.raises(ValidationError):
            config(iterations=0)

    def test_config_fault_iterations_requires_faults(self):
        with pytest.raises(ValidationError):
            config(fault_iterations=[1])  # faults rỗng

    def test_config_fault_iterations_1based(self):
        with pytest.raises(ValidationError):
            config(faults=[Fault(target="model", type=FaultType.TIMEOUT)],
                   fault_iterations=[0])

    def test_config_fault_iterations_dedup(self):
        c = config(faults=[Fault(target="model", type=FaultType.TIMEOUT)],
                   fault_iterations=[2, 1, 2])
        assert c.fault_iterations == [1, 2]

    def test_iteration_summary_defaults(self):
        s = ConformanceIterationSummary(index=1, status=SimulationStatus.SUCCESS,
                                        evidence_digest="abc", fault_injected=False)
        assert s.repeat_ok is None and s.recovered is False

    def test_report_defaults(self):
        r = ConformanceReport(profile=ConformanceProfile.QUICK, scenario_id="s1",
                              iterations_total=1, status=ConformanceStatus.PASS,
                              deterministic=True, repeat_consistent=True,
                              fault_recovery_rate=0.0)
        assert r.iterations == [] and r.findings == [] and r.gate is None

    def test_report_extra_forbid(self):
        with pytest.raises(ValidationError):
            ConformanceReport(profile=ConformanceProfile.QUICK, scenario_id="s1",
                              iterations_total=1, status=ConformanceStatus.PASS,
                              deterministic=True, repeat_consistent=True,
                              fault_recovery_rate=0.0, nope=1)


# ---------------------------------------------------------------------------
# Engine (T2)
# ---------------------------------------------------------------------------

class TestEngine:
    def test_profile_quick_iterations(self):  # AC1
        report = BehavioralConformanceEngine().run(config(iterations=10))
        assert report.iterations_total == 10
        assert report.metrics["iterations_total"] == 10

    def test_iterations_override_profile(self):  # AC1
        report = BehavioralConformanceEngine().run(config(profile="stress",
                                                          iterations=5))
        assert report.iterations_total == 5

    def test_soak_duration_based(self):  # AC2
        report = BehavioralConformanceEngine().run(
            config(profile="soak", duration_s=0.01))
        assert report.iterations_total >= 1
        assert report.iterations_total <= 10000  # cap

    def test_soak_zero_duration_one_iteration(self):  # AC2
        report = BehavioralConformanceEngine().run(config(profile="soak"))
        assert report.iterations_total == 1

    def test_soak_cap(self):  # AC2
        engine = BehavioralConformanceEngine(soak_max_iterations=3)
        report = engine.run(config(profile="soak", duration_s=10.0))
        assert report.iterations_total <= 3

    def test_deterministic(self):  # AC3
        report = BehavioralConformanceEngine().run(config(iterations=10))
        assert report.deterministic is True
        assert report.status == ConformanceStatus.PASS

    def test_evidence_digest_same(self):  # AC4
        report = BehavioralConformanceEngine().run(config(iterations=5))
        digests = {i.evidence_digest for i in report.iterations}
        assert len(digests) == 1

    def test_repeat_consistent(self):  # AC5
        report = BehavioralConformanceEngine().run(config(iterations=5))
        assert report.repeat_consistent is True
        # iteration > repeat_samples → repeat_ok None
        assert report.iterations[3].repeat_ok is None
        assert report.iterations[0].repeat_ok is True

    def test_repeat_samples_cap(self):  # P1-2 v2
        report = BehavioralConformanceEngine().run(
            config(iterations=2, repeat_samples=5))
        assert report.metrics["repeat_runs"] == 2  # cap min(5, 2)

    def test_fault_recovery_rate_1(self):  # AC6
        report = BehavioralConformanceEngine().run(
            config(iterations=5,
                   faults=[Fault(target="model", type=FaultType.TIMEOUT)]))
        assert report.fault_recovery_rate == 1.0
        assert report.status == ConformanceStatus.PASS
        assert report.metrics["faults_injected_total"] == 5

    def test_fault_iterations_subset(self):  # AC6 (P2-7 v1)
        report = BehavioralConformanceEngine().run(
            config(iterations=5,
                   faults=[Fault(target="model", type=FaultType.TIMEOUT)],
                   fault_iterations=[3]))
        assert report.metrics["faults_injected_total"] == 1
        assert report.iterations[2].fault_injected is True  # index 3 (1-based)
        assert report.iterations[0].fault_injected is False
        assert report.status == ConformanceStatus.PASS

    def test_fault_iterations_out_of_range_raises(self):  # P2-3 v2
        with pytest.raises(BehavioralConformanceError):
            BehavioralConformanceEngine().run(
                config(iterations=3,
                       faults=[Fault(target="model", type=FaultType.TIMEOUT)],
                       fault_iterations=[9]))

    def test_non_recoverable_fault_error(self):  # AC11 (P1-2 v1)
        report = BehavioralConformanceEngine().run(
            config(iterations=3,
                   faults=[Fault(target="model", type=FaultType.TIMEOUT,
                                 recoverable=False)]))
        assert report.status == ConformanceStatus.ERROR
        assert report.fault_recovery_rate == 0.0
        assert any("ERROR" in f for f in report.findings)

    def test_mismatch_fails(self):  # AC13 (P1-1 v1)
        # expect.intent sai → MISMATCH mọi iteration → FAIL (dù deterministic)
        report = BehavioralConformanceEngine().run(
            config(iterations=5, intent="doctor"))
        assert report.status == ConformanceStatus.FAIL
        assert report.deterministic is True  # vẫn deterministic nhưng sai
        assert any("MISMATCH" in f for f in report.findings)

    def test_gate_exposed_not_blocking(self):  # AC7 (P1-3 v1 + P1-1 v2)
        base = Baseline(version="v1", runs={
            "s1": RunResult(scenario_id="s1", quality=1.0)})
        # scenario SUCCESS → quality=1.0 → gate pass
        report = BehavioralConformanceEngine().run(
            config(iterations=5, baseline=base))
        assert report.gate is not None
        assert report.gate.gate_passed is True
        assert report.status == ConformanceStatus.PASS  # gate không đổi status

    def test_gate_blocked_finding_only(self):  # AC7
        base = Baseline(version="v1", runs={
            "s1": RunResult(scenario_id="s1", quality=1.0)})
        # scenario MISMATCH → quality=0.0 → gate block; status FAIL do MISMATCH
        report = BehavioralConformanceEngine().run(
            config(iterations=3, intent="doctor", baseline=base))
        assert report.gate is not None
        assert report.gate.gate_passed is False
        assert report.status == ConformanceStatus.FAIL
        assert any("regression gate blocked" in f for f in report.findings)

    def test_report_fields(self):  # AC8
        report = BehavioralConformanceEngine().run(config(iterations=4))
        assert report.scenario_id == "s1"
        assert report.profile == ConformanceProfile.QUICK
        assert report.summary.startswith("pass:")
        assert report.reproducible["scenario_id"] == "s1"
        assert report.reproducible["iterations"] == 4
        assert report.metrics["repeat_runs"] == 3
        assert len(report.iterations) == 4

    def test_cross_run_deterministic(self):  # AC15 (P2-1 v1)
        engine = BehavioralConformanceEngine()
        a = engine.run(config(iterations=10)).model_dump()
        b = engine.run(config(iterations=10)).model_dump()
        assert a == b

    def test_build_baseline(self):  # AC16 (P3-4 v1 + P1-1 v2)
        engine = BehavioralConformanceEngine()
        report = engine.run(config(iterations=5))
        base = engine.build_baseline(report)
        assert base.version == "v1"
        assert base.runs["s1"].quality == 1.0
        assert base.runs["s1"].failed is False

    def test_build_baseline_mismatch_quality(self):  # P1-1 v2
        engine = BehavioralConformanceEngine()
        report = engine.run(config(iterations=5, intent="doctor"))
        base = engine.build_baseline(report)
        assert base.runs["s1"].quality == 0.0
        assert base.runs["s1"].failed is True

    def test_scenario_from_yaml_file(self, tmp_path):  # AC14 (P1-5 v1)
        from aios_core.harness.testing import load as load_scenario

        f = tmp_path / "scenario.yaml"
        f.write_text(
            "id: y1\n"
            "input:\n"
            "  request: review the auth module\n"
            "expect:\n"
            "  intent: coding\n"
            "  agent: coder\n",
            encoding="utf-8",
        )
        sc = load_scenario(f)
        report = BehavioralConformanceEngine().run(
            ConformanceConfig(profile="quick", scenario=sc, iterations=3))
        assert report.status == ConformanceStatus.PASS
        assert report.scenario_id == "y1"


# ---------------------------------------------------------------------------
# Harness (T3)
# ---------------------------------------------------------------------------

class TestHarness:
    def test_id_name_version(self):
        h = BehavioralConformanceHarness()
        assert h.id == "behavioral"
        assert h.name == "Behavioral Conformance"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = BehavioralConformanceHarness()
        reg.register(h)
        assert reg.get("behavioral") is h

    def test_run_without_config_raises(self):
        h = BehavioralConformanceHarness()
        ctx = HarnessContext(run_id="r", harness="behavioral", target="x",
                             started_at=utcnow())
        with pytest.raises(BehavioralConformanceError):
            h.run(ctx)

    def test_run_returns_report(self):
        h = BehavioralConformanceHarness()
        ctx = ctx_for("r", config(iterations=3))
        payload = h.run(ctx)
        assert payload["iterations_total"] == 3
        assert payload["status"] == "pass"

    def test_verify_pass(self):
        state = StateService()
        h = BehavioralConformanceHarness(state_service=state)
        ctx = ctx_for("r-pass", config(iterations=3), strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-pass")["behavioral"]["status"] == "pass"

    def test_verify_fail_raises_and_persists(self):  # AC17a (P2-1 v2)
        state = StateService()
        h = BehavioralConformanceHarness(state_service=state)
        ctx = ctx_for("r-fail", config(iterations=3, intent="doctor"), strict=True)
        h.run(ctx)
        with pytest.raises(BehavioralConformanceError):
            h.verify(ctx, None)
        # persist TRƯỚC raise (evidence-first)
        assert state.get_state("r-fail")["behavioral"]["status"] == "fail"

    def test_verify_not_strict_no_raise(self):  # AC17b (P2-1 v2)
        state = StateService()
        h = BehavioralConformanceHarness(state_service=state)
        ctx = ctx_for("r-warn", config(iterations=3, intent="doctor"), strict=False)
        h.run(ctx)
        h.verify(ctx, None)  # không raise
        assert state.get_state("r-warn")["behavioral"]["strict"] is False

    def test_verify_without_run_raises(self):
        h = BehavioralConformanceHarness()
        ctx = ctx_for("r", config(iterations=3))
        with pytest.raises(BehavioralConformanceError):
            h.verify(ctx, None)

    def test_get_report(self):  # AC9 (P2-2 v2)
        state = StateService()
        h = BehavioralConformanceHarness(state_service=state)
        ctx = ctx_for("r-g", config(iterations=3), strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        report = h.get_report("r-g")
        assert report["scenario_id"] == "s1"
        assert report["status"] == "pass"

    def test_get_report_unknown(self):
        h = BehavioralConformanceHarness(state_service=StateService())
        assert h.get_report("nope") is None

    def test_full_runner_execute_pass(self):  # AC9
        state = StateService()
        h = BehavioralConformanceHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "beh", config={
            "config": config(iterations=3).model_dump(mode="json"),
            "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED
        assert state.get_state(ctx.run_id)["behavioral"]["status"] == "pass"

    def test_full_runner_execute_fail_closed(self):  # AC17a
        state = StateService()
        h = BehavioralConformanceHarness(state_service=state)
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, "beh", config={
            "config": config(iterations=3, intent="doctor").model_dump(mode="json"),
            "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.FAILED
        assert state.get_state(ctx.run_id)["behavioral"]["status"] == "fail"


# ---------------------------------------------------------------------------
# Wiring (T4)
# ---------------------------------------------------------------------------

class TestWiring:
    def test_registry_has_behavioral(self):  # AC9
        from aios_core.kernel import RuntimeKernel

        kernel = RuntimeKernel.create(Settings())
        registry = kernel.container.resolve(HarnessRegistry)
        assert registry.get("behavioral") is not None
        assert registry.get("behavioral").id == "behavioral"

    def test_harness_resolvable(self):  # AC9
        from aios_core.kernel import RuntimeKernel

        kernel = RuntimeKernel.create(Settings())
        h = kernel.container.resolve(BehavioralConformanceHarness)
        assert h.id == "behavioral"


# ---------------------------------------------------------------------------
# CLI (T5)
# ---------------------------------------------------------------------------

class TestCLI:
    def _run_cli(self, argv):
        from aios_core.workflow.cli import main

        return main(argv)

    def _write_scenario(self, tmp_path, sid="s1"):
        f = tmp_path / "scenario.yaml"
        f.write_text(
            f"id: {sid}\n"
            "input:\n"
            "  request: review the auth module\n"
            "expect:\n"
            "  intent: coding\n"
            "  agent: coder\n",
            encoding="utf-8",
        )
        return str(f)

    def test_cli_pass_exit_0(self, tmp_path, capsys):  # AC10
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", self._write_scenario(tmp_path),
            "--iterations", "3",
        ])
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert data["status"] == "pass"
        assert data["iterations_total"] == 3

    def test_cli_fail_exit_1(self, tmp_path, capsys):  # AC10
        f = tmp_path / "scenario.yaml"
        f.write_text(
            "id: s1\n"
            "input:\n"
            "  request: review the auth module\n"
            "expect:\n"
            "  intent: doctor\n"  # sai → MISMATCH → FAIL
            "  agent: coder\n",
            encoding="utf-8",
        )
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", str(f),
            "--iterations", "3",
        ])
        out = capsys.readouterr().out
        assert rc == 1
        data = json.loads(out)
        assert data["status"] == "fail"

    def test_cli_save_baseline(self, tmp_path):  # AC16
        baseline_file = tmp_path / "baseline.json"
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", self._write_scenario(tmp_path),
            "--iterations", "3",
            "--save-baseline", str(baseline_file),
        ])
        assert rc == 0
        assert baseline_file.exists()
        data = json.loads(baseline_file.read_text(encoding="utf-8"))
        assert data["version"] == "v1"
        assert data["runs"]["s1"]["quality"] == 1.0

    def test_cli_faults_json(self, tmp_path, capsys):  # AC6
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", self._write_scenario(tmp_path),
            "--iterations", "3",
            "--faults", json.dumps([{"target": "model", "type": "timeout"}]),
        ])
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert data["fault_recovery_rate"] == 1.0

    def test_cli_faults_not_list(self, tmp_path, capsys):  # P3-9 v2
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", self._write_scenario(tmp_path),
            "--faults", json.dumps({"target": "model", "type": "timeout"}),
        ])
        out = capsys.readouterr().out
        assert rc == 1
        assert "must be a JSON list" in out

    def test_cli_baseline_file(self, tmp_path, capsys):  # AC7
        base = Baseline(version="v1", runs={
            "s1": RunResult(scenario_id="s1", quality=1.0)})
        base_file = tmp_path / "base.json"
        base_file.write_text(json.dumps(base.model_dump(mode="json")),
                             encoding="utf-8")
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", self._write_scenario(tmp_path),
            "--iterations", "3",
            "--baseline", str(base_file),
        ])
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert data["gate"]["gate_passed"] is True

    def test_cli_missing_scenario_file(self, tmp_path, capsys):  # P1-5 v1
        rc = self._run_cli([
            "harness", "behavioral",
            "--scenario-file", str(tmp_path / "nope.yaml"),
        ])
        out = capsys.readouterr().out
        assert rc == 1
        assert "FAILED" in out