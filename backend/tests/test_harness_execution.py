"""TASK-030 — Execution Verification tests (M6-H2): contracts, evidence,
pipeline, verdict, replay, VerificationHarness, wiring, INV-019."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from aios_core.config import ExecutionSettings, Settings
from aios_core.harness import HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.execution import (
    Check,
    CheckKind,
    CheckResult,
    EvidenceServices,
    VerificationError,
    VerificationHarness,
    VerificationResult,
    VerificationTask,
    Verdict,
    build_result,
    collect_evidence,
    compute_verdict,
    has_critical_evidence,
    replay_verdict,
    run_checks,
)
from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.kernel.services import ArtifactService, StateService
from aios_core.harness import HarnessContext
from aios_core.harness.contracts import utcnow


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_check_kind_enum_values(self):
        assert CheckKind.FILE_EXISTS.value == "file_exists"
        assert CheckKind.TEST_RUN.value == "test_run"
        assert CheckKind.COVERAGE.value == "coverage"
        assert CheckKind.CONTAINS.value == "contains"
        assert CheckKind.CUSTOM.value == "custom"

    def test_check_defaults(self):
        c = Check(name="x", kind=CheckKind.FILE_EXISTS)
        assert c.params == {}
        assert c.name == "x"

    def test_check_extra_forbid(self):
        with pytest.raises(ValidationError):
            Check(name="x", kind=CheckKind.FILE_EXISTS, nope=1)

    def test_task_defaults(self):
        t = VerificationTask(execution_ref="p1")
        assert t.preconditions == []
        assert t.postconditions == []
        assert t.invariants == []
        assert t.base_dir == "."

    def test_task_requires_execution_ref(self):
        with pytest.raises(ValidationError):
            VerificationTask()

    def test_task_extra_forbid(self):
        with pytest.raises(ValidationError):
            VerificationTask(execution_ref="p1", nope=True)

    def test_check_result_defaults(self):
        r = CheckResult(check=Check(name="a", kind=CheckKind.FILE_EXISTS))
        assert r.passed is False
        assert r.detail == ""
        assert r.skipped is False

    def test_verdict_enum(self):
        assert Verdict.PASS.value == "pass"
        assert Verdict.PASS_WITH_WARNING.value == "pass_with_warning"
        assert Verdict.FAIL.value == "fail"
        assert Verdict.INCONCLUSIVE.value == "inconclusive"

    def test_verification_result_fields(self):
        r = VerificationResult(
            execution_ref="p1", verdict=Verdict.PASS,
            check_results=[], summary="ok")
        assert r.metrics == {}
        assert r.execution_ref == "p1"

    def test_evidence_services_duck_typed(self):
        svc = EvidenceServices(state="s", events="e", artifacts="a")
        assert svc.state == "s"
        assert svc.events == "e"
        assert svc.artifacts == "a"

    def test_check_model_dump_roundtrip(self):
        c = Check(name="a", kind=CheckKind.CONTAINS, params={"path": "f", "text": "x"})
        again = Check.model_validate(c.model_dump())
        assert again == c


# ---------------------------------------------------------------------------
# Evidence collection (T3)
# ---------------------------------------------------------------------------

def make_state(**kwargs):
    return StateService() if kwargs.pop("real", False) else kwargs


class FakeState:
    def __init__(self, mapping):
        self._mapping = mapping

    def get_state(self, ref):
        return self._mapping.get(ref)


class FakeEvents:
    def __init__(self, events):
        self._events = events

    def query_audit(self, limit=100, event_type=None):
        return self._events


class FakeArtifacts:
    def __init__(self):
        self.stored = []

    def store(self, contract, content):
        self.stored.append((contract, content))
        return contract

    def list(self, artifact_type=None):
        return [c for c, _ in self.stored]


def event(eid, execution_id, event_type="workflow.started", ts="2026-01-01T00:00:00Z"):
    return Event(
        id=eid, type=EventType(event_type),
        payload={"execution_id": execution_id},
        timestamp=_dt(ts),
    )


def _dt(iso: str):
    from datetime import datetime
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def services(state=None, events=None, artifacts=None):
    return EvidenceServices(
        state=state or FakeState({}),
        events=events or FakeEvents([]),
        artifacts=artifacts or FakeArtifacts(),
    )


PLAN_STATE = {
    "plan": {"id": "plan-1", "nodes": []},
    "nodes": {"n1": "completed"},
    "results": {"n1": {"status": "success"}},
    "started_at": "2026-01-01T00:00:00+00:00",
}
GRAPH_STATE = {
    "graph": {"nodes": ["a"], "edges": []},
    "nodes": {"a": "completed"},
    "results": {"a": {"status": "success"}},
    "started_at": "2026-01-01T00:00:00+00:00",
    "execution_order": ["a"],
    "metrics": {"duration_ms": 5},
}


class TestEvidence:
    def test_plan_namespace_resolution(self):
        svc = services(state=FakeState({"plan-1": PLAN_STATE}))
        ev = collect_evidence(VerificationTask(execution_ref="plan-1"), svc)
        assert ev["namespace"] == "plan"
        assert ev["plan.json"] == PLAN_STATE["plan"]
        assert ev["tool-results"] == PLAN_STATE["results"]

    def test_graph_prefix_resolution(self):
        svc = services(state=FakeState({"graph:g1": GRAPH_STATE}))
        ev = collect_evidence(VerificationTask(execution_ref="graph:g1"), svc)
        assert ev["namespace"] == "graph"
        assert "plan.json" not in ev
        assert ev["execution-graph.json"] == GRAPH_STATE["graph"]

    def test_graph_fallback_without_prefix(self):
        svc = services(state=FakeState({"graph:g1": GRAPH_STATE}))
        ev = collect_evidence(VerificationTask(execution_ref="g1"), svc)
        assert ev["namespace"] == "graph"

    def test_not_found_partial(self):
        svc = services(state=FakeState({}))
        ev = collect_evidence(VerificationTask(execution_ref="nope"), svc)
        assert ev["namespace"] == ""
        assert not has_critical_evidence(ev)

    def test_plan_events_filtered_and_sorted(self):
        evs = [
            event("e2", "plan-1", ts="2026-01-01T00:00:02Z"),
            event("e1", "plan-1", ts="2026-01-01T00:00:01Z"),
            event("e9", "other-plan", ts="2026-01-01T00:00:03Z"),
        ]
        svc = services(state=FakeState({"plan-1": PLAN_STATE}), events=FakeEvents(evs))
        ev = collect_evidence(VerificationTask(execution_ref="plan-1"), svc)
        ids = [e["id"] for e in ev["runtime-events.json"]]
        assert ids == ["e1", "e2"]  # sorted asc, filtered by execution_id

    def test_graph_events_match_both_forms(self):
        evs = [event("e1", "g1"), event("e2", "graph:g1")]
        svc = services(state=FakeState({"graph:g1": GRAPH_STATE}), events=FakeEvents(evs))
        ev = collect_evidence(VerificationTask(execution_ref="graph:g1"), svc)
        assert len(ev["runtime-events.json"]) == 2

    def test_event_to_dict_uses_to_dict(self):
        e = Event(id="x", type=EventType.WORKFLOW_STARTED, payload={"execution_id": "p"})
        evs = [e]
        svc = services(state=FakeState({"p": PLAN_STATE}), events=FakeEvents(evs))
        ev = collect_evidence(VerificationTask(execution_ref="p"), svc)
        d = ev["runtime-events.json"][0]
        assert d["id"] == "x"
        assert d["type"] == "workflow.started"
        assert d["payload"]["execution_id"] == "p"

    def test_plan_empty_events_no_critical(self):
        svc = services(state=FakeState({"p": PLAN_STATE}), events=FakeEvents([]))
        ev = collect_evidence(VerificationTask(execution_ref="p"), svc)
        assert not has_critical_evidence(ev)  # P2-02: plan cần ≥1 event

    def test_graph_empty_events_critical_ok(self):
        svc = services(state=FakeState({"graph:g1": GRAPH_STATE}), events=FakeEvents([]))
        ev = collect_evidence(VerificationTask(execution_ref="graph:g1"), svc)
        assert has_critical_evidence(ev)  # P2-02: graph chấp nhận []

    def test_plan_critical_evidence_present(self):
        evs = [event("e1", "plan-1")]
        svc = services(state=FakeState({"plan-1": PLAN_STATE}), events=FakeEvents(evs))
        ev = collect_evidence(VerificationTask(execution_ref="plan-1"), svc)
        assert has_critical_evidence(ev)

    def test_truncated_detection(self):
        evs = [event(f"e{i}", "plan-1") for i in range(10000)]
        svc = services(state=FakeState({"plan-1": PLAN_STATE}), events=FakeEvents(evs))
        ev = collect_evidence(VerificationTask(execution_ref="plan-1"), svc)
        assert ev["truncated"] is True
        assert not has_critical_evidence(ev)  # P2-01: không PASS khi thiếu

    def test_not_truncated_under_limit(self):
        evs = [event(f"e{i}", "plan-1") for i in range(9999)]
        svc = services(state=FakeState({"plan-1": PLAN_STATE}), events=FakeEvents(evs))
        ev = collect_evidence(VerificationTask(execution_ref="plan-1"), svc)
        assert ev["truncated"] is False

    def test_query_audit_limit_called(self):
        class Limited(FakeEvents):
            def __init__(self):
                super().__init__([])
                self.called_limit = None

            def query_audit(self, limit=100, event_type=None):
                self.called_limit = limit
                return []

        fe = Limited()
        svc = services(state=FakeState({"p": PLAN_STATE}), events=fe)
        collect_evidence(VerificationTask(execution_ref="p"), svc)
        assert fe.called_limit == 10000


# ---------------------------------------------------------------------------
# Pipeline — run_checks (T4)
# ---------------------------------------------------------------------------

def tmp_task(tmp_path, **kwargs):
    return VerificationTask(execution_ref="p1", base_dir=str(tmp_path), **kwargs)


class TestRunChecks:
    def test_file_exists_pass(self, tmp_path):
        (tmp_path / "a.txt").write_text("hi", encoding="utf-8")
        res = run_checks([Check(name="f", kind=CheckKind.FILE_EXISTS,
                                params={"path": "a.txt"})], str(tmp_path))
        assert res[0].passed is True

    def test_file_exists_fail(self, tmp_path):
        res = run_checks([Check(name="f", kind=CheckKind.FILE_EXISTS,
                                params={"path": "missing.txt"})], str(tmp_path))
        assert res[0].passed is False

    def test_contains_pass(self, tmp_path):
        (tmp_path / "out.log").write_text("hello world", encoding="utf-8")
        res = run_checks([Check(name="c", kind=CheckKind.CONTAINS,
                                params={"path": "out.log", "text": "hello"})], str(tmp_path))
        assert res[0].passed is True

    def test_contains_fail(self, tmp_path):
        (tmp_path / "out.log").write_text("hello", encoding="utf-8")
        res = run_checks([Check(name="c", kind=CheckKind.CONTAINS,
                                params={"path": "out.log", "text": "nope"})], str(tmp_path))
        assert res[0].passed is False

    def test_contains_missing_file(self, tmp_path):
        res = run_checks([Check(name="c", kind=CheckKind.CONTAINS,
                                params={"path": "x.log", "text": "nope"})], str(tmp_path))
        assert res[0].passed is False

    def test_test_run_with_runner_pass(self, tmp_path):
        res = run_checks(
            [Check(name="t", kind=CheckKind.TEST_RUN, params={"path": "tests"})],
            str(tmp_path), runners={CheckKind.TEST_RUN: lambda p: (True, 0.0)})
        assert res[0].passed is True

    def test_test_run_with_runner_fail(self, tmp_path):
        res = run_checks(
            [Check(name="t", kind=CheckKind.TEST_RUN, params={"path": "tests"})],
            str(tmp_path), runners={CheckKind.TEST_RUN: lambda p: (False, 0.0)})
        assert res[0].passed is False

    def test_test_run_no_runner_skipped(self, tmp_path):
        res = run_checks([Check(name="t", kind=CheckKind.TEST_RUN)], str(tmp_path))
        assert res[0].skipped is True
        assert res[0].passed is False

    def test_coverage_above_threshold(self, tmp_path):
        res = run_checks(
            [Check(name="cov", kind=CheckKind.COVERAGE,
                   params={"path": "src", "min_coverage": 80.0})],
            str(tmp_path), runners={CheckKind.COVERAGE: lambda p: (True, 95.0)})
        assert res[0].passed is True

    def test_coverage_below_threshold(self, tmp_path):
        res = run_checks(
            [Check(name="cov", kind=CheckKind.COVERAGE,
                   params={"path": "src", "min_coverage": 80.0})],
            str(tmp_path), runners={CheckKind.COVERAGE: lambda p: (True, 50.0)})
        assert res[0].passed is False

    def test_coverage_failed_run(self, tmp_path):
        res = run_checks(
            [Check(name="cov", kind=CheckKind.COVERAGE, params={"path": "src"})],
            str(tmp_path), runners={CheckKind.COVERAGE: lambda p: (False, 0.0)})
        assert res[0].passed is False

    def test_coverage_no_runner_skipped(self, tmp_path):
        res = run_checks([Check(name="cov", kind=CheckKind.COVERAGE)], str(tmp_path))
        assert res[0].skipped is True

    def test_custom_fn_true(self, tmp_path):
        res = run_checks([Check(name="cu", kind=CheckKind.CUSTOM,
                                params={"fn": lambda p: (True, "custom ok")})], str(tmp_path))
        assert res[0].passed is True

    def test_custom_fn_false(self, tmp_path):
        res = run_checks([Check(name="cu", kind=CheckKind.CUSTOM,
                                params={"fn": lambda p: False})], str(tmp_path))
        assert res[0].passed is False

    def test_custom_fn_unavailable_skipped(self, tmp_path):
        res = run_checks([Check(name="cu", kind=CheckKind.CUSTOM)], str(tmp_path))
        assert res[0].skipped is True

    def test_check_exception_reported_as_fail(self, tmp_path):
        def boom(p):
            raise RuntimeError("check exploded")
        res = run_checks([Check(name="cu", kind=CheckKind.CUSTOM,
                                params={"fn": boom})], str(tmp_path))
        assert res[0].passed is False
        assert "error" in res[0].detail

    def test_unknown_kind_skipped(self, tmp_path):
        # pydantic enum chặn kind lạ từ Check() — bypass qua model_construct
        check = Check.model_construct(name="u", kind="weird")
        res = run_checks([check], str(tmp_path))
        assert res[0].skipped is True

    def test_subdir_path_join(self, tmp_path):
        sub = tmp_path / "out" / "deep"
        sub.mkdir(parents=True)
        (sub / "f.txt").write_text("x", encoding="utf-8")
        res = run_checks([Check(name="f", kind=CheckKind.FILE_EXISTS,
                                params={"path": "out/deep/f.txt"})], str(tmp_path))
        assert res[0].passed is True


# ---------------------------------------------------------------------------
# Pipeline — compute_verdict (T4)
# ---------------------------------------------------------------------------

def res(passed=True, skipped=False):
    return CheckResult(check=Check(name="c", kind=CheckKind.CUSTOM), passed=passed, skipped=skipped)


class TestComputeVerdict:
    def test_all_pass(self):
        assert compute_verdict([res(True), res(True)], True) == Verdict.PASS

    def test_no_checks_warning(self):
        assert compute_verdict([], True) == Verdict.PASS_WITH_WARNING

    def test_any_fail_wins(self):
        assert compute_verdict([res(True), res(False)], True) == Verdict.FAIL

    def test_fail_beats_skip(self):
        assert compute_verdict([res(False), res(skipped=True)], True) == Verdict.FAIL

    def test_skipped_postcondition_inconclusive(self):
        assert compute_verdict([res(True), res(skipped=True)], True) == Verdict.INCONCLUSIVE

    def test_no_evidence_inconclusive(self):
        assert compute_verdict([res(True)], False) == Verdict.INCONCLUSIVE

    def test_truncated_inconclusive(self):
        assert compute_verdict([res(True)], True, truncated=True) == Verdict.INCONCLUSIVE

    def test_fail_even_without_evidence(self):
        # C1-03: FAIL check-derived thắng cả khi thiếu evidence
        assert compute_verdict([res(False)], False) == Verdict.FAIL

    def test_warning_with_checks_but_empty_pass(self):
        # PASS khi có checks pass nhưng không có checks khác
        assert compute_verdict([res(True)], True) == Verdict.PASS


class TestBuildResult:
    def test_metrics_deterministic(self):
        r = build_result("p1", [res(True), res(False)], True)
        assert r.metrics["checks_total"] == 2
        assert r.metrics["checks_passed"] == 1
        assert r.metrics["checks_failed"] == 1
        assert r.metrics["critical_evidence"] is True
        assert "duration" not in r.metrics  # R3-7

    def test_metrics_by_kind(self):
        r = build_result("p1", [res(True)], True)
        assert r.metrics["by_kind"]["custom"] == 1

    def test_summary_fail(self):
        r = build_result("p1", [res(False)], True)
        assert r.summary.startswith("FAIL:")

    def test_summary_inconclusive_no_evidence(self):
        r = build_result("p1", [res(True)], False)
        assert "missing critical evidence" in r.summary

    def test_summary_pass(self):
        r = build_result("p1", [res(True), res(True)], True)
        assert "PASS:" in r.summary


# ---------------------------------------------------------------------------
# Replay (T6)
# ---------------------------------------------------------------------------

class TestReplay:
    def test_roundtrip_ok(self):
        r = build_result("p1", [res(True)], True)
        evidence = {"verdict": r.verdict.value,
                    "check_results": [x.model_dump(mode="json") for x in r.check_results],
                    "critical_evidence": True}
        verdict, msg = replay_verdict(evidence)
        assert verdict == Verdict.PASS
        assert msg == "ok"

    def test_tamper_verdict_detected(self):
        evidence = {"verdict": "pass",
                    "check_results": [res(False).model_dump(mode="json")],
                    "critical_evidence": True}
        verdict, msg = replay_verdict(evidence)
        assert verdict == Verdict.FAIL
        assert "TAMPER" in msg

    def test_tamper_missing_evidence_detected(self):
        evidence = {"verdict": "pass",
                    "check_results": [res(True).model_dump(mode="json")],
                    "critical_evidence": False}
        verdict, msg = replay_verdict(evidence)
        assert verdict == Verdict.INCONCLUSIVE
        assert "TAMPER" in msg

    def test_fallback_tool_results(self):
        evidence = {"verdict": "pass", "critical_evidence": True,
                    "tool-results": {"n1": {"status": "success"}}}
        verdict, msg = replay_verdict(evidence)
        assert verdict == Verdict.PASS

    def test_fallback_tool_result_failure(self):
        evidence = {"verdict": "fail", "critical_evidence": True,
                    "tool-results": {"n1": {"status": "failure"}}}
        verdict, msg = replay_verdict(evidence)
        assert verdict == Verdict.FAIL

    def test_empty_evidence_inconclusive(self):
        verdict, msg = replay_verdict({})
        assert verdict == Verdict.INCONCLUSIVE


# ---------------------------------------------------------------------------
# VerificationHarness (T5)
# ---------------------------------------------------------------------------

def plan_env(tmp_path):
    state = StateService()
    state.set_state("plan-1", dict(PLAN_STATE))
    state.set_state("graph:g1", dict(GRAPH_STATE))
    fe = FakeEvents([event("e1", "plan-1")])
    fa = FakeArtifacts()
    svc = EvidenceServices(state=state, events=fe, artifacts=fa)
    return state, fe, fa, svc


class TestVerificationHarness:
    def test_id_name_version(self):
        h = VerificationHarness(services([], [], []))
        assert h.id == "verification"
        assert h.name == "Execution Verification"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = VerificationHarness(services([], [], []))
        reg.register(h)
        assert reg.get("verification") is h

    def test_run_without_task_raises(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        ctx = HarnessContext(run_id="r1", harness="verification", target="plan-1",
                             started_at=utcnow())
        with pytest.raises(VerificationError):
            h.run(ctx)

    def _ctx(self, run_id, task, **config):
        return HarnessContext(run_id=run_id, harness="verification",
                              target=task.execution_ref, started_at=utcnow(),
                              config={"task": task, **config})

    def test_verify_pass_with_file_check(self, tmp_path):
        (tmp_path / "result.json").write_text('{"ok": true}', encoding="utf-8")
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="plan-1", base_dir=str(tmp_path),
            postconditions=[Check(name="artifact", kind=CheckKind.FILE_EXISTS,
                                  params={"path": "result.json"})])
        ctx = self._ctx("r-pass", task)
        h.run(ctx)
        h.verify(ctx, None)  # không raise
        verdict = state.get_state("r-pass")["verification"]["verdict"]
        assert verdict == "pass"

    def test_verify_fail_raises_and_persists(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="plan-1", base_dir=str(tmp_path),
            postconditions=[Check(name="missing", kind=CheckKind.FILE_EXISTS,
                                  params={"path": "nope.txt"})])
        ctx = self._ctx("r-fail", task)
        h.run(ctx)
        with pytest.raises(VerificationError) as exc:
            h.verify(ctx, None)
        assert "verification failed" in str(exc.value)
        # AC5: persist TRƯỚC raise — state có verdict fail
        assert state.get_state("r-fail")["verification"]["verdict"] == "fail"

    def test_verify_skipped_inconclusive_no_raise(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="plan-1", base_dir=str(tmp_path),
            postconditions=[Check(name="t", kind=CheckKind.TEST_RUN)])  # runner None
        ctx = self._ctx("r-inc", task)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-inc")["verification"]["verdict"] == "inconclusive"

    def test_verdict_artifact_convention(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="plan-1", base_dir=str(tmp_path),
            postconditions=[Check(name="f", kind=CheckKind.FILE_EXISTS,
                                  params={"path": "x"})])
        # file không tồn tại → FAIL nhưng vẫn persist artifact
        ctx = self._ctx("r-art", task)
        h.run(ctx)
        try:
            h.verify(ctx, None)
        except VerificationError:
            pass
        stored = [c for c, _ in fa.stored if c.metadata.get("kind") == "verdict"]
        assert len(stored) == 1
        contract = stored[0]
        assert contract.id == "harness:r-art:verdict"
        assert contract.storage_path == "harness/r-art/verdict.json"
        assert contract.metadata["run_id"] == "r-art"

    def test_get_verdict_from_state(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="plan-1", base_dir=str(tmp_path),
            postconditions=[Check(name="f", kind=CheckKind.FILE_EXISTS,
                                  params={"path": "x"})])
        ctx = self._ctx("r-get", task)
        h.run(ctx)
        try:
            h.verify(ctx, None)
        except VerificationError:
            pass
        result = h.get_verdict("r-get")
        assert result is not None
        assert result.verdict == Verdict.FAIL
        assert result.execution_ref == "plan-1"

    def test_get_verdict_unknown_run(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        assert h.get_verdict("missing-run") is None

    def test_full_runner_execute_pass(self, tmp_path):
        """AC5: H1 runner execute — run thành công → PASS + evidence đầy đủ."""
        import tempfile
        from pathlib import Path as P

        state = StateService()
        state.set_state("plan-1", dict(PLAN_STATE))
        with tempfile.TemporaryDirectory() as art_dir:
            bus = EventBus()
            artifacts = ArtifactService(P(art_dir), bus)
            fe = FakeEvents([event("e1", "plan-1")])
            svc = EvidenceServices(state=state, events=fe, artifacts=artifacts)
            h = VerificationHarness(svc, state_service=state, artifact_service=artifacts)
            task = VerificationTask(
                execution_ref="plan-1", base_dir=str(tmp_path),
                postconditions=[Check(name="f", kind=CheckKind.FILE_EXISTS,
                                      params={"path": "x"})])
            # file tồn tại → PASS
            (tmp_path / "x").write_text("ok", encoding="utf-8")
            runner = HarnessRunner(state_service=state, artifact_service=artifacts)
            ctx = runner.create_context(h, "plan-1", config={"task": task})
            report = runner.execute(h, ctx)
            assert report.result.status == HarnessRunStatus.COMPLETED
            st = state.get_state(ctx.run_id)
            assert st["verification"]["verdict"] == "pass"
            # H1 evidence cũng đầy đủ (INV-018)
            assert len(st["artifacts"]) >= 2

    def test_full_runner_execute_fail(self, tmp_path):
        """AC5: verify raise → run FAILED nhưng verification persist verdict fail."""
        import tempfile
        from pathlib import Path as P

        state = StateService()
        state.set_state("plan-1", dict(PLAN_STATE))
        with tempfile.TemporaryDirectory() as art_dir:
            bus = EventBus()
            artifacts = ArtifactService(P(art_dir), bus)
            fe = FakeEvents([event("e1", "plan-1")])
            svc = EvidenceServices(state=state, events=fe, artifacts=artifacts)
            h = VerificationHarness(svc, state_service=state, artifact_service=artifacts)
            task = VerificationTask(
                execution_ref="plan-1", base_dir=str(tmp_path),
                postconditions=[Check(name="f", kind=CheckKind.FILE_EXISTS,
                                      params={"path": "missing"})])
            runner = HarnessRunner(state_service=state, artifact_service=artifacts,
                                   diagnose_on_failure=False)
            ctx = runner.create_context(h, "plan-1", config={"task": task})
            report = runner.execute(h, ctx)
            assert report.result.status == HarnessRunStatus.FAILED
            st = state.get_state(ctx.run_id)
            assert st["verification"]["verdict"] == "fail"

    def test_graph_task_verdict_pass(self, tmp_path):
        """Graph-namespace: evidence đủ (events rỗng OK) + file check → PASS."""
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="graph:g1", base_dir=str(tmp_path),
            postconditions=[Check(name="f", kind=CheckKind.FILE_EXISTS,
                                  params={"path": "x"})])
        (tmp_path / "x").write_text("ok", encoding="utf-8")
        ctx = self._ctx("r-graph", task)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-graph")["verification"]["verdict"] == "pass"

    def test_preconditions_checked(self, tmp_path):
        state, fe, fa, svc = plan_env(tmp_path)
        h = VerificationHarness(svc, state_service=state, artifact_service=fa)
        task = VerificationTask(
            execution_ref="plan-1", base_dir=str(tmp_path),
            preconditions=[Check(name="pre", kind=CheckKind.FILE_EXISTS,
                                 params={"path": "no-pre"})])
        ctx = self._ctx("r-pre", task)
        h.run(ctx)
        with pytest.raises(VerificationError):
            h.verify(ctx, None)
        assert state.get_state("r-pre")["verification"]["verdict"] == "fail"


# ---------------------------------------------------------------------------
# Config + wiring (T7)
# ---------------------------------------------------------------------------

class TestConfigWiring:
    def test_execution_settings_defaults(self):
        s = ExecutionSettings()
        assert s.event_window == 10_000
        assert s.persist_verdict_artifact is True

    def test_execution_settings_forbid_extra(self):
        with pytest.raises(ValidationError):
            ExecutionSettings(nope=1)

    def test_settings_has_execution(self):
        s = Settings()
        assert s.execution.event_window == 10_000

    def test_runtime_kernel_wires_verification_harness(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        harness = kernel.container.resolve(VerificationHarness)
        assert harness.id == "verification"
        reg = kernel.container.resolve(HarnessRegistry)
        assert "verification" in reg.list()

    def test_evidence_with_real_event_service(self, tmp_path):
        """Duck-typing với EventService thật (SQLite audit)."""
        from pathlib import Path as P

        bus = EventBus()
        from aios_core.kernel.services import EventService
        es = EventService(bus, P(tmp_path) / "audit.db")
        es.emit(EventType.WORKFLOW_STARTED, {"execution_id": "plan-1"})
        es.emit(EventType.TOOL_FINISHED, {"execution_id": "plan-1"})
        es.emit(EventType.TOOL_FINISHED, {"execution_id": "other"})
        state = StateService()
        state.set_state("plan-1", dict(PLAN_STATE))
        svc = EvidenceServices(state=state, events=es, artifacts=FakeArtifacts())
        ev = collect_evidence(VerificationTask(execution_ref="plan-1"), svc)
        assert ev["namespace"] == "plan"
        assert len(ev["runtime-events.json"]) == 2  # filter execution_id
        assert has_critical_evidence(ev)
