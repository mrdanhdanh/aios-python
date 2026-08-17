"""TASK-097 — Certify tests (M14-P3): apply + rollback + certified baseline."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from aios_core.config import Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.certify import (
    CertifiedBaseline, CertifyEngine, CertifyError, CertifyReport,
    RemediationRecord, RemediationStatus, CertifyHarness,
)
from aios_core.harness.heal.contracts import CandidateFix, RiskLevel
from aios_core.kernel.services import StateService


def _candidate(risk=RiskLevel.LOW, sig="sig1"):
    return CandidateFix(failure_signature=sig, description="test fix",
                        risk_level=risk, confidence=0.5,
                        suggested_action="retry", evidence={})

def _ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="certify", target="cert",
                          started_at=utcnow(), config=config)


class TestContracts:
    def test_status_enum(self):
        assert {s.value for s in RemediationStatus} == {
            "pending", "applied", "rolled_back", "certified", "failed"}

    def test_baseline_shape(self):
        b = CertifiedBaseline(
            before_version="1.1.0", candidate_version="1.1.0-fix",
            certification_id="abc", rollback_point="rb:1.1.0",
            timestamp=datetime.now(timezone.utc))
        assert b.model_dump()


class TestEngine:
    def test_apply_low_risk(self):
        record = CertifyEngine().apply(_candidate(RiskLevel.LOW))
        assert record.status == RemediationStatus.APPLIED
        assert record.baseline is not None

    def test_apply_high_risk_fails(self):
        record = CertifyEngine().apply(_candidate(RiskLevel.HIGH))
        assert record.status == RemediationStatus.FAILED
        assert record.baseline is None

    def test_rollback(self):
        engine = CertifyEngine()
        record = engine.apply(_candidate())
        rolled = engine.rollback(record)
        assert rolled.status == RemediationStatus.ROLLED_BACK

    def test_certify(self):
        engine = CertifyEngine()
        record = engine.apply(_candidate())
        cert = engine.certify(record)
        assert cert.status == RemediationStatus.CERTIFIED
        assert cert.baseline.after_version is not None

    def test_rollback_non_applied_noop(self):
        record = RemediationRecord(
            failure_signature="x", candidate_description="d",
            risk_level="low", status=RemediationStatus.FAILED,
            detail="fail", timestamp=datetime.now(timezone.utc))
        rolled = CertifyEngine().rollback(record)
        assert rolled.status == RemediationStatus.FAILED

    def test_build_report(self):
        records = [CertifyEngine().apply(_candidate(sig=f"s{i}")) for i in range(3)]
        report = CertifyEngine().build_report(records)
        assert report.total == 3
        assert report.applied == 3

    def test_determinism(self):
        c = _candidate()
        r1 = CertifyEngine().apply(c).model_dump()
        r2 = CertifyEngine().apply(c).model_dump()
        # signatures differ (timestamp-based cert_id) but status same
        assert r1["status"] == r2["status"]


class TestHarness:
    def test_id_version(self):
        h = CertifyHarness()
        assert h.id == "certify"
        assert h.version == "1.0.0"

    def test_apply_candidate(self):
        h = CertifyHarness()
        record = h.apply_candidate(_candidate())
        assert record.status == RemediationStatus.APPLIED
        assert len(h.get_records()) == 1

    def test_certify_record(self):
        h = CertifyHarness()
        record = h.apply_candidate(_candidate())
        cert = h.certify_record(record)
        assert cert.status == RemediationStatus.CERTIFIED

    def test_rollback_record(self):
        h = CertifyHarness()
        record = h.apply_candidate(_candidate())
        rolled = h.rollback_record(record)
        assert rolled.status == RemediationStatus.ROLLED_BACK

    def test_full_runner(self):
        state = StateService()
        h = CertifyHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "certify", config={"strict": False})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


class TestWiring:
    def test_registry_has_certify(self):
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("certify") is not None
        assert len(reg.list()) == 14


class TestCLI:
    def test_cli_exit_0(self, capsys):
        from aios_core.workflow.cli import main
        rc = main(["harness", "certify"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "certify" in data
        assert rc == 0
