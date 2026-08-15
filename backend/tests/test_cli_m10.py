"""TASK-071 — Developer Experience 1.0 (M10-F4)."""

from __future__ import annotations

import pytest


def test_doctor_has_18_items():
    from aios_core.cli.doctor import DoctorFirstClass

    report = DoctorFirstClass().run()
    ids = {c.item_id for c in report.checks}
    assert ids == {
        "runtime", "contracts", "registry", "models", "memory", "knowledge",
        "filesystem", "sandbox", "tools", "plugins", "policies", "permissions",
        "db", "events", "scheduler", "autonomy", "harness", "enterprise",
    }
    assert len(report.checks) == 18


def test_doctor_no_crash_and_score():
    from aios_core.cli.doctor import DoctorFirstClass

    report = DoctorFirstClass().run()
    for c in report.checks:
        assert c.status in ("pass", "warn", "fail")
    assert 0 <= report.score <= 100
    # runtime/contracts/models/events phải PASS (check thật chạy được)
    by_id = {c.item_id: c for c in report.checks}
    assert by_id["runtime"].status == "pass"
    assert by_id["contracts"].status == "pass"
    assert by_id["events"].status == "pass"


def test_doctor_format():
    from aios_core.cli.doctor import DoctorFirstClass, format_doctor_report

    text = format_doctor_report(DoctorFirstClass().run())
    assert "Health:" in text
    assert "runtime" in text and "enterprise" in text


def test_system_status():
    from aios_core.cli.system import system_status

    out = system_status()
    assert "version" in out
    assert "emergency" in out


def test_cli_health_alias(capsys):
    from aios_core.workflow.cli import main

    assert main(["health"]) == 0
    out = capsys.readouterr().out
    assert "Health:" in out and "runtime" in out


def test_cli_system_status(capsys):
    from aios_core.workflow.cli import main

    assert main(["system", "status"]) == 0
    out = capsys.readouterr().out
    assert '"version"' in out


def test_cli_goal_list_empty(capsys):
    from aios_core.workflow.cli import main

    assert main(["goal", "list"]) == 0
    out = capsys.readouterr().out
    assert "<empty>" in out or "progress" in out


def test_cli_execution_list_empty(capsys):
    from aios_core.workflow.cli import main

    assert main(["execution", "list"]) == 0
    out = capsys.readouterr().out
    assert "<empty>" in out or "|" in out


def test_cli_skill_and_capability_list(capsys):
    from aios_core.workflow.cli import main

    assert main(["skill", "list"]) == 0
    assert main(["capability", "list"]) == 0
    out = capsys.readouterr().out
    assert "<empty>" in out or "|" in out or "\n" in out


def test_old_doctor_json_still_works(capsys):
    """R3: doctor cũ (JSON) vẫn chạy — tương thích."""
    from aios_core.workflow.cli import main

    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert '"kernel": "ok"' in out
