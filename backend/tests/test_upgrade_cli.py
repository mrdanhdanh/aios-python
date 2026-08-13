"""Upgrade CLI tests (TASK-020) — `aiagent upgrade`."""

import json

import pytest

from aios_core.skills import SkillManager
from aios_core.workflow import cli


@pytest.fixture()
def skill_manager(tmp_path, monkeypatch):
    manager = SkillManager(
        db_path=str(tmp_path / "skills.db"),
        source_loader=lambda source, ref: {
            "id": "demo", "name": "Demo", "version": "1.0.0",
            "source": "zip", "dependencies": [],
        },
    )
    manager.resolve("zip", "demo")
    manager.validate("demo")
    manager.install("demo")
    manager.enable("demo")
    monkeypatch.setattr("aios_core.config.load_settings",
                        lambda: type("S", (), {"skills": type("K", (), {"db_path": str(tmp_path / "skills.db")})()})())
    monkeypatch.setattr("aios_core.skills.SkillManager", lambda db_path: manager)
    return manager


def test_upgrade_success(skill_manager, capsys):
    code = cli._upgrade("skill", "demo", "1.2.0", dry_run=False)
    out = capsys.readouterr().out
    assert code == 0
    assert "status: ok" in out
    assert "backup_id:" in out
    assert skill_manager.get("demo").version == "1.2.0"


def test_upgrade_dry_run(skill_manager, capsys):
    code = cli._upgrade("skill", "demo", "1.2.0", dry_run=True)
    out = capsys.readouterr().out
    assert code == 0
    assert "dry-run" in out
    assert "plan:" in out
    assert skill_manager.get("demo").version == "1.0.0"  # không đổi


def test_upgrade_skipped(skill_manager, capsys):
    code = cli._upgrade("skill", "demo", "1.0.0", dry_run=False)
    out = capsys.readouterr().out
    assert code == 0
    assert "status: skipped" in out


def test_upgrade_fail_exit_1(skill_manager, capsys):
    code = cli._upgrade("skill", "demo", "2.0.0", dry_run=False)
    out = capsys.readouterr().out
    assert code == 1
    assert "status: failed" in out


def test_upgrade_invalid_version(skill_manager, capsys):
    code = cli._upgrade("skill", "demo", "not-a-version", dry_run=False)
    out = capsys.readouterr().out
    assert code == 1
    assert "invalid version" in out


def test_upgrade_not_found(skill_manager, capsys):
    code = cli._upgrade("skill", "missing", "1.1.0", dry_run=False)
    out = capsys.readouterr().out
    assert code == 1
    assert "component not found" in out


def test_upgrade_not_wired_kind(skill_manager, capsys):
    code = cli._upgrade("workflow", "w1", "1.1.0", dry_run=False)
    out = capsys.readouterr().out
    assert code == 1
    assert "not wired" in out
