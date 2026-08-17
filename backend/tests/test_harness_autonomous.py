"""TASK-099 — Autonomous tests (M15): loop + trust budget + improvement."""

from __future__ import annotations

import json

import pytest

from aios_core.config import Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.autonomous import (
    AutonomyLevel, AutonomousEngine, AutonomousHarness, LoopAction,
    LoopState, TrustBudget,
)
from aios_core.harness.contracts import utcnow
from aios_core.harness.diagnose.contracts import FailureRecord, FailureSeverity
from aios_core.harness.heal.contracts import CandidateReport
from aios_core.kernel.services import StateService
from datetime import datetime, timezone


def _ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="autonomous", target="auto",
                          started_at=utcnow(), config=config)


def _failure(sig="sig1"):
    return FailureRecord(
        run_id="r1", harness_id="meta", status="failed",
        error_type="MetaError", error_message="fail",
        component="harness/meta", signature=sig,
        severity=FailureSeverity.HIGH, evidence={},
        timestamp=datetime.now(timezone.utc))


def _state(budget=None):
    return LoopState(iteration=0, action=LoopAction.CONTINUE,
                     autonomy_level=AutonomyLevel.SUPERVISED,
                     budget=budget or TrustBudget(), detail="test")


class TestContracts:
    def test_loop_action_enum(self):
        assert {a.value for a in LoopAction} == {
            "continue", "pause", "stop", "ask_human", "replan", "rollback"}

    def test_autonomy_level_enum(self):
        assert {l.value for l in AutonomyLevel} == {
            "supervised", "assisted", "autonomous"}

    def test_trust_budget_exceeded(self):
        b = TrustBudget(max_auto_repairs=2, current_repairs=2)
        assert b.exceeded is True

    def test_trust_budget_not_exceeded(self):
        b = TrustBudget(max_auto_repairs=5, current_repairs=1)
        assert b.exceeded is False


class TestEngine:
    def test_stop_when_no_failures(self):
        engine = AutonomousEngine()
        action = engine.decide(_state(), [], CandidateReport(
            candidates=[], total=0, by_risk={}, summary="", reproducible={}), [])
        assert action == LoopAction.STOP

    def test_ask_human_supervised_high_risk(self):
        from aios_core.harness.heal.contracts import CandidateFix, RiskLevel
        candidates = CandidateReport(
            candidates=[CandidateFix(failure_signature="x", description="d",
                                    risk_level=RiskLevel.HIGH, confidence=0.8,
                                    suggested_action="fix_code", evidence={})],
            total=1, by_risk={"high": 1}, summary="", reproducible={})
        engine = AutonomousEngine(autonomy_level=AutonomyLevel.SUPERVISED)
        action = engine.decide(_state(), [_failure()], candidates, [])
        assert action == LoopAction.ASK_HUMAN

    def test_continue_assisted(self):
        engine = AutonomousEngine(autonomy_level=AutonomyLevel.ASSISTED)
        action = engine.decide(_state(), [_failure()], CandidateReport(
            candidates=[], total=0, by_risk={}, summary="", reproducible={}), [])
        assert action == LoopAction.CONTINUE

    def test_stop_budget_exceeded(self):
        budget = TrustBudget(max_auto_repairs=1, current_repairs=1)
        engine = AutonomousEngine()
        action = engine.decide(_state(budget), [_failure()], CandidateReport(
            candidates=[], total=0, by_risk={}, summary="", reproducible={}), [])
        assert action == LoopAction.STOP

    def test_record_repair(self):
        budget = TrustBudget()
        new_budget = AutonomousEngine().record_repair(budget)
        assert new_budget.current_repairs == 1

    def test_record_failure(self):
        budget = TrustBudget()
        new_budget = AutonomousEngine().record_failure(budget)
        assert new_budget.consecutive_failures == 1

    def test_record_success_resets(self):
        budget = TrustBudget(consecutive_failures=3)
        new_budget = AutonomousEngine().record_success(budget)
        assert new_budget.consecutive_failures == 0

    def test_suggest_improvements_repeated(self):
        failures = [_failure(sig="same")] * 3
        engine = AutonomousEngine()
        improvements = engine.suggest_improvements(failures, CandidateReport(
            candidates=[], total=0, by_risk={}, summary="", reproducible={}))
        assert len(improvements) == 1
        assert improvements[0].source == "failure_pattern"

    def test_determinism(self):
        engine = AutonomousEngine()
        s1 = engine.decide(_state(), [_failure()], CandidateReport(
            candidates=[], total=0, by_risk={}, summary="", reproducible={}), [])
        s2 = engine.decide(_state(), [_failure()], CandidateReport(
            candidates=[], total=0, by_risk={}, summary="", reproducible={}), [])
        assert s1 == s2


class TestHarness:
    def test_id_version(self):
        h = AutonomousHarness()
        assert h.id == "autonomous"
        assert h.version == "1.0.0"

    def test_run_empty(self):
        h = AutonomousHarness()
        ctx = _ctx("r1")
        payload = h.run(ctx)
        assert "action" in payload
        assert payload["failures"] == 0

    def test_full_runner(self):
        state = StateService()
        h = AutonomousHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "autonomous", config={"strict": False})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


class TestWiring:
    def test_registry_has_autonomous(self):
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("autonomous") is not None
        assert len(reg.list()) == 16


class TestCLI:
    def test_cli_exit_0(self, capsys):
        from aios_core.workflow.cli import main
        rc = main(["harness", "autonomous"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "autonomous" in data
        assert rc == 0
