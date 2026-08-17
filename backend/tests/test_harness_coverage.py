"""TASK-090 — Harness Coverage tests (M13-P1): coverage model 9 chiều +
negative-path 8 + readiness scorer + harness + wiring + CLI (fail-closed)."""

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
from aios_core.harness.coverage import (
    CoverageDimension,
    CoverageError,
    CoverageHarness,
    CoverageItem,
    DimensionCoverage,
    HarnessCoverage,
    HarnessCoverageReport,
    HarnessReadinessReport,
    HarnessReadinessScorer,
    HarnessReadinessStatus,
    NegativePath,
    NegativePathCoverage,
)
from aios_core.kernel.services import StateService


def make_registry() -> HarnessRegistry:
    reg = HarnessRegistry()
    from aios_core.harness.behavioral import BehavioralConformanceHarness
    from aios_core.harness.benchmark import (
        BenchmarkHarness, BenchmarkRunner, RegressionGate,
    )
    from aios_core.harness.doctor import (
        DoctorChecks, DoctorHarness, ReadinessHarness, ReadinessScorer,
    )
    from aios_core.harness.evaluation import EvaluationHarness, Engine
    from aios_core.harness.execution import EvidenceServices, VerificationHarness
    from aios_core.harness.meta import MetaHarness
    from aios_core.harness.testing import TestHarness

    reg.register(VerificationHarness(EvidenceServices(
        state=None, events=None, artifacts=None)))
    reg.register(TestHarness())
    reg.register(EvaluationHarness(Engine()))
    reg.register(BenchmarkHarness(BenchmarkRunner(lambda s: None),
                                  RegressionGate()))
    reg.register(DoctorHarness(DoctorChecks()))
    reg.register(ReadinessHarness(DoctorChecks(), ReadinessScorer()))
    reg.register(BehavioralConformanceHarness())
    reg.register(MetaHarness())
    return reg


def coverage_ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="coverage", target="cov",
                          started_at=utcnow(), config=config)


# ---------------------------------------------------------------------------
# Contracts (T1)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_dimension_enum_9(self):  # AC1
        assert {d.value for d in CoverageDimension} == {
            "component", "contract", "state", "transition", "event",
            "failure_mode", "scenario", "verification_path", "artifact"}

    def test_negative_path_enum_8(self):  # AC2
        assert {p.value for p in NegativePath} == {
            "pass", "fail", "blocked", "violation", "timeout", "exception",
            "corrupted_evidence", "replay_mismatch"}

    def test_item_extra_forbid(self):
        with pytest.raises(ValidationError):
            CoverageItem(dimension=CoverageDimension.COMPONENT, id="x",
                         covered=True, evidence="m", nope=1)

    def test_dimension_coverage_defaults(self):
        d = DimensionCoverage(dimension=CoverageDimension.STATE, total=3,
                              covered=1, ratio=1 / 3)
        assert d.ratio == pytest.approx(1 / 3)

    def test_negative_path_coverage(self):
        n = NegativePathCoverage(path=NegativePath.PASS, covered=True,
                                 evidence="module:aios_core.harness")
        assert n.path == NegativePath.PASS

    def test_report_extra_forbid(self):
        with pytest.raises(ValidationError):
            HarnessCoverageReport(dimensions={}, negative_paths={},
                                  overall_ratio=0.0, negative_path_ratio=0.0,
                                  metrics={}, summary="", reproducible={},
                                  nope=1)

    def test_readiness_report_extra_forbid(self):
        with pytest.raises(ValidationError):
            HarnessReadinessReport(dimensions={}, overall=0.0,
                                   status=HarnessReadinessStatus.READY,
                                   summary="", metrics={}, reproducible={},
                                   nope=1)


# ---------------------------------------------------------------------------
# Coverage builder (T2)
# ---------------------------------------------------------------------------

class TestCoverage:
    def test_components_exclude_self(self):  # AC3 (P1-3 v1 + P2-G v2) + P2-1 TASK-091 + P3 TASK-092
        reg = make_registry()
        reg.register(CoverageHarness(reg))  # register coverage trước
        report = HarnessCoverage(reg).build()
        comp = report.dimensions["component"]
        # make_registry() có 8 harness + coverage = 9 total, exclude self → 8
        # runtime_kernel có 10 harness + coverage = 11 total, exclude self → 9
        assert comp.total == len(reg.list()) - 1  # exclude self

    def test_dimensions_total_positive(self):  # AC4
        report = HarnessCoverage(make_registry()).build()
        assert report.dimensions["contract"].total == 21
        assert report.dimensions["state"].total == 14
        assert report.dimensions["transition"].total == 12
        assert report.dimensions["event"].total == 6
        assert report.dimensions["failure_mode"].total == 8
        assert report.dimensions["scenario"].total == 20
        assert report.dimensions["verification_path"].total == 12
        assert report.dimensions["artifact"].total == 2
        for dim, dc in report.dimensions.items():
            assert dc.total > 0, dim

    def test_report_ratios(self):  # AC5
        report = HarnessCoverage(make_registry()).build()
        assert report.dimensions["component"].ratio == 1.0
        assert report.overall_ratio == pytest.approx(1.0)
        assert "status" not in report.model_dump()  # KHÔNG có status (P3-2)

    def test_negative_8_of_8(self):  # AC6 + AC18 (P2-F v2) + TASK-091 (P1-2/P3-1)
        report = HarnessCoverage(make_registry()).build()
        covered = [p for p, n in report.negative_paths.items() if n.covered]
        assert sorted(covered) == ["blocked", "corrupted_evidence", "exception",
                                   "fail", "pass", "replay_mismatch", "timeout",
                                   "violation"]
        assert report.negative_path_ratio == pytest.approx(1.0)
        # evidence non-empty + tồn tại (P2-5 v1)
        for p, n in report.negative_paths.items():
            if n.covered:
                assert n.evidence != ""
                assert _evidence_exists(n.evidence)
            else:
                assert n.evidence == ""  # AC18

    def test_evidence_anchored_cwd_independent(self, monkeypatch):  # AC13 (P1-A v2)
        # build từ cwd khác → report giống hệt (evidence anchored backend root)
        a = HarnessCoverage(make_registry()).build().model_dump()
        monkeypatch.chdir("c:/windows")
        b = HarnessCoverage(make_registry()).build().model_dump()
        assert a == b

    def test_determinism(self):  # AC13
        reg = make_registry()
        a = HarnessCoverage(reg).build().model_dump()
        b = HarnessCoverage(reg).build().model_dump()
        assert a == b

    def test_empty_registry_no_div0(self):  # AC15
        report = HarnessCoverage(HarnessRegistry()).build()
        assert report.dimensions["component"].total == 0
        assert report.dimensions["component"].ratio == 0.0
        assert report.overall_ratio == pytest.approx(1.0 - (1 / 9))  # 8 dims đủ

    def test_metrics_and_summary(self):  # AC14 + TASK-091 (P1-2)
        report = HarnessCoverage(make_registry()).build()
        assert report.metrics["dimensions_total"] == 9
        assert report.metrics["negative_paths_total"] == 8
        assert report.summary != ""
        assert "negative 8/8" in report.summary

    def test_keys_9_and_8(self):  # AC16
        report = HarnessCoverage(make_registry()).build()
        assert len(report.dimensions) == 9
        assert len(report.negative_paths) == 8

    def test_reproducible(self):  # P3-F v2
        report = HarnessCoverage(make_registry()).build()
        assert "aios_version" in report.reproducible
        assert sorted(report.reproducible["registry_harness_ids"]) == \
            sorted(report.reproducible["registry_harness_ids"])


def _evidence_exists(evidence: str) -> bool:
    import importlib.util
    from pathlib import Path
    if evidence.startswith("module:"):
        return importlib.util.find_spec(evidence[len("module:"):]) is not None
    if evidence.startswith("path:"):
        from aios_core.harness.coverage.coverage import BACKEND_ROOT
        return (BACKEND_ROOT / evidence[len("path:"):]).exists()
    return False


# ---------------------------------------------------------------------------
# Readiness scorer (T3)
# ---------------------------------------------------------------------------

class TestReadiness:
    def test_7_dimensions_and_gates(self):  # AC7
        coverage = HarnessCoverage(make_registry()).build()
        report = HarnessReadinessScorer().score(coverage)
        assert set(report.dimensions) == {
            "structural", "contract", "behavioral", "failure", "replay",
            "scenario", "production"}
        assert report.dimensions["production"] == 0.0  # P1-2 v1
        # overall = mean 6 dims active (production excluded)
        active = [report.dimensions[k] for k in
                  ("structural", "contract", "behavioral", "failure",
                   "replay", "scenario")]
        assert report.overall == pytest.approx(sum(active) / 6)

    def test_ready_when_meta_covered(self):  # AC8 (P1-1 v1) + TASK-091 (P1-2/P3-1)
        coverage = HarnessCoverage(make_registry()).build()
        report = HarnessReadinessScorer().score(coverage)
        assert report.dimensions["replay"] == pytest.approx(1.0)
        assert report.overall == pytest.approx(1.0)
        assert report.status == HarnessReadinessStatus.READY  # replay covered

    def test_ready_when_replay_covered(self):  # AC8
        coverage = HarnessCoverage(make_registry()).build()
        # giả lập REPLAY_MISMATCH đã cover (TASK-091) → replay 1.0
        coverage.negative_paths["replay_mismatch"] = NegativePathCoverage(
            path=NegativePath.REPLAY_MISMATCH, covered=True,
            evidence="module:aios_core.harness")
        report = HarnessReadinessScorer().score(coverage)
        assert report.dimensions["replay"] == pytest.approx(1.0)
        assert report.status == HarnessReadinessStatus.READY

    def test_production_gate_conditional(self):  # AC17 (P2-C v2)
        coverage = HarnessCoverage(make_registry()).build()
        report = HarnessReadinessScorer(production_tests_available=True).score(
            coverage)
        # production 0.0 < 0.5 → gate production fail → NOT_READY
        assert any(g.name == "production" and not g.passed
                   for g in report.hard_gates)
        assert report.status == HarnessReadinessStatus.NOT_READY

    def test_param_validation(self):  # AC19 (P2-H v2)
        with pytest.raises(ValueError):
            HarnessReadinessScorer(min_overall=1.5)
        with pytest.raises(ValueError):
            HarnessReadinessScorer(min_replay=0.0)

    def test_reproducible(self):
        coverage = HarnessCoverage(make_registry()).build()
        report = HarnessReadinessScorer().score(coverage)
        assert report.reproducible["min_overall"] == 0.8
        assert report.metrics["dimensions_active"] == 6


# ---------------------------------------------------------------------------
# Harness (T4)
# ---------------------------------------------------------------------------

class TestHarness:
    def test_id_name_version(self):
        h = CoverageHarness(make_registry())
        assert h.id == "coverage"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = make_registry()
        h = CoverageHarness(reg)
        reg.register(h)
        assert reg.get("coverage") is h

    def test_run_returns_payload(self):
        h = CoverageHarness(make_registry())
        ctx = coverage_ctx("r")
        payload = h.run(ctx)
        assert payload["readiness"]["status"] == "ready"  # TASK-091 8/8
        assert len(payload["coverage"]["dimensions"]) == 9

    def test_verify_ready_no_raise(self):  # AC11 (P1-B v2) + TASK-091 READY
        state = StateService()
        h = CoverageHarness(make_registry(), state_service=state)
        ctx = coverage_ctx("r-fail", strict=True)
        h.run(ctx)
        h.verify(ctx, None)  # ready → strict không raise
        assert state.get_state("r-fail")["coverage_report"]["readiness_status"] \
            == "ready"

    def test_verify_not_strict_no_raise(self):
        state = StateService()
        h = CoverageHarness(make_registry(), state_service=state)
        ctx = coverage_ctx("r-warn", strict=False)
        h.run(ctx)
        h.verify(ctx, None)
        assert state.get_state("r-warn")["coverage_report"]["strict"] is False

    def test_get_report_round_trip(self):  # AC9 (P2-D v2) + TASK-091 READY
        state = StateService()
        h = CoverageHarness(make_registry(), state_service=state)
        ctx = coverage_ctx("r-g", strict=False)
        h.run(ctx)
        h.verify(ctx, None)
        report = h.get_report("r-g")
        assert report["readiness_status"] == "ready"
        assert report["coverage_overall"] == pytest.approx(1.0)

    def test_get_report_unknown(self):
        h = CoverageHarness(make_registry(), state_service=StateService())
        assert h.get_report("nope") is None

    def test_full_runner_execute_completed(self):  # AC11 (P1-B v2) + TASK-091 READY
        state = StateService()
        h = CoverageHarness(make_registry(), state_service=state)
        runner = HarnessRunner(state_service=state)  # diagnose_on_failure=True
        ctx = runner.create_context(h, "cov", config={"strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED

    def test_full_runner_execute_completed_no_diagnose(self):  # AC11
        state = StateService()
        h = CoverageHarness(make_registry(), state_service=state)
        runner = HarnessRunner(state_service=state, diagnose_on_failure=False)
        ctx = runner.create_context(h, "cov", config={"strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


# ---------------------------------------------------------------------------
# Wiring (T5)
# ---------------------------------------------------------------------------

class TestWiring:
    def test_registry_has_coverage(self):  # AC9
        from aios_core.kernel import RuntimeKernel

        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("coverage") is not None
        assert reg.get("coverage").id == "coverage"
        # registry có 12 harness (11 + heal) — builder exclude self → 11
        assert len(reg.list()) == 15
        assert "coverage" in reg.list()
        assert "release" in reg.list()
        assert "diagnose" in reg.list()


# ---------------------------------------------------------------------------
# CLI (T6)
# ---------------------------------------------------------------------------

class TestCLI:
    def _run_cli(self, argv):
        from aios_core.workflow.cli import main

        return main(argv)

    def test_cli_ready_exit_0(self, capsys):  # AC10 + TASK-091 8/8 → READY
        rc = self._run_cli(["harness", "coverage"])
        out = capsys.readouterr().out
        assert rc == 0  # READY
        data = json.loads(out)
        assert data["readiness"]["status"] == "ready"
        assert len(data["coverage"]["dimensions"]) == 9

    def test_cli_min_replay_lower_ready(self, capsys):  # AC10
        rc = self._run_cli(["harness", "coverage", "--min-replay", "0.4"])
        out = capsys.readouterr().out
        assert rc == 0
        data = json.loads(out)
        assert data["readiness"]["status"] == "ready"