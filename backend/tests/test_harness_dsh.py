"""TASK-104 — DSH Bridge tests (M16): independent verification oracle."""

from __future__ import annotations

import json

import pytest

from aios_core.config import Settings
from aios_core.harness import HarnessContext, HarnessRegistry, HarnessRunner, HarnessRunStatus
from aios_core.harness.contracts import utcnow
from aios_core.harness.dsh_bridge import (
    DSHBridgeEngine, DSHBridgeError, DSHBridgeHarness, DSHConfig,
    DSHStatus, InvariantResult, OracleReport,
)
from aios_core.kernel.services import StateService


def _ctx(run_id, **config):
    return HarnessContext(run_id=run_id, harness="dsh", target="dsh",
                          started_at=utcnow(), config=config)


class TestContracts:
    def test_dsh_status_enum(self):
        assert {s.value for s in DSHStatus} == {
            "connected", "disconnected", "error", "unconfigured"}

    def test_config_default(self):
        c = DSHConfig()
        assert c.enabled is False
        assert c.telemetry_disabled is True

    def test_invariant_result_shape(self):
        r = InvariantResult(invariant_id="INV-017", name="Harness Isolation",
                            passed=True, detail="ok", source="dsh")
        assert r.model_dump()


class TestEngine:
    def test_unconfigured(self):
        report = DSHBridgeEngine().check_invariants()
        assert report.dsh_status == DSHStatus.UNCONFIGURED
        assert report.invariants_checked == 0
        assert report.is_truly_independent is False

    def test_configured_stub(self):
        config = DSHConfig(enabled=True, bin_path="/usr/bin/dsh", version="0.1.0")
        report = DSHBridgeEngine(config).check_invariants()
        assert report.dsh_status == DSHStatus.CONNECTED
        assert report.invariants_checked == 4
        assert report.invariants_passed == 4
        assert report.is_truly_independent is True

    def test_determinism(self):
        r1 = DSHBridgeEngine().check_invariants().model_dump()
        r2 = DSHBridgeEngine().check_invariants().model_dump()
        assert r1 == r2


class TestHarness:
    def test_id_version(self):
        h = DSHBridgeHarness()
        assert h.id == "dsh"
        assert h.version == "1.0.0"

    def test_run_unconfigured(self):
        h = DSHBridgeHarness()
        ctx = _ctx("r1")
        payload = h.run(ctx)
        assert payload["dsh_status"] == "unconfigured"

    def test_full_runner(self):
        state = StateService()
        h = DSHBridgeHarness(state_service=state)
        runner = HarnessRunner(state_service=state)
        ctx = runner.create_context(h, "dsh", config={"strict": False})
        report = runner.execute(h, ctx)
        assert report.result.status == HarnessRunStatus.COMPLETED


class TestWiring:
    def test_registry_has_dsh(self):
        from aios_core.kernel import RuntimeKernel
        kernel = RuntimeKernel.create(Settings())
        reg = kernel.container.resolve(HarnessRegistry)
        assert reg.get("dsh") is not None
        assert len(reg.list()) == 16


class TestCLI:
    def test_cli_exit_0(self, capsys):
        from aios_core.workflow.cli import main
        rc = main(["harness", "dsh"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "dsh" in data
        assert rc == 0
