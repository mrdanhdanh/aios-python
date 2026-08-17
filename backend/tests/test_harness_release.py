"""TASK-092 — Release Gate tests (M13-P3): System Readiness ≠ Harness Trust.

12 AC: 2 score độc lập + release gate cả 2 PASS + fail-closed (BLOCKED).
"""

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
from aios_core.harness.coverage.contracts import (
    HarnessReadinessReport,
    HarnessReadinessStatus,
    HardGate,
)
from aios_core.harness.meta.contracts import MetaReport, MetaStatus
from aios_core.harness.release import (
    ReleaseGateEngine,
    ReleaseGateError,
    ReleaseGateHarness,
    ReleaseGateReport,
    ReleaseGateStatus,
)
from aios_core.kernel.services import StateService


# ---------------------------------------------------------------------------
# Helpers — build reports trực tiếp (engine unit tests)
# ---------------------------------------------------------------------------

def _ready() -> HarnessReadinessReport:
    return HarnessReadinessReport(
        dimensions={"structural": 1.0, "contract": 1.0, "behavioral": 1.0,
                    "failure": 1.0, "replay": 1.0, "scenario": 1.0,
                    "production": 0.0},
        overall=1.0, status=HarnessReadinessStatus.READY,  # placeholder
        hard_gates=[HardGate(name="replay", passed=True, detail="ok"),
                    HardGate(name="overall", passed=True, detail="ok")],
        summary="READY (overall 100.0%)",
        metrics={"dimensions_active": 6, "hard_gates_total": 2,
                 "hard_gates_passed": 2, "production_tests_available": False},
        reproducible={"min_overall": 0.8, "min_replay": 0.75,
                      "production_tests_available": False, "state_ratio": 1.0,
                      "transition_ratio": 1.0, "event_ratio": 1.0,
                      "artifact_ratio": 1.0},
    )


def _not_ready() -> HarnessReadinessReport:
    return HarnessReadinessReport(
        dimensions={"structural": 0.0, "contract": 0.0, "behavioral": 0.0,
                    "failure": 0.0, "replay": 0.0, "scenario": 0.0,
                    "production": 0.0},
        overall=0.0, status=HarnessReadinessStatus.NOT_READY,
        hard_gates=[HardGate(name="replay", passed=False, detail="bad"),
                    HardGate(name="overall", passed=False, detail="bad")],
        summary="NOT READY (overall 0.0%)",
        metrics={"dimensions_active": 6, "hard_gates_total": 2,
                 "hard_gates_passed": 0, "production_tests_available": False},
        reproducible={"min_overall": 0.8, "min_replay": 0.75,
                      "production_tests_available": False, "state_ratio": 0.0,
                      "transition_ratio": 0.0, "event_ratio": 0.0,
                      "artifact_ratio": 0.0},
    )


def _meta(status: MetaStatus) -> MetaReport:
    return MetaReport(
        cases=[],  # rỗng hợp lệ (list[MetaCaseResult])
        all_fail_closed=(status == MetaStatus.PASS),
        status=status,
        metrics={"total": 8, "fail_closed": 8 if status == MetaStatus.PASS else 7,
                 "by_case": {}},
        summary=("meta-harness: 8/8 cases fail-closed -> pass"
                 if status == MetaStatus.PASS else
                 "meta-harness: 1 case bỏ lọt -> fail"),
        reproducible={"aios_version": "1.1.0", "python_version": "3.11",
                      "registry_harness_ids": ["meta"]},
    )


def release_ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="release", target="release",
                          started_at=utcnow(), config=config)


# ---------------------------------------------------------------------------
# AC1 — Hai score độc lập
# ---------------------------------------------------------------------------

class TestIndependentScores:
    def test_two_distinct_types(self):
        from aios_core.harness.coverage.contracts import HarnessReadinessReport
        from aios_core.harness.meta.contracts import MetaReport

        assert HarnessReadinessReport is not MetaReport
        # System Readiness status enum
        assert HarnessReadinessStatus.READY.value == "ready"
        assert HarnessReadinessStatus.NOT_READY.value == "not_ready"
        # Harness Trust status enum
        assert MetaStatus.PASS.value == "pass"
        assert MetaStatus.FAIL.value == "fail"


# ---------------------------------------------------------------------------
# AC2 — Engine pure function
# ---------------------------------------------------------------------------

class TestEnginePure:
    def test_pure_no_io(self):
        eng = ReleaseGateEngine()
        r1 = eng.evaluate(_ready(), _meta(MetaStatus.PASS))
        r2 = eng.evaluate(_ready(), _meta(MetaStatus.PASS))
        assert r1.model_dump() == r2.model_dump()


# ---------------------------------------------------------------------------
# AC3 — PASS yêu cầu CẢ 2
# ---------------------------------------------------------------------------

class TestGatePass:
    def test_both_pass(self):
        rep = ReleaseGateEngine().evaluate(_ready(), _meta(MetaStatus.PASS))
        assert rep.status == ReleaseGateStatus.PASS
        assert rep.both_pass is True
        assert "PASS" in rep.summary


# ---------------------------------------------------------------------------
# AC4 — Fail-closed: readiness NOT_READY → BLOCKED
# ---------------------------------------------------------------------------

class TestGateBlockedReadiness:
    def test_readiness_not_ready_blocks(self):
        rep = ReleaseGateEngine().evaluate(
            _not_ready(), _meta(MetaStatus.PASS))
        assert rep.status == ReleaseGateStatus.BLOCKED
        assert rep.both_pass is False
        assert "system_readiness" in rep.summary
        assert rep.system_readiness["status"] == "not_ready"
        assert rep.harness_trust["status"] == "pass"


# ---------------------------------------------------------------------------
# AC5 — Fail-closed: meta FAIL → BLOCKED
# ---------------------------------------------------------------------------

class TestGateBlockedTrust:
    def test_trust_fail_blocks(self):
        rep = ReleaseGateEngine().evaluate(
            _ready(), _meta(MetaStatus.FAIL))
        assert rep.status == ReleaseGateStatus.BLOCKED
        assert rep.both_pass is False
        assert "harness_trust" in rep.summary
        assert rep.system_readiness["status"] == "ready"
        assert rep.harness_trust["status"] == "fail"


# ---------------------------------------------------------------------------
# AC6 — Report shape (extra="forbid", no timestamp)
# ---------------------------------------------------------------------------

class TestReportShape:
    def test_shape(self):
        rep = ReleaseGateEngine().evaluate(_ready(), _meta(MetaStatus.PASS))
        dump = rep.model_dump()
        assert set(dump) == {
            "system_readiness", "harness_trust", "both_pass", "status",
            "summary", "reproducible"}
        assert "generated_at" not in dump
        assert "timestamp" not in dump
        assert rep.system_readiness["status"] == "ready"
        assert rep.harness_trust["status"] == "pass"

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            ReleaseGateReport(
                system_readiness={}, harness_trust={}, both_pass=True,
                status=ReleaseGateStatus.PASS, summary="", reproducible={},
                nope=1)


# ---------------------------------------------------------------------------
# AC11 — Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_evaluate_twice_identical(self):
        eng = ReleaseGateEngine()
        a = eng.evaluate(_ready(), _meta(MetaStatus.PASS)).model_dump()
        b = eng.evaluate(_ready(), _meta(MetaStatus.PASS)).model_dump()
        assert a == b


# ---------------------------------------------------------------------------
# AC12 — Tách biệt thật (tổng hợp AC4 + AC5)
# ---------------------------------------------------------------------------

class TestSeparationReal:
    def test_two_independent_block_paths(self):
        eng = ReleaseGateEngine()
        # path a: readiness one-sided
        a = eng.evaluate(_not_ready(), _meta(MetaStatus.PASS))
        # path b: trust one-sided
        b = eng.evaluate(_ready(), _meta(MetaStatus.FAIL))
        assert a.status == ReleaseGateStatus.BLOCKED
        assert b.status == ReleaseGateStatus.BLOCKED
        # hai nguyên nhân KHÁC nhau → chứng minh 2 score độc lập
        assert "system_readiness" in a.summary
        assert "harness_trust" in b.summary
        assert a.summary != b.summary


# ---------------------------------------------------------------------------
# AC7 / AC8 — Harness lifecycle + fail-closed verify
# ---------------------------------------------------------------------------

def _make_registry_full() -> HarnessRegistry:
    """Registry đầy đủ → coverage READY (copy pattern test_harness_coverage)."""
    from aios_core.harness.behavioral import BehavioralConformanceHarness
    from aios_core.harness.benchmark import (
        BenchmarkHarness, BenchmarkRunner, RegressionGate,
    )
    from aios_core.harness.doctor import (
        DoctorChecks, DoctorHarness, ReadinessHarness, ReadinessScorer,
    )
    from aios_core.harness.evaluation import EvaluationHarness, Engine
    from aios_core.harness.execution import (
        EvidenceServices, VerificationHarness,
    )
    from aios_core.harness.meta import MetaHarness
    from aios_core.harness.testing import TestHarness

    reg = HarnessRegistry()
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


class TestHarness:
    def test_id_name_version(self):
        h = ReleaseGateHarness(_FakeHarness(), _FakeHarness())
        assert h.id == "release"
        assert h.name == "release-gate"
        assert h.version == "1.0.0"

    def test_run_returns_payload_pass(self):
        # real full registry → coverage READY + meta PASS → PASS
        reg = _make_registry_full()
        from aios_core.harness.coverage import (
            CoverageHarness, HarnessReadinessScorer,
        )
        from aios_core.harness.meta import MetaHarness

        state = StateService()
        cov = CoverageHarness(reg, HarnessReadinessScorer(),
                              state_service=state)
        meta = MetaHarness(state_service=state,
                           registry_ids=sorted(reg.list()))
        h = ReleaseGateHarness(cov, meta, state_service=state)
        ctx = release_ctx("r-pass")
        payload = h.run(ctx)
        assert payload["status"] == "pass"
        assert payload["both_pass"] is True

    def test_run_returns_payload_blocked(self):
        # fake coverage NOT_READY + fake meta PASS → BLOCKED
        h = ReleaseGateHarness(_FakeCoverageHarness(), _FakeMetaHarness())
        ctx = release_ctx("r-blocked")
        payload = h.run(ctx)
        assert payload["status"] == "blocked"
        assert payload["both_pass"] is False
        assert payload["system_readiness"]["status"] == "not_ready"

    def test_verify_strict_raises(self):
        h = ReleaseGateHarness(_FakeCoverageHarness(), _FakeMetaHarness())
        ctx = release_ctx("r-fail", strict=True)
        h.run(ctx)
        with pytest.raises(ReleaseGateError):
            h.verify(ctx, None)

    def test_verify_not_strict_no_raise(self):
        h = ReleaseGateHarness(_FakeCoverageHarness(), _FakeMetaHarness())
        ctx = release_ctx("r-warn", strict=False)
        h.run(ctx)
        h.verify(ctx, None)  # BLOCKED nhưng not-strict → không raise

    def test_verify_strict_pass_no_raise(self):
        # real full registry → PASS → strict không raise
        reg = _make_registry_full()
        from aios_core.harness.coverage import (
            CoverageHarness, HarnessReadinessScorer,
        )
        from aios_core.harness.meta import MetaHarness

        state = StateService()
        cov = CoverageHarness(reg, HarnessReadinessScorer(),
                              state_service=state)
        meta = MetaHarness(state_service=state,
                           registry_ids=sorted(reg.list()))
        h = ReleaseGateHarness(cov, meta, state_service=state)
        ctx = release_ctx("r-pass-verify", strict=True)
        h.run(ctx)
        h.verify(ctx, None)  # PASS → không raise

    def test_get_report_round_trip(self):
        state = StateService()
        h = ReleaseGateHarness(_FakeCoverageHarness(), _FakeMetaHarness(),
                               state_service=state)
        ctx = release_ctx("r-g", strict=False)
        h.run(ctx)
        h.verify(ctx, None)
        report = h.get_report("r-g")
        assert report["status"] == "blocked"
        assert report["both_pass"] is False

    def test_full_runner_execute_diagnosed(self):
        h = ReleaseGateHarness(_FakeCoverageHarness(), _FakeMetaHarness())
        state = StateService()
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "release", config={"strict": True})
        report = runner.execute(h, ctx)
        # BLOCKED + strict → DIAGNOSED (verify raise → diagnose_on_failure)
        assert report.result.status in (
            HarnessRunStatus.DIAGNOSED, HarnessRunStatus.FAILED)

    def test_full_runner_execute_completed_pass(self):
        # real full registry → PASS → COMPLETED (verify không raise)
        reg = _make_registry_full()
        from aios_core.harness.coverage import (
            CoverageHarness, HarnessReadinessScorer,
        )
        from aios_core.harness.meta import MetaHarness

        state = StateService()
        cov = CoverageHarness(reg, HarnessReadinessScorer(),
                              state_service=state)
        meta = MetaHarness(state_service=state,
                           registry_ids=sorted(reg.list()))
        h = ReleaseGateHarness(cov, meta, state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "release", config={"strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


class _FakeHarness:
    """Harness giả cho test id/name/version (không chạy thật)."""
    id = "fake"
    name = "fake"
    version = "0.0.0"

    def run(self, ctx):
        return {}

    def verify(self, ctx, payload):
        ...

    def complete(self, ctx, payload):
        ...


class _FakeCoverageHarness:
    """Fake coverage harness → trả readiness NOT_READY (test BLOCKED path)."""
    id = "fake-cov"
    name = "fake-cov"
    version = "0.0.0"

    def run(self, ctx):
        return {"coverage": {}, "readiness": _not_ready().model_dump(mode="json")}

    def verify(self, ctx, payload):
        ...

    def complete(self, ctx, payload):
        ...


class _FakeMetaHarness:
    """Fake meta harness → trả MetaReport PASS nhưng coverage NOT_READY → BLOCKED."""
    id = "fake-meta"
    name = "fake-meta"
    version = "0.0.0"

    def run(self, ctx):
        return _meta(MetaStatus.PASS).model_dump(mode="json")

    def verify(self, ctx, payload):
        ...

    def complete(self, ctx, payload):
        ...


# ---------------------------------------------------------------------------
# AC7 — Wiring (runtime registry)
# ---------------------------------------------------------------------------

class TestWiring:
    def test_registry_has_release(self):
        from aios_core.kernel import RuntimeKernel

        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("release") is not None
        assert reg.get("release").id == "release"
        # runtime có 12 harness (11 + heal)
        assert len(reg.list()) == 14
        assert "release" in reg.list()


# ---------------------------------------------------------------------------
# AC9 — CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def _run_cli(self, argv):
        from aios_core.workflow.cli import main

        return main(argv)

    def test_cli_exit_code(self, capsys):
        # runtime registry đầy đủ → coverage READY + meta PASS → PASS → exit 0
        rc = self._run_cli(["harness", "release"])
        out = capsys.readouterr().out
        msg = json.loads(out)
        assert "release" in msg
        assert msg["release"]["status"] == "pass"
        assert rc == 0
