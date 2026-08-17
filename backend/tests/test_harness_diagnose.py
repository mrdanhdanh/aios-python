"""TASK-094 — Diagnose tests (M14-P0): failure corpus + signature + localization."""

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
from aios_core.harness.diagnose import (
    DiagnoseEngine,
    DiagnoseError,
    DiagnoseHarness,
    FailureCorpusReport,
    FailureRecord,
    FailureSeverity,
)
from aios_core.kernel.services import StateService


def diagnose_ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="diagnose", target="diag",
                          started_at=utcnow(), config=config)


def _make_failed_report(run_id="r1", harness_id="meta", summary=None):
    """Tạo HarnessReport FAILED để test analyze."""
    from aios_core.harness.contracts import HarnessReport, HarnessResult

    return HarnessReport(
        run_id=run_id,
        summary=summary or f"{harness_id}:{run_id} -> FAILED: some error",
        result=HarnessResult(
            run_id=run_id,
            status=HarnessRunStatus.FAILED,
            summary=summary or f"{harness_id}:{run_id} -> FAILED: some error",
            metrics={"duration_ms": 100, "phase_count": 3},
        ),
        generated_at=utcnow(),
    )


def _make_completed_report(run_id="r1", harness_id="meta"):
    from aios_core.harness.contracts import HarnessReport, HarnessResult

    return HarnessReport(
        run_id=run_id,
        summary=f"{harness_id}:{run_id} -> COMPLETED",
        result=HarnessResult(
            run_id=run_id,
            status=HarnessRunStatus.COMPLETED,
            summary=f"{harness_id}:{run_id} -> COMPLETED",
        ),
        generated_at=utcnow(),
    )


# ---------------------------------------------------------------------------
# AC1 — FailureRecord shape
# ---------------------------------------------------------------------------

class TestContracts:
    def test_record_shape(self):
        from datetime import datetime, timezone

        r = FailureRecord(
            run_id="r1", harness_id="meta", status="failed",
            error_type="MetaError", error_message="meta failed",
            component="harness/meta", signature="abc123",
            severity=FailureSeverity.HIGH, evidence={},
            timestamp=datetime.now(timezone.utc),
        )
        dump = r.model_dump()
        assert set(dump) == {
            "run_id", "harness_id", "status", "error_type", "error_message",
            "component", "signature", "severity", "evidence", "timestamp"}

    def test_record_extra_forbid(self):
        from datetime import datetime, timezone

        with pytest.raises(ValidationError):
            FailureRecord(
                run_id="r1", harness_id="meta", status="failed",
                error_type="MetaError", error_message="",
                component="harness/meta", signature="abc",
                severity=FailureSeverity.LOW, evidence={},
                timestamp=datetime.now(timezone.utc), nope=1)

    def test_severity_enum(self):
        assert {s.value for s in FailureSeverity} == {
            "low", "medium", "high", "critical"}


# ---------------------------------------------------------------------------
# AC2 — Signature deterministic
# ---------------------------------------------------------------------------

class TestSignature:
    def test_deterministic(self):
        engine = DiagnoseEngine()
        s1 = engine.compute_signature("MetaError", "harness/meta", "fail")
        s2 = engine.compute_signature("MetaError", "harness/meta", "fail")
        assert s1 == s2
        assert len(s1) == 16  # sha256[:16]

    def test_different_inputs_different_signatures(self):
        engine = DiagnoseEngine()
        s1 = engine.compute_signature("MetaError", "harness/meta", "fail")
        s2 = engine.compute_signature("MetaError", "harness/meta", "timeout")
        assert s1 != s2


# ---------------------------------------------------------------------------
# AC3 — normalize_message
# ---------------------------------------------------------------------------

class TestNormalize:
    def test_strips_timestamps(self):
        engine = DiagnoseEngine()
        msg = "Error at 2026-08-18T12:34:56.789+00:00 in module"
        result = engine.normalize_message(msg)
        assert "2026-08-18" not in result
        assert "<TIMESTAMP>" in result

    def test_strips_uuids(self):
        engine = DiagnoseEngine()
        msg = "Failed id=550e8400-e29b-41d4-a716-446655440000"
        result = engine.normalize_message(msg)
        assert "550e8400" not in result
        assert "<UUID>" in result

    def test_strips_windows_paths(self):
        engine = DiagnoseEngine()
        msg = "File not found: C:\\Users\\test\\file.py"
        result = engine.normalize_message(msg)
        assert "C:\\Users" not in result
        assert "<PATH>" in result

    def test_strips_unix_paths(self):
        engine = DiagnoseEngine()
        msg = "Module not found: /home/user/src/module.py"
        result = engine.normalize_message(msg)
        assert "/home/user" not in result
        assert "<PATH>" in result

    def test_strips_hex(self):
        engine = DiagnoseEngine()
        msg = "Address 0x7fff5fbff8d0 invalid"
        result = engine.normalize_message(msg)
        assert "0x7fff" not in result

    def test_collapse_spaces(self):
        engine = DiagnoseEngine()
        msg = "too   many    spaces"
        result = engine.normalize_message(msg)
        assert result == "too many spaces"


# ---------------------------------------------------------------------------
# AC4 — analyze() from FAILED report
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_analyze_failed(self):
        engine = DiagnoseEngine()
        report = _make_failed_report()
        record = engine.analyze(report)
        assert record is not None
        assert record.run_id == "r1"
        assert record.status == "failed"
        assert record.signature != ""
        assert record.severity in FailureSeverity

    def test_analyze_returns_none_for_completed(self):  # AC5
        engine = DiagnoseEngine()
        report = _make_completed_report()
        record = engine.analyze(report)
        assert record is None

    def test_analyze_diagnosed_status(self):
        from aios_core.harness.contracts import HarnessReport, HarnessResult

        engine = DiagnoseEngine()
        report = HarnessReport(
            run_id="r1",
            summary="meta:r1 -> DIAGNOSED: meta error",
            result=HarnessResult(
                run_id="r1",
                status=HarnessRunStatus.DIAGNOSED,
                summary="meta:r1 -> DIAGNOSED: meta error",
            ),
            generated_at=utcnow(),
        )
        record = engine.analyze(report)
        assert record is not None
        assert record.status == "diagnosed"


# ---------------------------------------------------------------------------
# AC6 — Severity mapping
# ---------------------------------------------------------------------------

class TestSeverity:
    def test_hook_error_is_high(self):
        engine = DiagnoseEngine()
        report = _make_failed_report(summary="meta:r1 -> FAILED: HarnessHookError: hook failed")
        record = engine.analyze(report)
        assert record.severity == FailureSeverity.HIGH

    def test_lifecycle_error_is_medium(self):
        engine = DiagnoseEngine()
        report = _make_failed_report(summary="meta:r1 -> FAILED: HarnessLifecycleError: bad transition")
        record = engine.analyze(report)
        assert record.severity == FailureSeverity.MEDIUM

    def test_unknown_error_is_low(self):
        engine = DiagnoseEngine()
        report = _make_failed_report(summary="meta:r1 -> FAILED: SomethingWeird: oops")
        record = engine.analyze(report)
        assert record.severity == FailureSeverity.LOW


# ---------------------------------------------------------------------------
# AC7 — Component localization
# ---------------------------------------------------------------------------

class TestLocalization:
    def test_localize_from_summary(self):
        engine = DiagnoseEngine()
        report = _make_failed_report(harness_id="meta")
        record = engine.analyze(report)
        assert record.component == "harness/meta"

    def test_localize_unknown_fallback(self):
        engine = DiagnoseEngine()
        report = _make_failed_report(summary="some weird summary without colon")
        record = engine.analyze(report)
        # Falls back to "unknown" or extracts from message
        assert record.component is not None


# ---------------------------------------------------------------------------
# AC8 — FailureCorpusReport
# ---------------------------------------------------------------------------

class TestCorpusReport:
    def test_empty_corpus(self):
        from aios_core.harness.diagnose.engine import build_corpus_report
        report = build_corpus_report([])
        assert report.total == 0
        assert report.unique_signatures == 0
        assert report.recent == []

    def test_corpus_with_records(self):
        from aios_core.harness.diagnose.engine import build_corpus_report
        from datetime import datetime, timezone

        records = [
            FailureRecord(
                run_id="r1", harness_id="meta", status="failed",
                error_type="MetaError", error_message="fail",
                component="harness/meta", signature="sig1",
                severity=FailureSeverity.HIGH, evidence={},
                timestamp=datetime.now(timezone.utc)),
            FailureRecord(
                run_id="r2", harness_id="coverage", status="failed",
                error_type="CoverageError", error_message="coverage",
                component="harness/coverage", signature="sig2",
                severity=FailureSeverity.MEDIUM, evidence={},
                timestamp=datetime.now(timezone.utc)),
        ]
        report = build_corpus_report(records)
        assert report.total == 2
        assert report.by_harness == {"meta": 1, "coverage": 1}
        assert report.by_severity == {"high": 1, "medium": 1}
        assert report.unique_signatures == 2

    def test_dedup_by_signature(self):
        from aios_core.harness.diagnose.engine import build_corpus_report
        from datetime import datetime, timezone

        records = [
            FailureRecord(
                run_id="r1", harness_id="meta", status="failed",
                error_type="MetaError", error_message="fail",
                component="harness/meta", signature="same_sig",
                severity=FailureSeverity.HIGH, evidence={},
                timestamp=datetime.now(timezone.utc)),
            FailureRecord(
                run_id="r2", harness_id="meta", status="failed",
                error_type="MetaError", error_message="fail",
                component="harness/meta", signature="same_sig",
                severity=FailureSeverity.HIGH, evidence={},
                timestamp=datetime.now(timezone.utc)),
        ]
        report = build_corpus_report(records)
        assert report.unique_signatures == 1  # deduped


# ---------------------------------------------------------------------------
# AC9 — Harness lifecycle
# ---------------------------------------------------------------------------

class TestHarness:
    def test_id_name_version(self):
        h = DiagnoseHarness()
        assert h.id == "diagnose"
        assert h.version == "1.0.0"

    def test_run_empty_corpus(self):
        h = DiagnoseHarness()
        ctx = diagnose_ctx("r-empty")
        payload = h.run(ctx)
        assert payload["total"] == 0

    def test_add_from_report(self):
        h = DiagnoseHarness()
        report = _make_failed_report()
        record = h.add_from_report(report)
        assert record is not None
        assert len(h.get_corpus()) == 1

    def test_add_deduplicates(self):
        h = DiagnoseHarness()
        r1 = _make_failed_report(run_id="r1")
        r2 = _make_failed_report(run_id="r2")
        h.add_from_report(r1)
        h.add_from_report(r2)  # same error → same signature → dedup
        assert len(h.get_corpus()) == 1

    def test_add_completed_returns_none(self):
        h = DiagnoseHarness()
        report = _make_completed_report()
        record = h.add_from_report(report)
        assert record is None
        assert len(h.get_corpus()) == 0

    def test_persist_round_trip(self):
        state = StateService()
        h = DiagnoseHarness(state_service=state)
        report = _make_failed_report()
        h.add_from_report(report)
        ctx = diagnose_ctx("r-persist")
        h.run(ctx)
        h.verify(ctx, None)
        data = h.get_report("r-persist")
        assert data is not None
        assert data["total"] == 1

    def test_full_runner_execute(self):
        state = StateService()
        h = DiagnoseHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "diagnose", config={"strict": False})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


# ---------------------------------------------------------------------------
# AC10 — CLI
# ---------------------------------------------------------------------------

class TestCLI:
    def _run_cli(self, argv):
        from aios_core.workflow.cli import main
        return main(argv)

    def test_cli_exit_0(self, capsys):
        rc = self._run_cli(["harness", "diagnose"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "diagnose" in data
        assert data["total"] == 0
        assert rc == 0


# ---------------------------------------------------------------------------
# AC11 — Wiring
# ---------------------------------------------------------------------------

class TestWiring:
    def test_registry_has_diagnose(self):
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("diagnose") is not None
        assert reg.get("diagnose").id == "diagnose"
        assert len(reg.list()) == 15


# ---------------------------------------------------------------------------
# AC12 — Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_analyze_twice_identical(self):
        engine = DiagnoseEngine()
        report = _make_failed_report()
        r1 = engine.analyze(report)
        r2 = engine.analyze(report)
        assert r1.signature == r2.signature
        assert r1.error_type == r2.error_type
        assert r1.component == r2.component
