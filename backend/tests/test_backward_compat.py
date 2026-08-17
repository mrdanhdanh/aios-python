"""M12-P2 (TASK-086): Backward Compatibility Suite + AiosRange fix + CLI verify."""

from __future__ import annotations

import json

import pytest

from aios_core.plugins.contracts import AiosRange, PluginManifest
from aios_core.upgrade.backward_compat import (
    BackwardCheck,
    BackwardCompatibilitySuite,
)


# -- AC1: suite đúng 9 check, 5 kind ------------------------------------------

def test_suite_9_checks_5_kinds():
    suite = BackwardCompatibilitySuite()
    ids = [c.id for c in suite.CHECKS]
    assert len(ids) == 9
    assert ids == [
        "workflow-v0-parse", "workflow-v0-run-simulate",
        "plugin-v0-load", "plugin-v1-compatible-field",
        "contract-v0-compat", "contract-v0-catalog",
        "extension-v0-matrix",
        "migrated-110-data", "migrated-v0-formats",
    ]
    kinds = {c.kind for c in suite.CHECKS}
    assert kinds == {"workflow", "plugin", "contract", "extension", "migrated"}


# -- AC2..AC6: 9 check chạy OK -------------------------------------------------

def test_all_checks_pass():
    report = BackwardCompatibilitySuite().run()
    assert report.ok is True
    assert report.fail_closed is True
    assert len(report.results) == 9
    for r in report.results:
        assert r.ok, f"{r.id} FAIL: {r.detail}"


def test_workflow_v0_parse_specific():
    from aios_core.upgrade.backward_compat import BackwardCompatibilitySuite

    suite = BackwardCompatibilitySuite()
    check = next(c for c in suite.CHECKS if c.id == "workflow-v0-parse")
    ok, detail = check.run()
    assert ok, detail


# -- AC7: fail-closed ----------------------------------------------------------

def test_fail_closed_one_check_raises():
    def boom() -> tuple[bool, str]:
        raise RuntimeError("kaboom")

    def fine() -> tuple[bool, str]:
        return True, "ok"

    suite = BackwardCompatibilitySuite(checks=[
        BackwardCheck("a", "plugin", "raise", boom),
        BackwardCheck("b", "contract", "fine", fine),
    ])
    report = suite.run()
    assert report.ok is False
    assert len(report.results) == 2
    assert report.results[0].ok is False
    assert "kaboom" in report.results[0].detail
    assert report.results[1].ok is True  # check khác vẫn chạy


def test_fail_closed_catches_base_exception():
    def sys_exit() -> tuple[bool, str]:
        raise SystemExit(3)

    suite = BackwardCompatibilitySuite(checks=[
        BackwardCheck("x", "plugin", "raise", sys_exit),
    ])
    report = suite.run()
    assert report.ok is False
    assert "SystemExit" in report.results[0].detail


# -- AC9: AiosRange fix (C1-01 + C2-04) ---------------------------------------

def test_aios_range_compatible_field():
    rng = AiosRange(min="1.0.0", max="*", compatible=["1.0.0", "1.1.0"])
    assert rng.compatible == ["1.0.0", "1.1.0"]
    # round-trip
    dumped = rng.model_dump()
    assert AiosRange.model_validate(dumped).compatible == ["1.0.0", "1.1.0"]


def test_aios_range_min_max_behavior_unchanged():
    # hành vi check min/max KHÔNG đổi (C2-04)
    assert AiosRange(min="1.0.0").min == "1.0.0"
    assert AiosRange().max == "*"
    assert AiosRange().compatible == []  # default


def test_plugin_manifest_v1_compatible_parses():
    manifest = PluginManifest.model_validate({
        "id": "demo", "name": "demo", "version": "1.0.0",
        "aios": {"min": "1.0.0", "compatible": ["1.0.0", "1.1.0"]},
    })
    assert manifest.aios.compatible == ["1.0.0", "1.1.0"]


def test_plugin_manifest_v0_still_parses():
    manifest = PluginManifest.validate_manifest(
        id="demo", name="demo", version="1.0.0",
        aios={"min": "1.0.0", "max": "*"},
    )
    assert manifest.aios.compatible == []


# -- AC8: CLI compat verify ----------------------------------------------------

def _run(argv, capsys):
    from aios_core.workflow.cli import main

    code = main(argv)
    out = capsys.readouterr().out
    return code, out


def test_cli_compat_verify(capsys):
    code, out = _run(["compat", "verify"], capsys)
    assert code == 0
    data = json.loads(out)  # JSON thuần — stdout ngoài JSON rỗng (C2-02)
    assert data["ok"] is True
    assert data["fail_closed"] is True
    assert data["summary"]["passed"] == 9
    assert data["summary"]["failed"] == 0
    assert len(data["results"]) == 9


def test_cli_compat_list_check_unchanged(capsys):
    code, out = _run(["compat", "list"], capsys)
    assert code == 0
    assert "entries" in out
    code2, out2 = _run(["compat", "check", "plugin", "demo", "1.0.0"], capsys)
    assert code2 == 0
    assert json.loads(out2)["compatible"] is True
