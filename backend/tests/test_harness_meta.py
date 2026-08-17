"""TASK-091 — Meta-Harness tests (M13-P2): verify the verifier.

8 adversarial cases + fail-closed + wiring + CLI. Chống circular (AC16).
"""

from __future__ import annotations

import importlib

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
from aios_core.harness.meta import (
    MetaCase,
    MetaError,
    MetaHarness,
    MetaHarnessEngine,
    MetaOracle,
    MetaReport,
    MetaStatus,
)
from aios_core.harness.execution.pipeline import compute_verdict
from aios_core.kernel.services import StateService


def meta_ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="meta", target="meta",
                          started_at=utcnow(), config=config)


# ---------------------------------------------------------------------------
# Contracts (AC1, AC10)
# ---------------------------------------------------------------------------

class TestContracts:
    def test_case_enum_8(self):
        assert {c.value for c in MetaCase} == {
            "false_positive", "false_negative", "malformed_evidence",
            "broken_verifier", "corrupted_artifact", "replay_mismatch",
            "skipped_verification", "verify_skipped"}

    def test_oracle_enum(self):
        assert {o.value for o in MetaOracle} == {
            "not_pass", "fail", "inconclusive", "tamper", "corrupt"}

    def test_case_result_extra_forbid(self):
        with pytest.raises(ValidationError):
            MetaHarnessEngine  # touch
            from aios_core.harness.meta import MetaCaseResult
            MetaCaseResult(case=MetaCase.FALSE_POSITIVE,
                           verifier_state="x", expected_state=MetaOracle.NOT_PASS,
                           fail_closed=True, detail="", nope=1)

    def test_report_extra_forbid(self):
        with pytest.raises(ValidationError):
            MetaReport(cases=[], all_fail_closed=True, status=MetaStatus.PASS,
                      metrics={}, summary="", reproducible={}, nope=1)

    def test_report_no_timestamp(self):
        rep = MetaHarnessEngine().run()
        dump = rep.model_dump()
        assert "generated_at" not in dump
        assert "timestamp" not in dump


# ---------------------------------------------------------------------------
# Engine 8 cases (AC2-AC9)
# ---------------------------------------------------------------------------

class TestEngine:
    def test_all_8_fail_closed(self):
        rep = MetaHarnessEngine().run()
        assert len(rep.cases) == 8
        assert rep.all_fail_closed is True
        assert rep.status == MetaStatus.PASS

    def test_false_positive(self):  # AC2
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.FALSE_POSITIVE)
        assert c.verifier_state == "inconclusive"
        assert c.fail_closed is True

    def test_false_negative(self):  # AC3
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.FALSE_NEGATIVE)
        assert c.verifier_state == "fail"
        assert c.fail_closed is True

    def test_malformed_evidence(self):  # AC4
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.MALFORMED_EVIDENCE)
        assert c.verifier_state == "inconclusive"
        assert c.fail_closed is True

    def test_broken_verifier_detected(self):  # AC5 (scenario a)
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.BROKEN_VERIFIER)
        assert c.verifier_state == "pass"
        assert c.fail_closed is True  # Meta phát hiện verifier hỏng

    def test_corrupted_artifact(self):  # AC6
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.CORRUPTED_ARTIFACT)
        assert c.fail_closed is True

    def test_replay_mismatch(self):  # AC7
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.REPLAY_MISMATCH)
        assert "TAMPER" in c.verifier_state
        assert c.fail_closed is True

    def test_skipped_verification(self):  # AC8 (INV-035)
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.SKIPPED_VERIFICATION)
        assert c.verifier_state == "inconclusive"
        assert c.fail_closed is True

    def test_verify_skipped_detected(self):  # AC9 (integration, scenario a)
        rep = MetaHarnessEngine(state_service=StateService()).run()
        c = next(c for c in rep.cases if c.case == MetaCase.VERIFY_SKIPPED)
        assert c.verifier_state == "completed"
        assert c.fail_closed is True

    def test_metrics_keys(self):  # P3-3
        rep = MetaHarnessEngine().run()
        assert rep.metrics["total"] == 8
        assert rep.metrics["fail_closed"] == 8
        assert set(rep.metrics["by_case"]) == {c.value for c in MetaCase}

    def test_reproducible_no_timestamp(self):  # P3-2
        rep = MetaHarnessEngine(registry_ids=["meta", "coverage"]).run()
        assert rep.reproducible["registry_harness_ids"] == ["coverage", "meta"]
        assert "aios_version" in rep.reproducible


# ---------------------------------------------------------------------------
# Chống circular (AC16) — scenario (b): verifier dưới test KHÔNG fail-closed
# ---------------------------------------------------------------------------

class TestIndependentOracle:
    def test_monkeypatch_detects_broken_real_verifier(self, monkeypatch):
        # P3-4: monkeypatch MODULE-LEVEL compute_verdict → luôn PASS trên
        # evidence thiếu → case 1 (false_positive) không còn fail_closed
        from aios_core.harness.execution import pipeline

        def fake_compute(check_results, has_critical, truncated=False):
            from aios_core.harness.execution.contracts import Verdict
            return Verdict.PASS

        monkeypatch.setattr(pipeline, "compute_verdict", fake_compute)
        rep = MetaHarnessEngine().run()
        c = next(c for c in rep.cases if c.case == MetaCase.FALSE_POSITIVE)
        assert c.fail_closed is False  # Meta phát hiện
        assert rep.status == MetaStatus.FAIL  # scenario (b) → Meta FAIL

    def test_engine_uses_module_level_import(self):
        # đảm bảo engine reference pipeline.compute_verdict ở module level
        # (AC16 khả thi: monkeypatch module-level compute_verdict)
        mod = importlib.import_module("aios_core.harness.meta.engine")
        assert hasattr(mod, "pipeline")
        assert hasattr(mod.pipeline, "compute_verdict")


# ---------------------------------------------------------------------------
# Harness wiring (AC11, AC12)
# ---------------------------------------------------------------------------

class TestHarness:
    def test_id_name_version(self):
        h = MetaHarness()
        assert h.id == "meta"
        assert h.name == "meta-harness"
        assert h.version == "1.0.0"

    def test_register_in_registry(self):
        reg = HarnessRegistry()
        h = MetaHarness()
        reg.register(h)
        assert reg.get("meta") is h

    def test_run_returns_payload(self):
        h = MetaHarness()
        ctx = meta_ctx("r")
        payload = h.run(ctx)
        assert payload["status"] == "pass"
        assert len(payload["cases"]) == 8

    def test_verify_strict_raises(self):  # AC12
        state = StateService()
        h = MetaHarness(state_service=state)
        ctx = meta_ctx("r-fail", strict=True)
        h.run(ctx)
        # status PASS → không raise
        h.verify(ctx, None)
        assert state.get_state("r-fail")["meta"]["status"] == "pass"

    def test_full_runner_execute_completed(self):  # AC11
        state = StateService()
        h = MetaHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "meta", config={"strict": True})
        report = runner.execute(h, ctx)
        assert report.result.status in (
            HarnessRunStatus.COMPLETED, HarnessRunStatus.DIAGNOSED)

    def test_get_report_round_trip(self):  # AC11
        state = StateService()
        h = MetaHarness(state_service=state)
        ctx = meta_ctx("r-g", strict=False)
        h.run(ctx)
        h.verify(ctx, None)
        report = h.get_report("r-g")
        assert report["status"] == "pass"
        assert report["all_fail_closed"] is True


# ---------------------------------------------------------------------------
# Wiring (AC11)
# ---------------------------------------------------------------------------

class TestWiring:
    def test_registry_has_meta(self):  # AC11
        from aios_core.kernel import RuntimeKernel

        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("meta") is not None
        assert reg.get("meta").id == "meta"
        assert "meta" in reg.list()


# ---------------------------------------------------------------------------
# CLI (AC13)
# ---------------------------------------------------------------------------

class TestCLI:
    def _run_cli(self, argv):
        from aios_core.workflow.cli import main

        return main(argv)

    def test_cli_pass_exit_0(self, capsys):  # AC13
        rc = self._run_cli(["harness", "meta"])
        out = capsys.readouterr().out
        assert rc == 0
        data = __import__("json").loads(out)
        assert data["meta"]["status"] == "pass"

    def test_cli_no_strict(self, capsys):  # AC13
        rc = self._run_cli(["harness", "meta", "--no-strict"])
        out = capsys.readouterr().out
        assert rc == 0
