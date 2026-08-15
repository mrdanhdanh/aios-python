"""TASK-074 — Upgrade & Migration 1.0 (M10-F5)."""

from __future__ import annotations

import pytest

from aios_core.upgrade.migration import (
    MigrationEngine,
    MigrationError,
    MigrationFormats,
    MigrationJournal,
    MigrationPlan,
    MigrationStep,
)


def _plan(steps=None, migration_id="m1", **kw):
    return MigrationPlan(
        migration_id=migration_id,
        kind="config",
        from_version=kw.get("from_version", "0.9.0"),
        to_version=kw.get("to_version", "1.0.0"),
        steps=steps or [MigrationStep(kind="config", id="s1", fn=lambda d: d)],
    )


# ---------------------------------------------------------------------------
# AC1: plan validation
# ---------------------------------------------------------------------------

def test_plan_validation():
    with pytest.raises(Exception):
        MigrationPlan(migration_id="x", kind="config", from_version="0.9.0",
                      to_version="1.0.0", steps=[])  # steps rỗng
    with pytest.raises(Exception):
        _plan(from_version="not-semver")
    with pytest.raises(Exception):
        MigrationPlan(migration_id="x", kind="config", from_version="0.9.0",
                      to_version="1.0.0", steps=[MigrationStep("c", "s", lambda d: d)],
                      bogus=1)  # extra=forbid


# ---------------------------------------------------------------------------
# AC2: dry-run không side effect
# ---------------------------------------------------------------------------

def test_dry_run_no_side_effect():
    calls = {"n": 0}

    def step_fn(data):
        calls["n"] += 1
        return {**data, "done": True}

    engine = MigrationEngine(journal=MigrationJournal(":memory:"))
    result = engine.dry_run(_plan(steps=[MigrationStep("config", "s1", step_fn)]),
                            {"x": 1})
    assert calls["n"] == 0  # fn không gọi
    assert result["x"] == 1
    assert result["_dry_run_steps"] == ["s1"]


# ---------------------------------------------------------------------------
# AC3/AC4: apply + rollback + journal
# ---------------------------------------------------------------------------

def test_apply_steps_and_journal(tmp_path):
    journal = MigrationJournal(tmp_path / "m.db")
    engine = MigrationEngine(journal=journal)
    log: list[str] = []

    def step1(data):
        log.append("s1")
        return {**data, "a": 1}

    def step2(data):
        log.append("s2")
        return {**data, "b": 2}

    plan = _plan(steps=[
        MigrationStep("config", "s1", step1, rollback_fn=lambda d: log.append("r1") or d),
        MigrationStep("config", "s2", step2, rollback_fn=lambda d: log.append("r2") or d),
    ])
    result = engine.apply(plan, {})
    assert result == {"a": 1, "b": 2}
    assert log == ["s1", "s2"]
    assert journal.status("m1") == "completed"


def test_rollback_reverse_order(tmp_path):
    journal = MigrationJournal(tmp_path / "m.db")
    engine = MigrationEngine(journal=journal)
    log: list[str] = []
    plan = _plan(steps=[
        MigrationStep("config", "s1", lambda d: log.append("apply1") or d,
                      rollback_fn=lambda d: log.append("rollback1") or d),
        MigrationStep("config", "s2", lambda d: log.append("apply2") or d,
                      rollback_fn=lambda d: log.append("rollback2") or d),
    ])
    engine.apply(plan, {})
    log.clear()
    engine.rollback(plan, {})
    assert log == ["rollback2", "rollback1"]  # ngược thứ tự


# ---------------------------------------------------------------------------
# AC5: fail giữa chừng → journal FAILED + auto-rollback
# ---------------------------------------------------------------------------

def test_apply_fail_auto_rollback(tmp_path):
    journal = MigrationJournal(tmp_path / "m.db")
    engine = MigrationEngine(journal=journal)
    log: list[str] = []

    def ok_step(data):
        log.append("ok")
        return {**data, "k": 1}

    def bad_step(data):
        log.append("bad")
        raise RuntimeError("boom")

    plan = _plan(steps=[
        MigrationStep("config", "ok", ok_step, rollback_fn=lambda d: log.append("r-ok") or d),
        MigrationStep("config", "bad", bad_step),
    ])
    with pytest.raises(MigrationError, match="rolled back"):
        engine.apply(plan, {})
    assert log == ["ok", "bad", "r-ok"]  # step ok được rollback
    assert journal.status("m1") in ("failed", "rolled_back")


def test_apply_idempotent(tmp_path):
    journal = MigrationJournal(tmp_path / "m.db")
    engine = MigrationEngine(journal=journal)
    engine.apply(_plan(), {})
    with pytest.raises(MigrationError, match="idempotent"):
        engine.apply(_plan(), {})


def test_validate_same_version():
    engine = MigrationEngine(journal=MigrationJournal(":memory:"))
    with pytest.raises(MigrationError):
        engine.validate(_plan(from_version="1.0.0", to_version="1.0.0"))


# ---------------------------------------------------------------------------
# AC6: formats v0→v1
# ---------------------------------------------------------------------------

def test_config_format():
    out = MigrationFormats.config_v0_to_v1(
        {"autonomous": {"budget": {"max_duration_s": 7200.0}}}
    )
    assert "max_duration_s" not in out["autonomous"]["budget"]
    assert out["autonomous"]["budget"]["max_duration_seconds"] == 7200.0


def test_workflow_format():
    out = MigrationFormats.workflow_v0_to_v1(
        {"id": "w", "nodes": [{"id": "n1", "type": "task", "name": "n1"}]}
    )
    assert out["nodes"][0]["timeout_s"] == 300.0


def test_plugin_format():
    out = MigrationFormats.plugin_v0_to_v1(
        {"id": "p", "aios": {"min": "1.0.0"}}
    )
    assert out["aios"]["compatible"] == ["1.0.0"]


def test_formats_deterministic():
    data = {"autonomous": {"budget": {"max_duration_s": 5.0}}}
    assert MigrationFormats.config_v0_to_v1(data) == \
        MigrationFormats.config_v0_to_v1(data)
    # input không bị mutate
    assert "max_duration_s" in data["autonomous"]["budget"]


# ---------------------------------------------------------------------------
# AC7: CLI
# ---------------------------------------------------------------------------

def test_cli_migrate_dry_run_and_apply(capsys, tmp_path):
    from aios_core.workflow.cli import main

    j = str(tmp_path / "m.db")
    assert main(["migrate", "config", "0.9.0", "1.0.0", "--dry-run",
                 "--journal", j]) == 0
    assert main(["migrate", "workflow", "0.9.0", "1.0.0", "--apply",
                 "--journal", j]) == 0
    out = capsys.readouterr().out
    assert "dry_run" in out
    assert "applied" in out


def test_cli_migrate_invalid_kind(capsys):
    from aios_core.workflow.cli import main

    assert main(["migrate", "bogus", "0.9.0", "1.0.0", "--dry-run"]) == 1
