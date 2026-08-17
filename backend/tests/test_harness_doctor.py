"""TASK-034 — Doctor & Readiness tests (M6-H5): checks, scorer, harnesses."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aios_core.config import DoctorSettings, Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.doctor import (
    DoctorChecks,
    DoctorError,
    DoctorHarness,
    DoctorKind,
    DoctorResult,
    DoctorStatus,
    HardGate,
    ReadinessError,
    ReadinessHarness,
    ReadinessReport,
    ReadinessScorer,
)
from aios_core.kernel.services import StateService


def ok_result(kind=DoctorKind.ARCHITECTURE, score=1.0):
    return DoctorResult(kind=kind, status=DoctorStatus.PASS, score=score,
                        checks_total=1, checks_passed=1)


def ctx_for(run_id, harness_id, **config):
    return HarnessContext(run_id=run_id, harness=harness_id, target="x",
                          started_at=utcnow(), config=config)


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_doctor_kind_13(self):
        assert len(list(DoctorKind)) == 13
        names = {k.value for k in DoctorKind}
        assert names == {"architecture", "runtime", "workflow", "agent",
                         "capability", "tool", "memory", "model", "policy",
                         "registry", "performance", "security", "evidence"}

    def test_doctor_status_4(self):
        assert {s.value for s in DoctorStatus} == {"pass", "warning", "error",
                                                   "unknown"}

    def test_result_defaults(self):
        r = DoctorResult(kind=DoctorKind.RUNTIME, status=DoctorStatus.PASS)
        assert r.score == 0.0 and r.details == []
        assert r.checks_total == 0 and r.checks_passed == 0

    def test_result_extra_forbid(self):
        with pytest.raises(ValidationError):
            DoctorResult(kind=DoctorKind.RUNTIME, status=DoctorStatus.PASS, nope=1)

    def test_hard_gate_defaults(self):
        g = HardGate(name="policy", passed=True)
        assert g.detail == ""

    def test_report_defaults(self):
        r = ReadinessReport()
        assert r.dimensions == {} and r.overall == 0.0
        assert r.ready is False and r.hard_gates == []


# ---------------------------------------------------------------------------
# DoctorChecks (T3)
# ---------------------------------------------------------------------------

class TestChecks:
    def test_placeholder_pass_all_kinds(self):
        checks = DoctorChecks()
        results = checks.run_all()
        assert len(results) == 13
        assert all(r.status == DoctorStatus.PASS for r in results)
        assert all(r.score == 1.0 for r in results)

    def test_run_placeholder(self):
        checks = DoctorChecks()
        r = checks.run(DoctorKind.MEMORY)
        assert r.status == DoctorStatus.PASS
        assert r.checks_total == 1 and r.checks_passed == 1

    def test_register_custom(self):
        checks = DoctorChecks()
        checks.register(DoctorKind.SECURITY,
                        lambda: (DoctorStatus.ERROR, 0.0, ["exploit found"]))
        r = checks.run(DoctorKind.SECURITY)
        assert r.status == DoctorStatus.ERROR
        assert r.score == 0.0
        assert r.details == ["exploit found"]

    def test_register_override_placeholder(self):
        checks = DoctorChecks()
        checks.register(DoctorKind.POLICY,
                        lambda: (DoctorStatus.WARNING, 0.6, ["warn"]))
        assert checks.run(DoctorKind.POLICY).status == DoctorStatus.WARNING

    def test_check_fn_raise_error(self):
        def boom():
            raise RuntimeError("probe exploded")
        checks = DoctorChecks()
        checks.register(DoctorKind.MODEL, boom)
        r = checks.run(DoctorKind.MODEL)
        assert r.status == DoctorStatus.ERROR  # C2-02
        assert r.score == 0.0
        assert "probe exploded" in r.details[0]

    def test_run_all_subset(self):
        checks = DoctorChecks()
        results = checks.run_all([DoctorKind.AGENT, DoctorKind.TOOL])
        assert [r.kind for r in results] == [DoctorKind.AGENT, DoctorKind.TOOL]

    def test_run_all_sorted_enum_order(self):
        checks = DoctorChecks()
        results = checks.run_all()
        assert [r.kind for r in results] == list(DoctorKind)  # C2-01

    def test_score_clamped(self):
        checks = DoctorChecks()
        checks.register(DoctorKind.PERFORMANCE,
                        lambda: (DoctorStatus.PASS, 99.0, ["fast"]))
        r = checks.run(DoctorKind.PERFORMANCE)
        assert r.score == 1.0  # clamp 0..1

    def test_pass_counts(self):
        checks = DoctorChecks()
        checks.register(DoctorKind.TOOL,
                        lambda: (DoctorStatus.PASS, 1.0, []))
        r = checks.run(DoctorKind.TOOL)
        assert r.checks_passed == 1


# ---------------------------------------------------------------------------
# DoctorHarness (T4)
# ---------------------------------------------------------------------------

class TestDoctorHarness:
    def test_id_name_version(self):
        h = DoctorHarness(DoctorChecks())
        assert h.id == "doctor"
        assert h.name == "Doctor"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = DoctorHarness(DoctorChecks())
        reg.register(h)
        assert reg.get("doctor") is h

    def test_run_all_kinds(self):
        h = DoctorHarness(DoctorChecks())
        payload = h.run(ctx_for("r", "doctor"))
        assert len(payload) == 13

    def test_run_subset_kinds(self):
        h = DoctorHarness(DoctorChecks())
        payload = h.run(ctx_for("r", "doctor", kinds=["architecture", "model"]))
        assert [p["kind"] for p in payload] == ["architecture", "model"]

    def test_run_invalid_kind_raises(self):
        h = DoctorHarness(DoctorChecks())
        with pytest.raises(DoctorError):
            h.run(ctx_for("r", "doctor", kinds=["not-a-kind"]))

    def test_verify_pass(self):
        state = StateService()
        h = DoctorHarness(DoctorChecks(), state_service=state)
        ctx = ctx_for("r-pass", "doctor", strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-pass")["doctor"]["metrics"]["doctors_run"] == 13

    def test_verify_error_strict_raises_and_persists(self):
        state = StateService()
        checks = DoctorChecks()
        checks.register(DoctorKind.SECURITY,
                        lambda: (DoctorStatus.ERROR, 0.0, ["bad"]))
        h = DoctorHarness(checks, state_service=state)
        ctx = ctx_for("r-fail", "doctor", strict=True)
        h.run(ctx)
        with pytest.raises(DoctorError):
            h.verify(ctx, None)
        # persist TRƯỚC raise
        assert state.get_state("r-fail")["doctor"]["metrics"]["error"] == 1

    def test_verify_error_not_strict_warning(self):
        state = StateService()
        checks = DoctorChecks()
        checks.register(DoctorKind.SECURITY,
                        lambda: (DoctorStatus.ERROR, 0.0, ["bad"]))
        h = DoctorHarness(checks, state_service=state)
        ctx = ctx_for("r-warn", "doctor", strict=False)
        h.run(ctx)
        h.verify(ctx, None)  # không raise

    def test_verify_warning_not_raise(self):
        checks = DoctorChecks()
        checks.register(DoctorKind.POLICY,
                        lambda: (DoctorStatus.WARNING, 0.5, ["warn"]))
        h = DoctorHarness(checks)
        ctx = ctx_for("r-w", "doctor", strict=True)
        h.run(ctx)
        h.verify(ctx, None)  # P3-01: WARNING không raise

    def test_verify_without_run_raises(self):
        h = DoctorHarness(DoctorChecks())
        with pytest.raises(DoctorError):
            h.verify(ctx_for("r", "doctor"), None)

    def test_get_results(self):
        state = StateService()
        h = DoctorHarness(DoctorChecks(), state_service=state)
        ctx = ctx_for("r-g", "doctor", strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        results = h.get_results("r-g")
        assert results["metrics"]["doctors_run"] == 13

    def test_get_results_unknown(self):
        h = DoctorHarness(DoctorChecks(), state_service=StateService())
        assert h.get_results("nope") is None

    def test_full_runner_execute_error(self):
        state = StateService()
        checks = DoctorChecks()
        checks.register(DoctorKind.SECURITY,
                        lambda: (DoctorStatus.ERROR, 0.0, ["bad"]))
        h = DoctorHarness(checks, state_service=state)
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, "x", config={"strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.FAILED
        assert state.get_state(ctx.run_id)["doctor"]["metrics"]["error"] == 1

    def test_full_runner_execute_pass(self):
        state = StateService()
        h = DoctorHarness(DoctorChecks(), state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "x", config={"strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


# ---------------------------------------------------------------------------
# ReadinessScorer (T5a)
# ---------------------------------------------------------------------------

class TestScorer:
    def test_overall_mean(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result(score=1.0), ok_result(
            kind=DoctorKind.MODEL, score=0.5)])
        assert report.overall == 0.75
        assert report.dimensions == {"architecture": 1.0, "model": 0.5}

    def test_unknown_score_zero(self):
        scorer = ReadinessScorer()
        r_unknown = DoctorResult(kind=DoctorKind.TOOL, status=DoctorStatus.UNKNOWN,
                                 score=0.0)
        report = scorer.score([ok_result(score=1.0), r_unknown])
        assert report.overall == 0.5  # C1-02: unknown → 0.0

    def test_empty_results_overall_zero(self):
        scorer = ReadinessScorer()
        report = scorer.score([])
        assert report.overall == 0.0
        # min_overall default 0.0 → overall gate pass (0.0 >= 0.0)
        assert report.ready is True

    def test_empty_results_with_min_overall_not_ready(self):
        scorer = ReadinessScorer(min_overall=0.1)
        report = scorer.score([])
        assert report.ready is False

    def test_ready_all_pass(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result()])
        assert report.ready is True
        assert report.summary.startswith("READY")

    def test_policy_violation_blocks(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result()], policy_violations=2)
        assert report.ready is False  # dù overall 1.0 — PLAN hard gate
        assert "RELEASE BLOCKED" in report.summary
        policy_gate = report.hard_gates[0]
        assert policy_gate.name == "policy" and policy_gate.passed is False

    def test_policy_gate_first(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result()], policy_violations=1)
        assert [g.name for g in report.hard_gates] == ["policy", "overall"]

    def test_zero_violations_ok(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result()], policy_violations=0)
        assert report.hard_gates[0].passed is True

    def test_min_overall_gate(self):
        scorer = ReadinessScorer(min_overall=0.9)
        report = scorer.score([ok_result(score=0.5)])
        assert report.ready is False
        assert report.hard_gates[1].passed is False

    def test_min_overall_default_zero(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result(score=0.1)])
        assert report.ready is True  # P2-03: default không block

    def test_policy_gate_disabled(self):
        scorer = ReadinessScorer(policy_gate=False)
        report = scorer.score([ok_result()], policy_violations=5)
        assert len(report.hard_gates) == 1  # chỉ overall
        assert report.ready is True

    def test_metrics_counts(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result(), ok_result(
            kind=DoctorKind.MODEL, score=0.0)], policy_violations=1)
        assert report.metrics["doctors_run"] == 2
        assert report.metrics["hard_gates_total"] == 2
        assert report.metrics["hard_gates_passed"] == 1

    def test_reproducible(self):
        scorer = ReadinessScorer(min_overall=0.5, policy_gate=True)
        report = scorer.score([ok_result()])
        assert report.reproducible == {"min_overall": 0.5, "policy_gate": True}

    def test_deterministic_repeat(self):
        scorer = ReadinessScorer()
        results = [ok_result(score=0.8), ok_result(kind=DoctorKind.MODEL, score=0.6)]
        a = scorer.score(results).model_dump()
        b = scorer.score(results).model_dump()
        assert a == b

    def test_dimensions_only_run_kinds(self):
        scorer = ReadinessScorer()
        report = scorer.score([ok_result(kind=DoctorKind.SECURITY)])
        assert set(report.dimensions) == {"security"}  # P3-02

    def test_ready_false_summary_not_ready(self):
        scorer = ReadinessScorer(min_overall=0.9)
        report = scorer.score([ok_result(score=0.5)])
        assert report.summary.startswith("NOT READY")


# ---------------------------------------------------------------------------
# ReadinessHarness (T5b)
# ---------------------------------------------------------------------------

class TestReadinessHarness:
    def test_id_name_version(self):
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer())
        assert h.id == "readiness"
        assert h.name == "Readiness"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer())
        reg.register(h)
        assert reg.get("readiness") is h

    def test_run_ready(self):
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer())
        payload = h.run(ctx_for("r", "readiness", strict=True))
        assert payload["ready"] is True
        assert len(payload["dimensions"]) == 13

    def test_run_policy_violations(self):
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer())
        payload = h.run(ctx_for("r", "readiness", policy_violations=1,
                                strict=True))
        assert payload["ready"] is False
        assert "RELEASE BLOCKED" in payload["summary"]

    def test_verify_pass(self):
        state = StateService()
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer(),
                             state_service=state)
        ctx = ctx_for("r-pass", "readiness", strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-pass")["readiness"]["ready"] is True

    def test_verify_blocked_strict_raises_and_persists(self):
        state = StateService()
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer(),
                             state_service=state)
        ctx = ctx_for("r-block", "readiness", policy_violations=3, strict=True)
        h.run(ctx)
        with pytest.raises(ReadinessError):
            h.verify(ctx, None)
        # persist TRƯỚC raise
        assert state.get_state("r-block")["readiness"]["ready"] is False
        assert "RELEASE BLOCKED" in state.get_state("r-block")["readiness"]["summary"]

    def test_readiness_error_subclass_doctor(self):
        assert issubclass(ReadinessError, DoctorError)

    def test_verify_not_strict_warning(self):
        state = StateService()
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer(),
                             state_service=state)
        ctx = ctx_for("r-warn", "readiness", policy_violations=1, strict=False)
        h.run(ctx)
        h.verify(ctx, None)  # không raise

    def test_verify_without_run_raises(self):
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer())
        with pytest.raises(ReadinessError):
            h.verify(ctx_for("r", "readiness"), None)

    def test_get_report(self):
        state = StateService()
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer(),
                             state_service=state)
        ctx = ctx_for("r-g", "readiness", strict=True)
        h.run(ctx)
        h.verify(ctx, None)
        report = h.get_report("r-g")
        assert report["ready"] is True
        assert report["overall"] == 1.0

    def test_get_report_unknown(self):
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer(),
                             state_service=StateService())
        assert h.get_report("nope") is None

    def test_shared_checks_with_doctor_harness(self):
        """P1-01: doctor + readiness dùng chung DoctorChecks instance."""
        checks = DoctorChecks()
        checks.register(DoctorKind.SECURITY,
                        lambda: (DoctorStatus.ERROR, 0.0, ["bad"]))
        doctor = DoctorHarness(checks)
        readiness = ReadinessHarness(checks, ReadinessScorer())
        d_payload = doctor.run(ctx_for("r1", "doctor"))
        assert any(p["status"] == "error" for p in d_payload)
        r_payload = readiness.run(ctx_for("r2", "readiness"))
        assert r_payload["dimensions"]["security"] == 0.0

    def test_full_runner_execute_blocked(self):
        state = StateService()
        h = ReadinessHarness(DoctorChecks(), ReadinessScorer(),
                             state_service=state)
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, "x", config={
            "policy_violations": 1, "strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.FAILED
        assert state.get_state(ctx.run_id)["readiness"]["ready"] is False


# ---------------------------------------------------------------------------
# Config + wiring (T6)
# ---------------------------------------------------------------------------

class TestConfigWiring:
    def test_doctor_settings_defaults(self):
        d = DoctorSettings()
        assert d.strict is True
        assert d.min_overall == 0.0
        assert d.policy_gate is True

    def test_doctor_settings_extra_forbid(self):
        with pytest.raises(ValidationError):
            DoctorSettings(nope=1)

    def test_settings_has_doctor(self):
        assert Settings().doctor.policy_gate is True

    def test_runtime_kernel_wires_doctor_harnesses(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        assert kernel.container.resolve(DoctorHarness).id == "doctor"
        assert kernel.container.resolve(ReadinessHarness).id == "readiness"

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
                                   "behavioral"}  # M13-P0 TASK-089

    def test_registry_register_shared_checks(self, tmp_path):
        from aios_core.config import ArtifactsSettings, AuditSettings, Settings
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings(
            audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
            artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        ))
        doctor = kernel.container.resolve(DoctorHarness)
        readiness = kernel.container.resolve(ReadinessHarness)
        # checks injectable qua doctor — readiness thấy kết quả (shared instance)
        payload = doctor.run(ctx_for("r", "doctor", kinds=["architecture"]))
        assert payload[0]["kind"] == "architecture"

    def test_readiness_report_extra_forbid(self):
        with pytest.raises(ValidationError):
            ReadinessReport(nope=1)

    def test_hard_gate_extra_forbid(self):
        with pytest.raises(ValidationError):
            HardGate(name="policy", passed=True, nope=1)

    def test_run_result_summary_statuses(self):
        checks = DoctorChecks()
        checks.register(DoctorKind.SECURITY,
                        lambda: (DoctorStatus.ERROR, 0.0, ["bad"]))
        h = DoctorHarness(checks)
        payload = h.run(ctx_for("r", "doctor"))
        summary = {p["kind"]: p["status"] for p in payload}
        assert summary["security"] == "error"
        assert summary["architecture"] == "pass"
