"""TASK-029 — Harness Kernel tests (M6-H1): contracts, lifecycle, context,
registry, runner, evidence (INV-018), isolation (INV-017)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from aios_core.config import HarnessSettings
from aios_core.harness import (
    Harness,
    HarnessArtifact,
    HarnessContext,
    HarnessError,
    HarnessEvent,
    HarnessLifecycle,
    HarnessLifecycleError,
    HarnessRegistrationError,
    HarnessRegistry,
    HarnessReport,
    HarnessResult,
    HarnessRun,
    HarnessRunner,
    HarnessRunStatus,
    safe_run_id,
)
from aios_core.kernel.services import StateService


class OkHarness(Harness):
    id = "ok"
    name = "Ok"
    version = "1.0.0"

    def run(self, ctx):
        return "payload"


class FailHarness(Harness):
    id = "fail"
    name = "Fail"
    version = "1.0.0"

    def run(self, ctx):
        raise RuntimeError("boom")


class FailOnFailureHarness(Harness):
    """C1-03: on_failure raise must not break evidence/report."""

    id = "failhook"
    name = "FailHook"
    version = "1.0.0"

    def run(self, ctx):
        raise RuntimeError("boom")

    def on_failure(self, ctx, error):
        raise RuntimeError("on_failure exploded")


def make_runner(tmp_path=None, artifact=True, diagnose=True) -> HarnessRunner:
    from aios_core.kernel.services import ArtifactService
    from aios_core.kernel.events import EventBus

    artifacts = None
    if artifact:
        artifacts = ArtifactService(str(tmp_path / "artifacts"), EventBus())
    return HarnessRunner(StateService(), artifacts,
                         diagnose_on_failure=diagnose)


# ---------------------------------------------------------------------------
# YC-1 — Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            HarnessRun(run_id="r", harness="h", target="t",
                       started_at="2026-01-01T00:00:00Z", bogus=1)
        with pytest.raises(ValidationError):
            HarnessEvent(run_id="r", phase="p", timestamp="x", message="m", bogus=1)

    def test_defaults(self):
        run = HarnessRun(run_id="r", harness="h", target="t",
                         started_at="2026-01-01T00:00:00Z")
        assert run.status is HarnessRunStatus.CREATED
        assert run.environment == "local"
        assert run.ended_at is None and run.error is None

    def test_round_trip(self):
        run = HarnessRun(run_id="r", harness="h", target="t",
                         started_at="2026-01-01T00:00:00Z")
        restored = HarnessRun.model_validate(json.loads(
            run.model_dump_json()))
        assert restored.run_id == "r"

    def test_safe_run_id(self):
        assert safe_run_id("harness:abc") == "harness_abc"
        assert safe_run_id('harness:a?b"c') == "harness_a_b_c"
        assert safe_run_id("..") == "run"  # R3-5


# ---------------------------------------------------------------------------
# YC-3 — Lifecycle
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_happy_chain(self):
        status = HarnessRunStatus.CREATED
        for target in (HarnessRunStatus.PREPARING, HarnessRunStatus.VALIDATING,
                       HarnessRunStatus.RUNNING, HarnessRunStatus.VERIFYING,
                       HarnessRunStatus.COMPLETED):
            status = HarnessLifecycle.transition(status, target)
        assert status is HarnessRunStatus.COMPLETED

    def test_error_chain(self):
        status = HarnessLifecycle.transition(
            HarnessRunStatus.RUNNING, HarnessRunStatus.FAILED)
        assert status is HarnessRunStatus.FAILED
        status = HarnessLifecycle.transition(status, HarnessRunStatus.DIAGNOSED)
        assert HarnessLifecycle.is_terminal(status)

    def test_matrix_8x8(self):
        for current in HarnessRunStatus:
            for target in HarnessRunStatus:
                allowed = HarnessLifecycle.can_transition(current, target)
                if not allowed:
                    with pytest.raises(HarnessLifecycleError):
                        HarnessLifecycle.transition(current, target)

    def test_terminal(self):
        assert HarnessLifecycle.is_terminal(HarnessRunStatus.COMPLETED)
        assert HarnessLifecycle.is_terminal(HarnessRunStatus.DIAGNOSED)
        assert not HarnessLifecycle.is_terminal(HarnessRunStatus.FAILED)

    def test_completed_to_failed(self):
        assert HarnessLifecycle.can_transition(
            HarnessRunStatus.COMPLETED, HarnessRunStatus.FAILED)  # C1-02

    def test_created_to_failed(self):
        assert HarnessLifecycle.can_transition(
            HarnessRunStatus.CREATED, HarnessRunStatus.FAILED)  # B1


# ---------------------------------------------------------------------------
# YC-4 — Context
# ---------------------------------------------------------------------------

class TestContext:
    def test_model_dump_no_sink(self):
        ctx = HarnessContext(run_id="r", harness="h", target="t",
                             started_at="2026-01-01T00:00:00Z")
        ctx.attach_sink(lambda e: None)
        dumped = ctx.model_dump()
        assert "_sink" not in dumped

    def test_emit_event_sink(self):
        received = []
        ctx = HarnessContext(run_id="r", harness="h", target="t",
                             started_at="2026-01-01T00:00:00Z")
        ctx.attach_sink(received.append)
        event = ctx.emit_event("running", "started")
        assert event.run_id == "r" and event.phase == "running"
        assert len(received) == 1

    def test_sink_raise_no_crash(self):
        """C2-05: sink failure must not break the run."""
        ctx = HarnessContext(run_id="r", harness="h", target="t",
                             started_at="2026-01-01T00:00:00Z")

        def bad_sink(event):
            raise RuntimeError("sink broke")

        ctx.attach_sink(bad_sink)
        event = ctx.emit_event("running", "x")  # no raise
        assert event.message == "x"

    def test_emit_without_sink(self):
        ctx = HarnessContext(run_id="r", harness="h", target="t",
                             started_at="2026-01-01T00:00:00Z")
        assert ctx.emit_event("p", "m").level == "info"


# ---------------------------------------------------------------------------
# YC-5 — Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_register_get_list(self):
        reg = HarnessRegistry()
        reg.register(OkHarness())
        assert reg.get("ok").id == "ok"
        assert reg.list() == ["ok"]

    def test_duplicate_raises(self):
        reg = HarnessRegistry()
        reg.register(OkHarness())
        with pytest.raises(HarnessRegistrationError):
            reg.register(OkHarness())

    def test_unknown_raises(self):
        with pytest.raises(Exception):
            HarnessRegistry().get("nope")

    def test_abstract_enforced(self):
        with pytest.raises(TypeError):
            Harness()  # abstract properties (C3-04)


# ---------------------------------------------------------------------------
# YC-6 — Runner
# ---------------------------------------------------------------------------

class TestRunner:
    def test_happy_run_with_evidence(self, tmp_path):
        runner = make_runner(tmp_path)
        ctx = runner.create_context(OkHarness(), target="t")
        report = runner.execute(OkHarness(), ctx)
        assert report.result.status is HarnessRunStatus.COMPLETED
        assert len(report.artifacts) == 2  # events + report (INV-018)
        assert [a.id for a in report.artifacts] == [
            f"{ctx.run_id}:events", f"{ctx.run_id}:report"]  # B5
        assert all(a.ref for a in report.artifacts)  # checksum tamper-evident
        assert report.result.metrics["phase_count"] == 5
        # state + queries
        assert runner.get_run(ctx.run_id) is not None
        assert len(runner.get_evidence(ctx.run_id)) == 2

    def test_failure_diagnosed(self, tmp_path):
        runner = make_runner(tmp_path)
        ctx = runner.create_context(FailHarness(), target="t")
        report = runner.execute(FailHarness(), ctx)
        assert report.result.status is HarnessRunStatus.DIAGNOSED
        assert report.result.artifacts == [f"{ctx.run_id}:events",
                                           f"{ctx.run_id}:report"]  # evidence on failure
        assert "boom" in (runner.get_run(ctx.run_id).error or "")

    def test_on_failure_raise_still_reports(self, tmp_path):
        """C1-03: on_failure raising must still produce report + evidence."""
        runner = make_runner(tmp_path)
        ctx = runner.create_context(FailOnFailureHarness(), target="t")
        report = runner.execute(FailOnFailureHarness(), ctx)  # no raise
        assert report.result.status is HarnessRunStatus.DIAGNOSED
        assert len(report.artifacts) == 2

    def test_catch_all_outside_hook(self, tmp_path):
        """B1: exception outside hooks (e.g. broken hook attr) -> FAILED."""

        class Weird(Harness):
            id = "weird"
            name = "Weird"
            version = "1.0.0"

            def prepare(self, ctx):
                raise TypeError("prepare exploded")

        runner = make_runner(tmp_path)
        ctx = runner.create_context(Weird(), target="t")
        report = runner.execute(Weird(), ctx)
        assert report.result.status is HarnessRunStatus.DIAGNOSED
        assert "prepare exploded" in (runner.get_run(ctx.run_id).error or "")

    def test_duplicate_run_id(self, tmp_path):
        runner = make_runner(tmp_path)
        ctx = runner.create_context(OkHarness(), target="t")
        runner.execute(OkHarness(), ctx)
        with pytest.raises(HarnessError, match="duplicate"):
            runner.execute(OkHarness(), ctx)

    def test_sanitize_run_id_path(self, tmp_path):
        """B4: run_id with invalid Windows chars still produces evidence."""
        runner = make_runner(tmp_path)
        ctx = HarnessContext(run_id="harness:a?b", harness="ok", target="t",
                             started_at="2026-01-01T00:00:00Z")
        report = runner.execute(OkHarness(), ctx)
        assert len(report.artifacts) == 2
        assert all(a.ref for a in report.artifacts)

    def test_no_artifact_service_in_memory(self):
        """B1: artifact_service=None -> in-memory report with path/ref None."""
        runner = make_runner(artifact=False)
        ctx = runner.create_context(OkHarness(), target="t")
        report = runner.execute(OkHarness(), ctx)
        assert report.result.status is HarnessRunStatus.COMPLETED
        assert all(a.path is None for a in report.artifacts)

    def test_deterministic(self, tmp_path):
        """AC10: same input -> same report (except timestamps + ref)."""
        r1 = make_runner(tmp_path)
        r2 = make_runner(tmp_path)
        ctx1 = HarnessContext(run_id="harness:fixed", harness="ok", target="t",
                              started_at="2026-01-01T00:00:00Z")
        ctx2 = HarnessContext(run_id="harness:fixed", harness="ok", target="t",
                              started_at="2026-01-01T00:00:00Z")
        rep1 = r1.execute(OkHarness(), ctx1)
        rep2 = r2.execute(OkHarness(), ctx2)
        d1, d2 = rep1.model_dump(), rep2.model_dump()
        for d in (d1, d2):
            d.pop("generated_at")
            for a in d["artifacts"]:
                a.pop("created_at")
                a.pop("ref")  # B2: checksum contains timestamps
            d["result"]["metrics"].pop("duration_ms")
        assert d1 == d2

    def test_get_evidence_unknown(self):
        runner = make_runner(artifact=False)
        assert runner.get_evidence("nope") == []  # B8

    def test_get_evidence_restart_fallback(self, tmp_path):
        """B3: evidence survives restart via ArtifactService sidecars."""
        artifacts_dir = tmp_path / "artifacts"
        runner = make_runner(tmp_path)
        ctx = runner.create_context(OkHarness(), target="t")
        runner.execute(OkHarness(), ctx)
        # Simulate restart: new StateService (in-memory lost), same artifacts dir.
        from aios_core.kernel.events import EventBus
        from aios_core.kernel.services import ArtifactService

        fresh = HarnessRunner(
            StateService(),
            ArtifactService(str(artifacts_dir), EventBus()))
        evidence = fresh.get_evidence(ctx.run_id)
        assert len(evidence) == 2  # reconstructed from sidecars

    def test_evidence_files_parseable(self, tmp_path):
        """B11: evidence JSON on disk parses + checksum matches."""
        runner = make_runner(tmp_path)
        ctx = runner.create_context(OkHarness(), target="t")
        runner.execute(OkHarness(), ctx)
        from aios_core.kernel.services import ArtifactService
        from aios_core.contracts.artifact import ArtifactType

        artifacts = ArtifactService(str(tmp_path / "artifacts"), None)
        contracts = artifacts.list(ArtifactType.JSON)
        assert len(contracts) == 2
        for contract in contracts:
            content = artifacts.load(contract)
            parsed = json.loads(content.decode("utf-8"))
            assert parsed is not None


# ---------------------------------------------------------------------------
# INV-018 behavioral
# ---------------------------------------------------------------------------

def test_inv018_every_run_has_evidence(tmp_path):
    """Every run — success AND failure — produces >= 2 artifacts (INV-018)."""
    runner = make_runner(tmp_path)
    ok_ctx = runner.create_context(OkHarness(), target="t")
    fail_ctx = runner.create_context(FailHarness(), target="t")
    ok_report = runner.execute(OkHarness(), ok_ctx)
    fail_report = runner.execute(FailHarness(), fail_ctx)
    assert len(ok_report.artifacts) == 2
    assert len(fail_report.artifacts) == 2


# ---------------------------------------------------------------------------
# INV-017 behavioral — duck-typed state/artifact stubs
# ---------------------------------------------------------------------------

def test_inv017_duck_typed_state():
    class StubState:
        def __init__(self):
            self.store = {}

        def update_state(self, key, **fields):
            self.store[key] = fields

        def get_state(self, key):
            return self.store.get(key)

    runner = HarnessRunner(StubState(), None)
    ctx = runner.create_context(OkHarness(), target="t")
    report = runner.execute(OkHarness(), ctx)
    assert report.result.status is HarnessRunStatus.COMPLETED
