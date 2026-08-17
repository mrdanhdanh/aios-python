"""TASK-095 — Heal tests (M14-P1): candidate fixes + risk scoring."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from aios_core.config import Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.diagnose.contracts import FailureRecord, FailureSeverity
from aios_core.harness.heal import (
    CandidateFix, CandidateReport, HealEngine, HealError,
    HealHarness, RiskLevel,
)
from aios_core.kernel.services import StateService


def _make_record(sig="sig1", severity=FailureSeverity.LOW, harness_id="meta",
                 component="harness/meta"):
    return FailureRecord(
        run_id="r1", harness_id=harness_id, status="failed",
        error_type="HarnessError", error_message="test error",
        component=component, signature=sig, severity=severity,
        evidence={}, timestamp=datetime.now(timezone.utc))


# Contracts
class TestContracts:
    def test_risk_level_enum(self):
        assert {r.value for r in RiskLevel} == {"low", "medium", "high", "critical"}

    def test_candidate_fix_shape(self):
        c = CandidateFix(failure_signature="x", description="d",
                         risk_level=RiskLevel.LOW, confidence=0.5,
                         suggested_action="retry", evidence={})
        assert c.model_dump()

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            CandidateFix(failure_signature="x", description="d",
                         risk_level=RiskLevel.LOW, confidence=0.5,
                         suggested_action="retry", evidence={}, nope=1)


# Engine
class TestEngine:
    def test_empty_corpus(self):
        report = HealEngine().generate([])
        assert report.total == 0
        assert report.candidates == []

    def test_single_failure(self):
        records = [_make_record()]
        report = HealEngine().generate(records)
        assert report.total == 1
        assert report.candidates[0].risk_level == RiskLevel.LOW
        assert report.candidates[0].suggested_action == "retry"

    def test_high_severity_high_risk(self):
        records = [_make_record(severity=FailureSeverity.HIGH)]
        report = HealEngine().generate(records)
        assert report.candidates[0].risk_level == RiskLevel.HIGH
        assert report.candidates[0].suggested_action == "fix_code"

    def test_medium_severity(self):
        records = [_make_record(severity=FailureSeverity.MEDIUM)]
        report = HealEngine().generate(records)
        assert report.candidates[0].risk_level == RiskLevel.MEDIUM
        assert report.candidates[0].suggested_action == "fix_config"

    def test_repeated_failures_higher_confidence(self):
        records = [_make_record(sig="same")] * 5
        report = HealEngine().generate(records)
        assert report.total == 1  # deduped
        assert report.candidates[0].confidence > 0.5

    def test_determinism(self):
        records = [_make_record()]
        r1 = HealEngine().generate(records).model_dump()
        r2 = HealEngine().generate(records).model_dump()
        assert r1 == r2

    def test_by_risk(self):
        records = [
            _make_record(sig="s1", severity=FailureSeverity.LOW),
            _make_record(sig="s2", severity=FailureSeverity.HIGH),
        ]
        report = HealEngine().generate(records)
        assert report.by_risk == {"low": 1, "high": 1}


# Harness
class TestHarness:
    def test_id_version(self):
        h = HealHarness()
        assert h.id == "heal"
        assert h.version == "1.0.0"

    def test_run_empty(self):
        h = HealHarness()
        ctx = _ctx("r1")
        payload = h.run(ctx)
        assert payload["total"] == 0

    def test_persist_round_trip(self):
        state = StateService()
        h = HealHarness(state_service=state)
        ctx = _ctx("r2")
        h.run(ctx)
        h.verify(ctx, None)
        assert h.get_report("r2") is not None

    def test_full_runner(self):
        state = StateService()
        h = HealHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "heal", config={"strict": False})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


# Wiring
class TestWiring:
    def test_registry_has_heal(self):
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("heal") is not None
        assert len(reg.list()) == 12


# CLI
class TestCLI:
    def test_cli_exit_0(self, capsys):
        from aios_core.workflow.cli import main
        rc = main(["harness", "heal"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "heal" in data
        assert rc == 0


def _ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="heal", target="heal",
                          started_at=utcnow(), config=config)
