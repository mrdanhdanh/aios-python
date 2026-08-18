"""TASK-096 — Simulate tests (M14-P2): simulation + meta-verify gate."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from aios_core.config import Settings
from aios_core.harness import HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.diagnose.contracts import FailureRecord, FailureSeverity
from aios_core.harness.heal.contracts import CandidateFix, RiskLevel
from aios_core.harness.meta.contracts import MetaReport, MetaStatus
from aios_core.harness.simulate import (
    SimulationEngine, SimulationError, SimulationReport, SimulationResult,
    SimulateHarness,
)
from aios_core.kernel.services import StateService


def _candidate(risk=RiskLevel.LOW, sig="sig1"):
    return CandidateFix(failure_signature=sig, description="test",
                        risk_level=risk, confidence=0.5,
                        suggested_action="retry", evidence={})

def _meta_pass():
    return MetaReport(cases=[], all_fail_closed=True, status=MetaStatus.PASS,
                      metrics={}, summary="pass", reproducible={})

def _meta_fail():
    return MetaReport(cases=[], all_fail_closed=False, status=MetaStatus.FAIL,
                      metrics={}, summary="fail", reproducible={})

def _ctx(run_id, **config):
    from aios_core.harness import HarnessContext
    return HarnessContext(run_id=run_id, harness="simulate", target="sim",
                          started_at=utcnow(), config=config)


class TestContracts:
    def test_result_enum(self):
        assert {r.value for r in SimulationResult} == {
            "pass", "fail", "blocked", "error"}

    def test_report_shape(self):
        r = SimulationReport(candidate_signature="x", result=SimulationResult.PASS,
                             checks_passed=1, checks_total=1,
                             meta_verify_pass=True, detail="ok", reproducible={})
        assert r.model_dump()


class TestEngine:
    def test_low_risk_passes(self):
        sim = SimulationEngine().simulate(_candidate(RiskLevel.LOW), _meta_pass())
        assert sim.result == SimulationResult.PASS
        assert sim.meta_verify_pass is True

    def test_high_risk_blocked(self):
        sim = SimulationEngine().simulate(_candidate(RiskLevel.HIGH))
        assert sim.result == SimulationResult.BLOCKED

    def test_critical_risk_blocked(self):
        sim = SimulationEngine().simulate(_candidate(RiskLevel.CRITICAL))
        assert sim.result == SimulationResult.BLOCKED

    def test_meta_fail_blocks(self):
        sim = SimulationEngine().simulate(_candidate(RiskLevel.LOW), _meta_fail())
        assert sim.result == SimulationResult.FAIL
        assert sim.meta_verify_pass is False

    def test_medium_risk_passes(self):
        sim = SimulationEngine().simulate(_candidate(RiskLevel.MEDIUM), _meta_pass())
        assert sim.result == SimulationResult.PASS

    def test_determinism(self):
        c = _candidate()
        r1 = SimulationEngine().simulate(c, _meta_pass()).model_dump()
        r2 = SimulationEngine().simulate(c, _meta_pass()).model_dump()
        assert r1 == r2


class TestHarness:
    def test_id_version(self):
        h = SimulateHarness()
        assert h.id == "simulate"
        assert h.version == "1.0.0"

    def test_run_empty_heal(self):
        h = SimulateHarness()
        ctx = _ctx("r1")
        payload = h.run(ctx)
        assert payload["total"] == 0
        assert payload["all_pass"] is True

    def test_full_runner(self):
        state = StateService()
        h = SimulateHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "simulate", config={"strict": False})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


class TestWiring:
    def test_registry_has_simulate(self):
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("simulate") is not None
        assert len(reg.list()) == 16


class TestCLI:
    def test_cli_exit_0(self, capsys):
        from aios_core.workflow.cli import main
        rc = main(["harness", "simulate"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "simulate" in data
        assert rc == 0
