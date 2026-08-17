"""TASK-031 — Test & Simulation tests (M6-H3): contracts, loader, faults,
simulation runner, TestHarness, wiring (INV-020)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from aios_core.config import Settings, TestingSettings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.testing import (
    ExpectedResult,
    FakeRuntime,
    FakeTool,
    Fault,
    FaultInjector,
    FaultType,
    ResourceExhaustedError,
    Scenario,
    ScenarioError,
    SimulationOutcome,
    SimulationRunner,
    SimulationStatus,
    TestError,
    TestHarness,
    TestLevel,
    load,
    load_many,
)
from aios_core.kernel.services import StateService


def scenario(**over):
    base = dict(
        id="s1",
        input={"request": "review the auth module"},
        expect={"intent": "coding", "agent": "coder",
                "required_capabilities": ["filesystem", "python"]},
    )
    base.update(over)
    return Scenario.model_validate(base)


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_test_level_12(self):
        values = [l.value for l in TestLevel]
        assert len(values) == 12
        assert "workflow" in values and "e2e" in values and "regression" in values

    def test_fault_type_enum(self):
        assert FaultType.TIMEOUT.value == "timeout"
        assert FaultType.FAILURE.value == "failure"
        assert FaultType.EXHAUSTED.value == "exhausted"

    def test_fault_defaults(self):
        f = Fault(target="model", type=FaultType.TIMEOUT)
        assert f.params == {}

    def test_fault_extra_forbid(self):
        with pytest.raises(ValidationError):
            Fault(target="model", type=FaultType.TIMEOUT, nope=1)

    def test_expected_result_defaults(self):
        e = ExpectedResult()
        assert e.intent is None and e.agent is None and e.policy is None
        assert e.required_capabilities == []
        assert e.tests_pass is True and e.no_policy_bypass is True

    def test_scenario_defaults(self):
        s = scenario()
        assert s.level == TestLevel.WORKFLOW
        assert s.environment == {"mode": "simulation"}
        assert s.faults == [] and s.tags == []

    def test_scenario_requires_input(self):
        # input là dict bắt buộc (request bắt buộc do loader validate)
        with pytest.raises(ValidationError):
            Scenario(id="x", expect=ExpectedResult())

    def test_scenario_input_accepts_empty_dict(self):
        # model cho phép input {} — loader mới bắt request (C2)
        s = Scenario(id="x", input={}, expect=ExpectedResult())
        assert s.input == {}

    def test_scenario_extra_forbid(self):
        with pytest.raises(ValidationError):
            scenario(nope=1)

    def test_simulation_status(self):
        assert SimulationStatus.SUCCESS.value == "success"
        assert SimulationStatus.MISMATCH.value == "mismatch"
        assert SimulationStatus.ERROR.value == "error"

    def test_outcome_defaults(self):
        o = SimulationOutcome(scenario_id="s", status=SimulationStatus.SUCCESS)
        assert o.executed_nodes == [] and o.tool_calls == []
        assert o.metrics == {}

    def test_outcome_extra_forbid(self):
        with pytest.raises(ValidationError):
            SimulationOutcome(scenario_id="s", status=SimulationStatus.SUCCESS, nope=1)


# ---------------------------------------------------------------------------
# Loader (T3)
# ---------------------------------------------------------------------------

class TestLoader:
    def test_load_dict(self):
        s = load({"id": "a", "input": {"request": "hi"},
                  "expect": {"intent": "general"}})
        assert s.id == "a"

    def test_load_dict_missing_request(self):
        with pytest.raises(ScenarioError):
            load({"id": "a", "input": {}, "expect": {}})

    def test_load_json_file(self, tmp_path):
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"id": "j", "input": {"request": "x"},
                                 "expect": {}}), encoding="utf-8")
        s = load(p)
        assert s.id == "j"

    def test_load_yaml_file(self, tmp_path):
        p = tmp_path / "s.yaml"
        p.write_text("id: y\ninput:\n  request: x\nexpect: {}\n", encoding="utf-8")
        s = load(p)
        assert s.id == "y"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(ScenarioError):
            load(tmp_path / "nope.yaml")

    def test_load_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with pytest.raises(ScenarioError):
            load(p)

    def test_load_mode_live_rejected(self):
        with pytest.raises(ScenarioError):
            load({"id": "a", "input": {"request": "x"}, "environment": {"mode": "live"},
                  "expect": {}})

    def test_load_many_list(self, tmp_path):
        p = tmp_path / "m.yaml"
        p.write_text("- id: a\n  input:\n    request: x\n  expect: {}\n"
                     "- id: b\n  input:\n    request: y\n  expect: {}\n",
                     encoding="utf-8")
        s = load_many(p)
        assert [x.id for x in s] == ["a", "b"]

    def test_load_many_scenarios_key(self, tmp_path):
        p = tmp_path / "m2.yaml"
        p.write_text("scenarios:\n- id: a\n  input:\n    request: x\n  expect: {}\n",
                     encoding="utf-8")
        s = load_many(p)
        assert [x.id for x in s] == ["a"]

    def test_load_many_invalid_item(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("- id: a\n  input: {}\n  expect: {}\n", encoding="utf-8")
        with pytest.raises(ScenarioError):
            load_many(p)


# ---------------------------------------------------------------------------
# FaultInjector (T4)
# ---------------------------------------------------------------------------

class TestFaultInjector:
    def test_no_fault_next_for_none(self):
        inj = FaultInjector([])
        assert inj.next_for("model") is None

    def test_next_for_returns_matching(self):
        f = Fault(target="model", type=FaultType.TIMEOUT)
        inj = FaultInjector([f])
        assert inj.next_for("model") is f
        assert inj.next_for("tool.python") is None

    def test_inject_once_then_none(self):
        inj = FaultInjector([Fault(target="model", type=FaultType.TIMEOUT)])
        assert inj.next_for("model") is not None
        with pytest.raises(TimeoutError):
            inj.apply("model", lambda: {"ok": True})
        assert inj.next_for("model") is None  # inject 1 lần (C2-04)

    def test_timeout_fault_raises(self):
        inj = FaultInjector([Fault(target="model", type=FaultType.TIMEOUT)])
        with pytest.raises(TimeoutError):
            inj.apply("model", lambda: {"ok": True})

    def test_failure_fault_raises(self):
        inj = FaultInjector([Fault(target="tool.python", type=FaultType.FAILURE)])
        with pytest.raises(RuntimeError):
            inj.apply("tool.python", lambda: {"ok": True})

    def test_exhausted_fault_raises(self):
        inj = FaultInjector([Fault(target="resource", type=FaultType.EXHAUSTED)])
        with pytest.raises(ResourceExhaustedError):
            inj.apply("resource", lambda: {"ok": True})

    def test_apply_no_fault_calls_fn(self):
        inj = FaultInjector([])
        result, recovered = inj.apply("model", lambda: {"ok": True})
        assert result == {"ok": True}
        assert recovered is True

    def test_apply_after_fault_succeeds(self):
        inj = FaultInjector([Fault(target="model", type=FaultType.TIMEOUT)])
        with pytest.raises(TimeoutError):
            inj.apply("model", lambda: {"ok": True})
        result, _ = inj.apply("model", lambda: {"ok": True})
        assert result == {"ok": True}  # lần 2 thành công

    def test_injected_records(self):
        inj = FaultInjector([Fault(target="model", type=FaultType.TIMEOUT)])
        with pytest.raises(TimeoutError):
            inj.apply("model", lambda: {})
        assert inj.injected == [{"target": "model", "type": "timeout", "attempt": 1}]

    def test_recover_records_event(self):
        inj = FaultInjector([Fault(target="model", type=FaultType.TIMEOUT)])
        inj.recover("model", "retry", Fault(target="model", type=FaultType.TIMEOUT))
        assert inj.recovery_events == [{"type": "retry", "target": "model",
                                        "fault_type": "timeout"}]

    def test_multiple_targets_independent(self):
        inj = FaultInjector([
            Fault(target="model", type=FaultType.TIMEOUT),
            Fault(target="tool.python", type=FaultType.FAILURE),
        ])
        assert inj.next_for("model") is not None
        assert inj.next_for("tool.python") is not None
        with pytest.raises(TimeoutError):
            inj.apply("model", lambda: {})
        assert inj.next_for("model") is None
        assert inj.next_for("tool.python") is not None

    def test_apply_twice_after_recovery_ok(self):
        inj = FaultInjector([Fault(target="model", type=FaultType.TIMEOUT)])
        with pytest.raises(TimeoutError):
            inj.apply("model", lambda: {"ok": True})
        assert inj.apply("model", lambda: {"ok": True})[0] == {"ok": True}
        assert inj.apply("model", lambda: {"ok": True})[0] == {"ok": True}


# ---------------------------------------------------------------------------
# FakeRuntime + FakeTool (T5a)
# ---------------------------------------------------------------------------

class TestFakeRuntime:
    def test_default_intent_keywords(self):
        r = FakeRuntime()
        assert r.intent("please review auth") == "coding"
        assert r.intent("fix the bug") == "coding"
        assert r.intent("write docs") == "writing"
        assert r.intent("summarize the report") == "writing"
        assert r.intent("run unit tests") == "testing"
        assert r.intent("plan the release") == "planning"
        assert r.intent("hello there") == "general"

    def test_default_agent_map(self):
        r = FakeRuntime()
        assert r.resolve_agent("coding") == "coder"
        assert r.resolve_agent("testing") == "coder"
        assert r.resolve_agent("writing") == "writer"
        assert r.resolve_agent("general") == "generalist"

    def test_default_policy_allow(self):
        r = FakeRuntime()
        assert r.check_policy("anything", "coding") == "allow"

    def test_default_capabilities(self):
        r = FakeRuntime()
        assert r.capabilities("coder") == ["filesystem", "python"]
        assert r.capabilities("writer") == ["filesystem"]
        assert r.capabilities("generalist") == ["filesystem"]

    def test_injectable_intent(self):
        r = FakeRuntime(intent=lambda req: "custom")
        assert r.intent("x") == "custom"

    def test_injectable_agent(self):
        r = FakeRuntime(resolve_agent=lambda i: "special")
        assert r.resolve_agent("coding") == "special"

    def test_injectable_policy(self):
        r = FakeRuntime(check_policy=lambda req, i: "deny")
        assert r.check_policy("x", "coding") == "deny"

    def test_injectable_capabilities(self):
        r = FakeRuntime(capabilities=lambda a: ["network"])
        assert r.capabilities("coder") == ["network"]


class TestFakeTool:
    def test_default_behavior_ok(self):
        t = FakeTool("model")
        assert t.run({"request": "x"}) == {"ok": True}

    def test_custom_behavior(self):
        t = FakeTool("tool:python", {"ok": False, "error": "boom"})
        assert t.run({}) == {"ok": False, "error": "boom"}

    def test_last_call_recorded(self):
        t = FakeTool("model")
        t.run({"request": "r"})
        assert t.last_call["name"] == "model"
        assert t.last_call["input"] == {"request": "r"}


# ---------------------------------------------------------------------------
# SimulationRunner (T5b)
# ---------------------------------------------------------------------------

class TestSimulationRunner:
    def test_success_minimal(self):
        s = scenario(expect={"intent": "coding", "agent": "coder"})
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.SUCCESS
        assert out.intent == "coding"
        assert out.agent == "coder"
        assert out.policy == "allow"
        assert out.expectation_matches["intent"] is True
        assert out.expectation_matches["agent"] is True

    def test_model_node_always_first(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["python"]})
        out = SimulationRunner().run(s)
        assert out.executed_nodes == ["model", "capability:python"]
        assert out.metrics["nodes"] == 2
        assert out.metrics["tool_calls"] == 2

    def test_capabilities_nodes_created(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem", "python"]})
        out = SimulationRunner().run(s)
        tools = [c["tool"] for c in out.tool_calls]
        assert tools == ["model", "tool:filesystem", "tool:python"]

    def test_tool_call_shape(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem"]})
        out = SimulationRunner().run(s)
        call = out.tool_calls[1]
        assert set(call) == {"node", "tool", "input", "ok", "status", "attempt"}
        assert call["node"] == "capability:filesystem"
        assert call["ok"] is True and call["status"] == "ok"

    def test_intent_mismatch(self):
        s = scenario(expect={"intent": "writing"})
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.MISMATCH
        assert out.expectation_matches["intent"] is False

    def test_agent_mismatch(self):
        s = scenario(expect={"intent": "coding", "agent": "writer"})
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.MISMATCH

    def test_capability_missing(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["network"]})
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.MISMATCH
        assert out.expectation_matches["required_capabilities"] is False

    def test_policy_deny_expected(self):
        r = FakeRuntime(check_policy=lambda req, i: "deny")
        s = scenario(expect={"intent": "coding", "policy": "deny"})
        out = SimulationRunner(r).run(s)
        assert out.status == SimulationStatus.SUCCESS
        assert out.summary == "blocked-as-expected"
        assert out.tool_calls == []
        assert out.verification["no_policy_bypass"] is True

    def test_policy_deny_not_expected(self):
        r = FakeRuntime(check_policy=lambda req, i: "deny")
        s = scenario(expect={"intent": "coding", "policy": "allow"})
        out = SimulationRunner(r).run(s)
        assert out.status == SimulationStatus.MISMATCH

    def test_policy_deny_expect_none(self):
        r = FakeRuntime(check_policy=lambda req, i: "deny")
        s = scenario(expect={"intent": "coding"})
        out = SimulationRunner(r).run(s)
        assert out.status == SimulationStatus.MISMATCH  # P1-02

    def test_policy_match_checked(self):
        s = scenario(expect={"intent": "coding", "policy": "allow"})
        out = SimulationRunner().run(s)
        assert out.expectation_matches["policy"] is True

    def test_timeout_fault_recovers(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem"]},
                     faults=[Fault(target="tool:filesystem", type=FaultType.TIMEOUT)])
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.SUCCESS
        assert len(out.recovery_events) == 1
        assert out.recovery_events[0]["type"] == "retry"
        # fault raise TRƯỚC call (không ghi call) → model 1 + filesystem 1
        assert out.metrics["tool_calls"] == 2
        assert out.verification["tests_pass"] is True

    def test_failure_fault_fallback(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem"]},
                     faults=[Fault(target="tool:filesystem", type=FaultType.FAILURE)])
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.SUCCESS
        assert out.recovery_events[0]["type"] == "fallback"

    def test_resource_fault_on_first_node(self):
        s = scenario(expect={"intent": "coding", "agent": "coder"},
                     faults=[Fault(target="resource", type=FaultType.EXHAUSTED)])
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.SUCCESS
        assert out.recovery_events[0]["type"] == "queued"
        # fault inject tại node model (đầu — P1-01)
        assert out.faults_injected[0]["target"] == "resource"

    def test_model_fault(self):
        s = scenario(expect={"intent": "coding", "agent": "coder"},
                     faults=[Fault(target="model", type=FaultType.TIMEOUT)])
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.SUCCESS
        assert out.faults_injected[0]["target"] == "model"

    def test_fault_metrics_counts(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem"]},
                     faults=[Fault(target="tool:filesystem", type=FaultType.TIMEOUT)])
        out = SimulationRunner().run(s)
        assert out.metrics["faults_injected"] == 1
        assert out.metrics["recovery_events"] == 1

    def test_tool_calls_capped_100(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": [f"c{i}" for i in range(150)]})
        out = SimulationRunner().run(s)
        assert len(out.tool_calls) == 100  # C2-06

    def test_no_capabilities_one_model_call(self):
        s = scenario(expect={"intent": "coding", "agent": "coder"})
        out = SimulationRunner().run(s)
        assert out.executed_nodes == ["model"]
        assert out.metrics["tool_calls"] == 1

    def test_error_status_when_retry_fails(self, monkeypatch):
        s = scenario(expect={"intent": "coding", "agent": "coder"},
                     faults=[Fault(target="model", type=FaultType.TIMEOUT)])
        calls = {"n": 0}

        def failing_apply(self_, target, call_fn):
            calls["n"] += 1
            raise TimeoutError("always")

        monkeypatch.setattr(FaultInjector, "apply", failing_apply)
        out = SimulationRunner().run(s)
        assert out.status == SimulationStatus.ERROR
        assert "not recovered" in out.summary

    def test_deterministic_repeat(self):
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem", "python"]},
                     faults=[Fault(target="tool:filesystem", type=FaultType.TIMEOUT)])
        a = SimulationRunner().run(s)
        b = SimulationRunner().run(s)
        assert a.model_dump() == b.model_dump()  # deterministic (C1-04/R3-7)

    def test_metrics_no_timing(self):
        s = scenario(expect={"intent": "coding", "agent": "coder"})
        out = SimulationRunner().run(s)
        assert "duration" not in out.metrics
        assert "timestamp" not in out.metrics


# ---------------------------------------------------------------------------
# TestHarness (T6)
# ---------------------------------------------------------------------------

def make_ctx(run_id, sc, **config):
    return HarnessContext(run_id=run_id, harness="test", target=sc.id,
                          started_at=utcnow(), config={"scenario": sc, **config})


class TestTestHarness:
    def test_id_name_version(self):
        h = TestHarness()
        assert h.id == "test"
        assert h.name == "Test & Simulation"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = TestHarness()
        reg.register(h)
        assert reg.get("test") is h

    def test_run_without_scenario_raises(self):
        h = TestHarness()
        ctx = HarnessContext(run_id="r", harness="test", target="x", started_at=utcnow())
        with pytest.raises(TestError):
            h.run(ctx)

    def test_run_returns_outcome(self):
        h = TestHarness()
        s = scenario()
        ctx = make_ctx("r", s, strict=True)
        payload = h.run(ctx)
        assert payload["scenario_id"] == "s1"
        assert payload["status"] == "success"

    def test_verify_pass(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario()
        ctx = make_ctx("r-pass", s, strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-pass")["testing"]["status"] == "success"

    def test_verify_mismatch_strict_raises_and_persists(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario(expect={"intent": "writing"})
        ctx = make_ctx("r-fail", s, strict=True)
        h.run(ctx)
        with pytest.raises(TestError):
            h.verify(ctx, None)
        # persist TRƯỚC raise (pattern H2 AC5)
        assert state.get_state("r-fail")["testing"]["status"] == "mismatch"

    def test_verify_mismatch_not_strict_warning(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario(expect={"intent": "writing"})
        ctx = make_ctx("r-warn", s, strict=False)
        h.run(ctx)
        h.verify(ctx, None)  # không raise
        assert state.get_state("r-warn")["testing"]["strict"] is False
        assert state.get_state("r-warn")["testing"]["status"] == "mismatch"

    def test_verify_without_run_raises(self):
        h = TestHarness()
        ctx = make_ctx("r", scenario())
        with pytest.raises(TestError):
            h.verify(ctx, None)

    def test_persist_content(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario(expect={"intent": "coding", "agent": "coder",
                             "required_capabilities": ["filesystem"]})
        ctx = make_ctx("r-p", s, strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        persisted = state.get_state("r-p")["testing"]
        assert persisted["scenario_id"] == "s1"
        assert persisted["metrics"]["nodes"] == 2
        assert len(persisted["tool_calls"]) == 2
        assert persisted["matches"]["intent"] is True

    def test_get_outcome(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario()
        ctx = make_ctx("r-g", s, strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        out = h.get_outcome("r-g")
        assert out["scenario_id"] == "s1"
        assert out["status"] == "success"

    def test_get_outcome_unknown(self):
        h = TestHarness(state_service=StateService())
        assert h.get_outcome("nope") is None

    def test_runtime_override_via_config(self):
        state = StateService()
        deny_runtime = FakeRuntime(check_policy=lambda req, i: "deny")
        runner = SimulationRunner(deny_runtime)
        h = TestHarness(state_service=state)
        s = scenario(expect={"intent": "coding", "policy": "deny"})
        ctx = make_ctx("r-d", s, strict=True, simulation_runner=runner)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-d")["testing"]["summary"] == "blocked-as-expected"

    def test_full_runner_execute_pass(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario(expect={"intent": "coding", "agent": "coder"})
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, s.id, config={"scenario": s, "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED
        assert state.get_state(ctx.run_id)["testing"]["status"] == "success"

    def test_full_runner_execute_fail_strict(self):
        state = StateService()
        h = TestHarness(state_service=state)
        s = scenario(expect={"intent": "writing"})
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, s.id, config={"scenario": s, "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.FAILED
        assert state.get_state(ctx.run_id)["testing"]["status"] == "mismatch"


# ---------------------------------------------------------------------------
# Config + wiring (T7)
# ---------------------------------------------------------------------------

class TestConfigWiring:
    def test_testing_settings_defaults(self):
        t = TestingSettings()
        assert t.default_retries == 1
        assert t.strict is True
        assert t.simulation_timeout_s == 30.0

    def test_testing_settings_extra_forbid(self):
        with pytest.raises(ValidationError):
            TestingSettings(nope=1)

    def test_settings_has_testing(self):
        assert Settings().testing.strict is True

    def test_runtime_kernel_wires_test_harness(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        h = kernel.container.resolve(TestHarness)
        assert h.id == "test"
        reg = kernel.container.resolve(HarnessRegistry)
        assert "test" in reg.list()
        assert "verification" in reg.list()  # H2 vẫn còn

    def test_harness_registry_has_all_m6(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        reg = kernel.container.resolve(HarnessRegistry)
        # TASK-029..034: 6 harnesses M6 + M13 + M14
        assert set(reg.list()) == {"verification", "test", "evaluation",
                                   "benchmark", "doctor", "readiness",
                                   "behavioral", "coverage", "meta",
                                   "release", "diagnose", "heal"}
