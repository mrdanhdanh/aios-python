"""M12-P3 (TASK-087): Compatibility Conformance — area + gate G + CLI."""

from __future__ import annotations

import pytest

from aios_core.harness.certification.checks import AreaChecks
from aios_core.harness.certification.conformance import ConformanceRunner
from aios_core.harness.certification.contracts import PassFail


# -- AC1/AC2: area compatibility -------------------------------------------------

def test_area_compatibility_exists_in_run_all():
    areas = AreaChecks().run_all()
    compat = next((a for a in areas if a.area == "compatibility"), None)
    assert compat is not None
    assert len(areas) == 11


def test_area_compatibility_pass():
    result = AreaChecks().compatibility()
    assert result.status == PassFail.PASS
    assert "matrix=14 entries" in result.evidence
    assert "verify=9/9" in result.evidence
    assert "version=1.1.0" in result.evidence


# -- AC3: fail-closed ------------------------------------------------------------

def test_area_compatibility_fail_closed(monkeypatch):
    import aios_core.upgrade.backward_compat as bc

    class _Broken:
        def run(self):
            raise RuntimeError("verify broken")

    monkeypatch.setattr(bc, "BackwardCompatibilitySuite", _Broken)
    result = AreaChecks().compatibility()
    assert result.status == PassFail.FAIL
    assert "verify broken" in result.evidence


# -- AC4/AC5: gate G --------------------------------------------------------------

def test_gate_g_standalone():
    gates = ConformanceRunner().release_gates()  # không areas → chạy thật
    assert gates["gate_g_compatibility"] is True
    assert len(gates) == 7


def test_gate_g_reuses_precomputed_areas():
    runner = ConformanceRunner()
    areas = AreaChecks().run_all()
    gates = runner.release_gates(areas=areas)  # reuse — không chạy lại
    assert gates["gate_g_compatibility"] is True


def test_gate_g_fail_when_area_fail():
    from aios_core.harness.certification.contracts import AreaResult

    gates = ConformanceRunner().release_gates(
        areas=[AreaResult("compatibility", PassFail.FAIL, "x")]
    )
    assert gates["gate_g_compatibility"] is False


def test_gate_g_exception_fail_closed(monkeypatch):
    import aios_core.harness.certification.conformance as conf

    class _Broken:
        def compatibility(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(conf.AreaChecks, "compatibility", _Broken().compatibility)
    gates = ConformanceRunner().release_gates()
    assert gates["gate_g_compatibility"] is False


# -- AC5/AC6: conformance full + CLI ----------------------------------------------

def test_conformance_11_areas_7_gates():
    runner = ConformanceRunner()
    report = runner.run()
    assert len(report.areas) == 11
    assert len(report.gates) == 7
    assert report.areas_ready
    assert report.gates_ready
    assert report.ready


def test_cli_conformance_compat(capsys):
    from aios_core.workflow.cli import main

    assert main(["conformance"]) == 0
    out = capsys.readouterr().out
    assert "AIOS Conformance 1.1" in out
    assert "compatibility" in out
    assert "gate_g_compatibility" in out
    assert "AIOS 1.1 READY" in out
