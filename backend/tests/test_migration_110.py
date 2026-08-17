"""M12-P1 (TASK-085): Migration 1.0→1.1 — transforms + matrix gate + CLI."""

from __future__ import annotations

import json

import pytest

from aios_core.upgrade.backup import BackupStore
from aios_core.upgrade.compatibility import AIOS_VERSION
from aios_core.upgrade.migration import MigrationEngine, MigrationError, MigrationJournal
from aios_core.upgrade.migration_110 import (
    Aios110Migrator,
    get_plan,
    migrate_config_100_110,
    migrate_contract_100_110,
    migrate_plugin_100_110,
    migrate_workflow_100_110,
    rollback_config_100_110,
    rollback_contract_100_110,
    rollback_plugin_100_110,
    rollback_workflow_100_110,
)


def _migrator(tmp_path):
    return Aios110Migrator(
        engine=MigrationEngine(journal=MigrationJournal(str(tmp_path / "m.db"))),
        backup_store=BackupStore(str(tmp_path / "b.db")),
    )


# -- AC1: plan registry -------------------------------------------------------

def test_get_plan_4_kinds_and_id_per_component():
    for kind in ("config", "workflow", "plugin", "contract"):
        plan = get_plan(kind, "comp-x")
        assert plan is not None
        assert plan.from_version == "1.0.0"
        assert plan.to_version == AIOS_VERSION
        assert plan.backup_required is True
        assert len(plan.steps) >= 1
        assert plan.steps[0].rollback_fn is not None
        assert plan.migration_id == f"aios-1.0-to-1.1-{kind}-comp-x"


def test_get_plan_unknown_kind_none():
    assert get_plan("bogus", "x") is None


# -- AC2: plugin transform (append/remove "1.1.0" — C2-03) --------------------

def test_plugin_migrate_appends_110():
    payload = {"id": "demo", "version": "1.0.0", "aios": {"min": "1.0.0"}}
    out = migrate_plugin_100_110(payload)
    assert out["aios"]["compatible"] == ["1.0.0", "1.1.0"]
    assert payload == {"id": "demo", "version": "1.0.0", "aios": {"min": "1.0.0"}}  # no mutate


def test_plugin_migrate_keeps_existing_entries():
    payload = {"id": "p", "version": "1.0.0", "aios": {"compatible": ["1.0.0"]}}
    out = migrate_plugin_100_110(payload)
    assert out["aios"]["compatible"] == ["1.0.0", "1.1.0"]


def test_plugin_migrate_idempotent():
    once = migrate_plugin_100_110({"id": "d", "aios": {"min": "1.0.0"}})
    twice = migrate_plugin_100_110(once)
    assert once == twice


def test_plugin_rollback_restores():
    payload = {"id": "p", "version": "1.0.0", "aios": {"compatible": ["1.0.0"]}}
    migrated = migrate_plugin_100_110(payload)
    assert migrated["aios"]["compatible"] == ["1.0.0", "1.1.0"]
    rolled = rollback_plugin_100_110(migrated)
    assert rolled["aios"]["compatible"] == ["1.0.0"]


def test_plugin_migrate_missing_aios_seeds():
    out = migrate_plugin_100_110({"id": "d", "version": "1.0.0"})
    assert out["aios"]["compatible"] == ["1.0.0", "1.1.0"]


# -- AC3: workflow transform --------------------------------------------------

def test_workflow_migrate_bumps_top_level_version():
    payload = {"name": "demo_flow", "version": "1.0.0",
               "nodes": [{"id": "n1", "type": "task", "name": "n1"}]}
    out = migrate_workflow_100_110(payload)
    assert out["version"] == "1.1.0"
    assert payload["version"] == "1.0.0"  # no mutate


def test_workflow_migrate_noop_other_version():
    out = migrate_workflow_100_110({"name": "w", "version": "0.9.0"})
    assert out["version"] == "0.9.0"


def test_workflow_rollback_guard():
    rolled = rollback_workflow_100_110({"name": "w", "version": "1.1.0"})
    assert rolled["version"] == "1.0.0"
    # payload đã sẵn 1.1.0 trước migration (forward no-op) → rollback KHÔNG hạ
    still = rollback_workflow_100_110({"name": "w", "version": "1.1.0", "pre": True})
    assert still["version"] == "1.0.0"


# -- AC4: contract + config ---------------------------------------------------

def test_contract_migrate_bumps_version():
    out = migrate_contract_100_110({"id": "agent", "version": "1.0.0"})
    assert out["version"] == "1.1.0"
    rolled = rollback_contract_100_110(out)
    assert rolled["version"] == "1.0.0"


def test_config_migrate_marker_and_rollback():
    payload = {}
    out = migrate_config_100_110(payload)
    assert out["migration"] == {"from": "1.0.0", "to": "1.1.0"}
    assert payload == {}  # no mutate
    rolled = rollback_config_100_110(out)
    assert "migration" not in rolled
    # guard: marker khác (user data) → không xóa
    custom = {"migration": {"from": "0.5.0", "to": "1.0.0"}}
    assert rollback_config_100_110(custom) == custom


# -- AC5/AC6/AC7: Aios110Migrator matrix gate ---------------------------------

def test_pre_check_unknown_entry_blocked(tmp_path):
    migrator = _migrator(tmp_path)
    payload = {"id": "p", "version": "1.0.0", "aios": {"min": "1.0.0"}}
    with pytest.raises(MigrationError, match="no matrix entry"):
        migrator.apply("plugin", payload)
    # journal không start
    journal = MigrationJournal(str(tmp_path / "m.db"))
    assert journal.status("aios-1.0-to-1.1-plugin-p") is None


def test_pre_check_range_blocked(tmp_path):
    migrator = _migrator(tmp_path)
    with pytest.raises(MigrationError, match="ngoài range"):
        migrator.apply("contract", {"id": "agent", "version": "0.5.0"})


def test_config_skips_range_and_matrix(tmp_path):
    migrator = _migrator(tmp_path)
    result = migrator.apply("config", {})
    assert result.journal_status == "completed"
    assert result.matrix["pre"] == "skipped"
    assert result.matrix["post"] == "ok"
    assert result.payload["migration"]["to"] == "1.1.0"


def test_apply_plugin_success(tmp_path):
    migrator = _migrator(tmp_path)
    payload = {"id": "demo", "version": "1.0.0", "aios": {"min": "1.0.0"}}
    result = migrator.apply("plugin", payload)
    assert result.journal_status == "completed"
    assert result.backup_id is not None
    assert result.matrix["pre"] == "ok" and result.matrix["post"] == "ok"
    assert result.payload["aios"]["compatible"] == ["1.0.0", "1.1.0"]


def test_apply_workflow_success(tmp_path):
    migrator = _migrator(tmp_path)
    payload = {"name": "demo_flow", "version": "1.0.0",
               "nodes": [{"id": "n1", "type": "task", "name": "n1"}]}
    result = migrator.apply("workflow", payload)
    assert result.journal_status == "completed"
    assert result.payload["version"] == "1.1.0"


def test_apply_contract_twice_different_components(tmp_path):
    migrator = _migrator(tmp_path)
    r1 = migrator.apply("contract", {"id": "agent", "version": "1.0.0"})
    r2 = migrator.apply("contract", {"id": "capability", "version": "1.0.0"})
    assert r1.journal_status == "completed"
    assert r2.journal_status == "completed"  # C2-04: idempotent per component
    # cùng component lần 2 → bị chặn
    with pytest.raises(MigrationError, match="đã applied"):
        migrator.apply("contract", {"id": "agent", "version": "1.0.0"})


def test_post_check_fail_rolls_back(tmp_path, monkeypatch):
    """post-check fail (transform no-op → version không đổi) → payload == bản gốc."""
    from aios_core.upgrade import migration_110 as m110

    # ép workflow transform thành no-op → engine.apply xong payload vẫn 1.0.0
    monkeypatch.setitem(m110._PLAN_TEMPLATES, "workflow",
                        (lambda data: data, m110.rollback_workflow_100_110))
    migrator = _migrator(tmp_path)
    payload = {"name": "demo_flow", "version": "1.0.0"}
    with pytest.raises(MigrationError, match="post-check fail"):
        migrator.apply("workflow", payload)
    # payload gốc không bị đổi (engine apply + rollback no-op)
    assert payload["version"] == "1.0.0"


# -- CLI (AC8/AC9) ------------------------------------------------------------

def _run(argv, capsys):
    from aios_core.workflow.cli import main

    code = main(argv)
    out = capsys.readouterr().out
    return code, out


def test_cli_migrate_110_contract_apply(tmp_path, capsys):
    code, out = _run(["migrate", "contract", "1.0.0", "1.1.0", "--apply",
                      "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["applied"] is True
    assert data["backup_id"] is not None
    assert data["journal"] == "completed"
    assert data["matrix"]["pre"] == "ok" and data["matrix"]["post"] == "ok"
    assert data["payload"]["version"] == "1.1.0"


def test_cli_migrate_110_plugin_apply(tmp_path, capsys):
    code, out = _run(["migrate", "plugin", "1.0.0", "1.1.0", "--apply",
                      "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["payload"]["aios"]["compatible"] == ["1.0.0", "1.1.0"]


def test_cli_migrate_110_dry_run_no_side_effect(tmp_path, capsys):
    journal_path = str(tmp_path / "m.db")
    code, out = _run(["migrate", "plugin", "1.0.0", "1.1.0", "--dry-run",
                      "--journal", journal_path], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["dry_run"] is True
    # journal không có gì (chưa start)
    assert MigrationJournal(journal_path).status("aios-1.0-to-1.1-plugin-demo") is None


def test_cli_migrate_110_input_file(tmp_path, capsys):
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps({"id": "demo", "version": "1.0.0", "aios": {"min": "1.0.0"}}))
    code, out = _run(["migrate", "plugin", "1.0.0", "1.1.0", "--apply",
                      "--input", str(inp), "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 0


def test_cli_migrate_110_input_missing_file(tmp_path, capsys):
    code, out = _run(["migrate", "plugin", "1.0.0", "1.1.0", "--apply",
                      "--input", str(tmp_path / "nope.json"),
                      "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 1
    assert "FAILED" in out


def test_cli_migrate_110_unknown_entry_exit_1(tmp_path, capsys):
    inp = tmp_path / "p.json"
    inp.write_text(json.dumps({"id": "p", "version": "1.0.0", "aios": {"min": "1.0.0"}}))
    code, out = _run(["migrate", "plugin", "1.0.0", "1.1.0", "--apply",
                      "--input", str(inp), "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 1
    assert "no matrix entry" in out


def test_cli_migrate_110_bogus_kind(tmp_path, capsys):
    code, out = _run(["migrate", "bogus", "1.0.0", "1.1.0", "--dry-run",
                      "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 1
    assert "FAILED" in out


def test_cli_migrate_old_path_still_works(tmp_path, capsys):
    code, out = _run(["migrate", "plugin", "0.9.0", "1.0.0", "--apply",
                      "--journal", str(tmp_path / "m.db")], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["applied"] is True
