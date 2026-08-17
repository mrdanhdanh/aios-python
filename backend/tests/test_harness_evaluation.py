"""TASK-032 — Evaluation Harness tests (M6-H4): contracts, evaluators,
trajectory, suites, EvaluationHarness, wiring (INV-020)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from aios_core.config import EvaluationSettings, Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.evaluation import (
    CompositeEvaluator,
    DeterministicEvaluator,
    Engine,
    EvaluationError,
    EvaluationHarness,
    EvaluationItem,
    EvaluationKind,
    EvaluationResult,
    EvaluationStatus,
    HumanEvaluator,
    LLMJudgeEvaluator,
    Metric,
    Score,
    SemanticEvaluator,
    Suite,
    SuiteError,
    Trajectory,
    TrajectoryEvaluator,
    TrajectoryStep,
    load,
    load_many,
)
from aios_core.kernel.services import StateService


def item(output="ok", expected="ok", **over):
    base = {"input": "do the thing", "output": output, "expected": expected}
    base.update(over)
    return EvaluationItem.model_validate(base)


def metric(name="m1", kind=EvaluationKind.DETERMINISTIC, params=None):
    return Metric(name=name, kind=kind, params=params or {})


def suite(**over):
    base = {"id": "s1", "metrics": [metric()],
            "thresholds": {"m1": 0.5}}
    base.update(over)
    return Suite.model_validate(base)


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_kind_enum_5(self):
        assert {k.value for k in EvaluationKind} == {
            "deterministic", "semantic", "llm_judge", "human", "composite"}

    def test_metric_defaults(self):
        m = Metric(name="a")
        assert m.kind == EvaluationKind.DETERMINISTIC
        assert m.params == {} and m.weight == 1.0

    def test_metric_extra_forbid(self):
        with pytest.raises(ValidationError):
            Metric(name="a", nope=1)

    def test_suite_defaults(self):
        s = Suite(id="x")
        assert s.dataset == "" and s.metrics == [] and s.thresholds == {}

    def test_suite_negative_threshold_rejected(self):
        with pytest.raises(ValidationError):
            Suite(id="x", thresholds={"a": -0.1})

    def test_item_defaults(self):
        it = item()
        assert it.trajectory == [] and it.score is None

    def test_item_requires_output_expected(self):
        with pytest.raises(ValidationError):
            EvaluationItem(input="x")

    def test_trajectory_step_defaults(self):
        s = TrajectoryStep(kind="tool")
        assert s.tool is None and s.ok is None and s.denied is False

    def test_score_defaults(self):
        s = Score(metric="a", threshold=0.5)
        assert s.value is None and s.passed is False
        assert s.kind == EvaluationKind.DETERMINISTIC

    def test_result_defaults(self):
        r = EvaluationResult(suite_id="s")
        assert r.passed_all is False
        assert r.status == EvaluationStatus.FAILED
        assert r.reproducible == {}

    def test_status_enum(self):
        assert EvaluationStatus.PASSED.value == "passed"
        assert EvaluationStatus.FAILED.value == "failed"
        assert EvaluationStatus.INCONCLUSIVE.value == "inconclusive"


# ---------------------------------------------------------------------------
# Evaluators (T3)
# ---------------------------------------------------------------------------

class TestDeterministic:
    def test_exact_match(self):
        d = DeterministicEvaluator()
        assert d.evaluate(metric(), item("ok", "ok")) == 1.0
        assert d.evaluate(metric(), item("bad", "ok")) == 0.0

    def test_contains(self):
        d = DeterministicEvaluator()
        m = metric(params={"kind": "contains"})
        assert d.evaluate(m, item("hello world", "world")) == 1.0
        assert d.evaluate(m, item("hello", "world")) == 0.0

    def test_regex(self):
        d = DeterministicEvaluator()
        m = metric(params={"kind": "regex"})
        assert d.evaluate(m, item("abc123", r"\d+")) == 1.0
        assert d.evaluate(m, item("abc", r"\d+")) == 0.0

    def test_regex_invalid_pattern_zero(self):
        d = DeterministicEvaluator()
        m = metric(params={"kind": "regex"})
        assert d.evaluate(m, item("abc", r"[")) == 0.0  # C2-02

    def test_numeric_ge(self):
        d = DeterministicEvaluator()
        m = metric(params={"kind": "numeric_ge"})
        assert d.evaluate(m, item("95", "90")) == 1.0
        assert d.evaluate(m, item("85", "90")) == 0.0

    def test_numeric_ge_parse_fail_zero(self):
        d = DeterministicEvaluator()
        m = metric(params={"kind": "numeric_ge"})
        assert d.evaluate(m, item("abc", "90")) == 0.0  # C2-01

    def test_bool(self):
        d = DeterministicEvaluator()
        m = metric(params={"kind": "bool"})
        assert d.evaluate(m, item("true", "yes")) == 1.0
        assert d.evaluate(m, item("true", "no")) == 0.0


class TestSemantic:
    def test_identical(self):
        s = SemanticEvaluator()
        assert s.evaluate(metric(), item("hello world", "hello world")) == 1.0

    def test_partial_overlap(self):
        s = SemanticEvaluator()
        value = s.evaluate(metric(), item("hello world", "hello there"))
        assert 0.0 < value < 1.0

    def test_no_overlap(self):
        s = SemanticEvaluator()
        assert s.evaluate(metric(), item("alpha beta", "gamma delta")) == 0.0

    def test_empty_side_zero(self):
        s = SemanticEvaluator()
        assert s.evaluate(metric(), item("", "gamma delta")) == 0.0

    def test_deterministic(self):
        s = SemanticEvaluator()
        a = s.evaluate(metric(), item("hello world foo", "hello world bar"))
        b = s.evaluate(metric(), item("hello world foo", "hello world bar"))
        assert a == b


class TestLLMJudge:
    def test_item_score(self):
        j = LLMJudgeEvaluator()
        assert j.evaluate(metric(), item(score=0.91)) == 0.91

    def test_params_score(self):
        j = LLMJudgeEvaluator()
        m = metric(kind=EvaluationKind.LLM_JUDGE, params={"score": 0.5})
        assert j.evaluate(m, item()) == 0.5

    def test_no_score_none(self):
        j = LLMJudgeEvaluator()
        assert j.evaluate(metric(kind=EvaluationKind.LLM_JUDGE), item()) is None

    def test_reproducible_fields(self):
        j = LLMJudgeEvaluator()
        m = metric(kind=EvaluationKind.LLM_JUDGE, params={
            "model": "gpt-4", "prompt_version": "v3", "temperature": 0.2})
        rep = j.reproducible(m)
        assert rep == {"model": "gpt-4", "prompt_version": "v3", "temperature": 0.2}


class TestHuman:
    def test_item_score(self):
        h = HumanEvaluator()
        assert h.evaluate(metric(), item(score=0.7)) == 0.7

    def test_params_score(self):
        h = HumanEvaluator()
        m = metric(kind=EvaluationKind.HUMAN, params={"score": 0.9})
        assert h.evaluate(m, item()) == 0.9

    def test_no_score_none(self):
        h = HumanEvaluator()
        assert h.evaluate(metric(kind=EvaluationKind.HUMAN), item()) is None


class TestComposite:
    def test_weighted_mean(self):
        c = CompositeEvaluator()
        m = metric(kind=EvaluationKind.COMPOSITE, params={
            "sub_scores": [{"value": 1.0, "weight": 2}, {"value": 0.5, "weight": 1}]})
        assert c.evaluate(m, item()) == pytest.approx(0.8333, abs=0.001)

    def test_no_sub_scores_none(self):
        c = CompositeEvaluator()
        assert c.evaluate(metric(kind=EvaluationKind.COMPOSITE), item()) is None

    def test_skip_none_values(self):
        c = CompositeEvaluator()
        m = metric(kind=EvaluationKind.COMPOSITE, params={
            "sub_scores": [{"value": None}, {"value": 0.8}]})
        assert c.evaluate(m, item()) == 0.8


class TestEngine:
    def test_dispatch(self):
        e = Engine()
        assert e.evaluate(metric(), item("ok", "ok")) == 1.0
        assert e.evaluate(metric(kind=EvaluationKind.LLM_JUDGE), item(score=0.9)) == 0.9

    def test_score_passed(self):
        e = Engine(default_threshold=0.5)
        s = e.score(metric(), item("ok", "ok"), 0.5)
        assert s.passed is True and s.value == 1.0

    def test_score_failed(self):
        e = Engine(default_threshold=0.9)
        s = e.score(metric(), item("bad", "ok"), 0.9)
        assert s.passed is False

    def test_score_default_threshold(self):
        e = Engine(default_threshold=0.5)
        s = e.score(metric(), item("ok", "ok"))  # không truyền threshold → default
        assert s.threshold == 0.5 and s.passed is True

    def test_score_inconclusive(self):
        e = Engine()
        s = e.score(metric(kind=EvaluationKind.LLM_JUDGE), item(), 0.5)
        assert s.value is None and s.passed is False

    def test_reproducible_empty_for_deterministic(self):
        e = Engine()
        assert e.reproducible(metric()) == {}

    def test_reproducible_for_llm(self):
        e = Engine()
        m = metric(kind=EvaluationKind.LLM_JUDGE, params={
            "model": "m", "prompt_version": "p", "temperature": 0.1})
        assert e.reproducible(m)["model"] == "m"


# ---------------------------------------------------------------------------
# Trajectory (T4)
# ---------------------------------------------------------------------------

class TestTrajectory:
    def test_empty_steps(self):
        t = TrajectoryEvaluator().analyze([])
        assert t.final_correct is None
        assert t.warning is False

    def test_final_correct(self):
        steps = [TrajectoryStep(kind="decision"),
                 TrajectoryStep(kind="output", ok=True)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.final_correct is True
        assert t.marks["final_correct"] is True

    def test_final_incorrect(self):
        steps = [TrajectoryStep(kind="output", ok=False)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.final_correct is False

    def test_no_output_step(self):
        steps = [TrajectoryStep(kind="decision")]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.final_correct is None

    def test_trajectory_warning_denied(self):
        # PLAN VD: final đúng nhưng gọi sai tool → deny → retry → đúng
        steps = [TrajectoryStep(kind="tool", tool="A", ok=True, denied=True),
                 TrajectoryStep(kind="tool", tool="B", ok=True),
                 TrajectoryStep(kind="output", ok=True)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.final_correct is True
        assert t.warning is True
        assert t.marks["trajectory_warning"] is True

    def test_warning_failed_tool(self):
        steps = [TrajectoryStep(kind="tool", ok=False),
                 TrajectoryStep(kind="tool", ok=True),
                 TrajectoryStep(kind="output", ok=True)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.warning is True
        assert t.marks["had_failed_tool"] is True

    def test_warning_recovery(self):
        steps = [TrajectoryStep(kind="recovery", ok=True),
                 TrajectoryStep(kind="output", ok=True)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.warning is True
        assert t.marks["had_recovery"] is True

    def test_clean_no_warning(self):
        steps = [TrajectoryStep(kind="decision"),
                 TrajectoryStep(kind="tool", ok=True),
                 TrajectoryStep(kind="output", ok=True)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.warning is False

    def test_wrong_final_no_warning(self):
        # final sai → không phải "final correct / trajectory warning"
        steps = [TrajectoryStep(kind="tool", ok=False),
                 TrajectoryStep(kind="output", ok=False)]
        t = TrajectoryEvaluator().analyze(steps)
        assert t.final_correct is False
        assert t.warning is False


# ---------------------------------------------------------------------------
# Suite loader (T5)
# ---------------------------------------------------------------------------

class TestSuites:
    def test_load_dict(self):
        s = load({"id": "a", "metrics": [{"name": "m"}]})
        assert s.id == "a"

    def test_load_json(self, tmp_path):
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"id": "j", "metrics": [{"name": "m"}]}),
                     encoding="utf-8")
        assert load(p).id == "j"

    def test_load_yaml(self, tmp_path):
        p = tmp_path / "s.yaml"
        p.write_text("id: y\nmetrics:\n- name: m\nthresholds:\n  m: 0.5\n",
                     encoding="utf-8")
        s = load(p)
        assert s.id == "y" and s.thresholds["m"] == 0.5

    def test_load_invalid(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{bad", encoding="utf-8")
        with pytest.raises(SuiteError):
            load(p)

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(SuiteError):
            load(tmp_path / "nope.yaml")

    def test_load_many_list(self, tmp_path):
        p = tmp_path / "m.yaml"
        p.write_text("- id: a\n  metrics: []\n- id: b\n  metrics: []\n",
                     encoding="utf-8")
        assert [s.id for s in load_many(p)] == ["a", "b"]

    def test_load_many_suites_key(self, tmp_path):
        p = tmp_path / "m2.yaml"
        p.write_text("suites:\n- id: a\n  metrics: []\n", encoding="utf-8")
        assert [s.id for s in load_many(p)] == ["a"]

    def test_unknown_threshold_dropped(self):
        s = load({"id": "a", "metrics": [{"name": "m1"}],
                  "thresholds": {"m1": 0.5, "ghost": 0.9}})
        assert s.thresholds == {"m1": 0.5}

    def test_negative_threshold_rejected(self):
        with pytest.raises(SuiteError):
            load({"id": "a", "metrics": [], "thresholds": {"x": -1}})


# ---------------------------------------------------------------------------
# EvaluationHarness (T6)
# ---------------------------------------------------------------------------

def eval_ctx(run_id, s, items, **config):
    return HarnessContext(run_id=run_id, harness="evaluation", target=s.id,
                          started_at=utcnow(),
                          config={"suite": s, "items": items, **config})


class TestEvaluationHarness:
    def test_id_name_version(self):
        h = EvaluationHarness()
        assert h.id == "evaluation"
        assert h.name == "Evaluation"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = EvaluationHarness()
        reg.register(h)
        assert reg.get("evaluation") is h

    def test_run_without_suite_raises(self):
        h = EvaluationHarness()
        ctx = HarnessContext(run_id="r", harness="evaluation", target="x",
                             started_at=utcnow())
        with pytest.raises(EvaluationError):
            h.run(ctx)

    def test_run_returns_result(self):
        h = EvaluationHarness()
        s = suite()
        ctx = eval_ctx("r", s, [item("ok", "ok")])
        payload = h.run(ctx)
        assert payload["suite_id"] == "s1"
        assert payload["status"] == "passed"

    def test_verify_pass(self):
        state = StateService()
        h = EvaluationHarness(state_service=state)
        s = suite(thresholds={"m1": 0.5})
        ctx = eval_ctx("r-pass", s, [item("ok", "ok")], strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-pass")["evaluation"]["status"] == "passed"

    def test_verify_fail_strict_raises_and_persists(self):
        state = StateService()
        h = EvaluationHarness(state_service=state)
        s = suite(thresholds={"m1": 0.9})
        ctx = eval_ctx("r-fail", s, [item("bad", "ok")], strict=True)
        h.run(ctx)
        with pytest.raises(EvaluationError):
            h.verify(ctx, None)
        # persist TRƯỚC raise (pattern H2 AC5)
        assert state.get_state("r-fail")["evaluation"]["status"] == "failed"

    def test_verify_not_strict_warning(self):
        state = StateService()
        h = EvaluationHarness(state_service=state)
        s = suite(thresholds={"m1": 0.9})
        ctx = eval_ctx("r-warn", s, [item("bad", "ok")], strict=False)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-warn")["evaluation"]["strict"] is False

    def test_verify_without_run_raises(self):
        h = EvaluationHarness()
        ctx = eval_ctx("r", suite(), [item()])
        with pytest.raises(EvaluationError):
            h.verify(ctx, None)

    def test_aggregate_mean(self):
        h = EvaluationHarness()
        s = suite(thresholds={"m1": 0.5})
        ctx = eval_ctx("r", s, [item("ok", "ok"), item("bad", "ok")])
        result = h.run(ctx)
        assert result["scores"][0]["value"] == 0.5  # mean(1, 0)
        assert result["scores"][0]["passed"] is True

    def test_inconclusive_score_fails_all(self):
        h = EvaluationHarness()
        m = metric(kind=EvaluationKind.LLM_JUDGE)
        s = suite(metrics=[m])
        ctx = eval_ctx("r", s, [item()])
        result = h.run(ctx)
        assert result["scores"][0]["value"] is None
        assert result["passed_all"] is False  # AC9
        assert result["status"] == "inconclusive"

    def test_empty_metrics_fails(self):
        h = EvaluationHarness()
        s = suite(metrics=[])
        ctx = eval_ctx("r", s, [item()])
        result = h.run(ctx)
        assert result["passed_all"] is False  # C2-07

    def test_reproducible_collected_for_llm(self):
        h = EvaluationHarness()
        m = metric(kind=EvaluationKind.LLM_JUDGE, params={
            "model": "gpt-4", "prompt_version": "v3", "temperature": 0.1})
        s = suite(metrics=[m], thresholds={"m1": 0.5})
        ctx = eval_ctx("r", s, [item(score=0.9)])
        result = h.run(ctx)
        assert result["reproducible"] == {"model": "gpt-4",
                                          "prompt_version": "v3",
                                          "temperature": 0.1}

    def test_reproducible_empty_deterministic(self):
        h = EvaluationHarness()
        ctx = eval_ctx("r", suite(), [item("ok", "ok")])
        assert h.run(ctx)["reproducible"] == {}

    def test_trajectory_aggregated_first(self):
        h = EvaluationHarness()
        steps = [TrajectoryStep(kind="tool", denied=True),
                 TrajectoryStep(kind="output", ok=True)]
        ctx = eval_ctx("r", suite(thresholds={"m1": 0.5}),
                       [item("ok", "ok", trajectory=steps),
                        item("ok", "ok")])
        result = h.run(ctx)
        assert result["trajectory"]["final_correct"] is True
        assert result["trajectory"]["warning"] is True
        assert result["metrics"]["items_with_trajectory"] == 1

    def test_no_trajectory_none(self):
        h = EvaluationHarness()
        ctx = eval_ctx("r", suite(thresholds={"m1": 0.5}), [item("ok", "ok")])
        assert h.run(ctx)["trajectory"] is None

    def test_metrics_counts(self):
        h = EvaluationHarness()
        s = suite(thresholds={"m1": 0.5})
        ctx = eval_ctx("r", s, [item("ok", "ok"), item("ok", "ok")])
        result = h.run(ctx)
        assert result["metrics"]["items_total"] == 2
        assert result["metrics"]["metrics_total"] == 1
        assert result["metrics"]["metrics_passed"] == 1

    def test_get_result(self):
        state = StateService()
        h = EvaluationHarness(state_service=state)
        s = suite(thresholds={"m1": 0.5})
        ctx = eval_ctx("r-g", s, [item("ok", "ok")], strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        result = h.get_result("r-g")
        assert result["suite_id"] == "s1"
        assert result["status"] == "passed"

    def test_get_result_unknown(self):
        h = EvaluationHarness(state_service=StateService())
        assert h.get_result("nope") is None

    def test_max_items_cap(self):
        h = EvaluationHarness(max_items=2)
        s = suite(thresholds={"m1": 0.5})
        ctx = eval_ctx("r", s, [item("ok", "ok")] * 5)
        result = h.run(ctx)
        assert result["metrics"]["items_total"] == 2  # C2-06 cap

    def test_full_runner_execute_pass(self):
        state = StateService()
        h = EvaluationHarness(state_service=state)
        s = suite(thresholds={"m1": 0.5})
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, s.id, config={
            "suite": s, "items": [item("ok", "ok")], "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED
        assert state.get_state(ctx.run_id)["evaluation"]["status"] == "passed"

    def test_full_runner_execute_fail_strict(self):
        state = StateService()
        h = EvaluationHarness(state_service=state)
        s = suite(thresholds={"m1": 0.9})
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, s.id, config={
            "suite": s, "items": [item("bad", "ok")], "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.FAILED
        assert state.get_state(ctx.run_id)["evaluation"]["status"] == "failed"


# ---------------------------------------------------------------------------
# Config + wiring (T7)
# ---------------------------------------------------------------------------

class TestConfigWiring:
    def test_evaluation_settings_defaults(self):
        e = EvaluationSettings()
        assert e.default_threshold == 0.8
        assert e.strict is True
        assert e.max_items == 1000

    def test_evaluation_settings_extra_forbid(self):
        with pytest.raises(ValidationError):
            EvaluationSettings(nope=1)

    def test_settings_has_evaluation(self):
        assert Settings().evaluation.default_threshold == 0.8

    def test_runtime_kernel_wires_evaluation_harness(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        h = kernel.container.resolve(EvaluationHarness)
        assert h.id == "evaluation"
        reg = kernel.container.resolve(HarnessRegistry)
        assert "evaluation" in reg.list()

    def test_harness_registry_all_m6_so_far(self, tmp_path):
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
