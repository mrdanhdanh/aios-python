"""UpgradePipeline tests (TASK-020) — DictMigrator + SkillMigrator."""

import pytest

from aios_core.skills import SkillManager
from aios_core.upgrade import (
    BackupStore,
    ComponentSpec,
    Dependency,
    DependencyResolver,
    DictMigrator,
    SkillMigrator,
    UpgradeError,
    UpgradePipeline,
)


def make_pipeline(store: dict | None = None, validate=None, emit=None, tmp_path=None):
    store = store if store is not None else {}
    migrator = DictMigrator(store)
    backup = BackupStore(tmp_path / "upgrade.db") if tmp_path else BackupStore(":memory:")

    def lookup(kind: str, component_id: str):
        payload = store.get(f"{kind}:{component_id}")
        if payload is None:
            return None
        deps = tuple(
            Dependency(d["name"], d["version"])
            for d in payload.get("dependencies", []) if isinstance(d, dict)
        )
        return ComponentSpec(kind, component_id, payload["version"], deps)

    resolver = DependencyResolver(lookup)
    return UpgradePipeline(migrator, backup, resolver, validate=validate, emit=emit)


def test_success_sequence_and_events(tmp_path):
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0", "state": "enabled"}}
    pipe = make_pipeline(store, emit=lambda t, p: events.append(t), tmp_path=tmp_path)
    result = pipe.run("skill", "root", "1.1.0")
    assert result.status == "ok"
    assert result.backup_id is not None
    assert store["skill:root"]["version"] == "1.1.0"
    assert events == [
        "UPGRADE_STARTED",
        "UPGRADE_COMPATIBILITY_OK",
        "UPGRADE_DEPENDENCIES_OK",
        "UPGRADE_BACKUP_CREATED",
        "UPGRADE_MIGRATED",
        "UPGRADE_HEALTH_OK",
        "UPGRADE_COMPLETED",
    ]
    assert [s.component_id for s in result.plan] == ["root"]


def test_compatibility_fail_major_break(tmp_path):
    """1.0.0 → 2.0.0 = breaking → dừng bước 1, không backup/migrate."""
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0"}}
    pipe = make_pipeline(store, emit=lambda t, p: events.append(t), tmp_path=tmp_path)
    result = pipe.run("skill", "root", "2.0.0")
    assert result.status == "failed"
    assert result.step == "compatibility"
    assert result.reason
    assert store["skill:root"]["version"] == "1.0.0"  # chưa đụng
    assert events == ["UPGRADE_STARTED"]  # không backup/migrate events


def test_dependency_missing_fails_before_backup(tmp_path):
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0", "dependencies": [{"name": "ghost", "version": "1.0.0"}]}}
    pipe = make_pipeline(store, emit=lambda t, p: events.append(t), tmp_path=tmp_path)
    result = pipe.run("skill", "root", "1.1.0")
    assert result.status == "failed"
    assert result.step == "dependencies"
    assert "missing dependency" in result.reason
    assert events == ["UPGRADE_STARTED", "UPGRADE_COMPATIBILITY_OK"]
    assert store["skill:root"]["version"] == "1.0.0"


def test_skip_same_or_older_version(tmp_path):
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0"}}
    pipe = make_pipeline(store, emit=lambda t, p: events.append(t), tmp_path=tmp_path)
    same = pipe.run("skill", "root", "1.0.0")
    assert same.status == "skipped"
    assert same.step is None
    older = pipe.run("skill", "root", "0.9.0")
    assert older.status == "skipped"
    assert events == ["UPGRADE_STARTED", "UPGRADE_SKIPPED", "UPGRADE_STARTED", "UPGRADE_SKIPPED"]


def test_component_not_found_fails_early(tmp_path):
    pipe = make_pipeline({}, tmp_path=tmp_path)
    result = pipe.run("skill", "nope", "1.1.0")
    assert result.status == "failed"
    assert result.step == "compatibility"
    assert "component not found" in result.reason


def test_dry_run_no_changes(tmp_path):
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0"}}
    pipe = make_pipeline(store, emit=lambda t, p: events.append(t), tmp_path=tmp_path)
    result = pipe.run("skill", "root", "1.1.0", dry_run=True)
    assert result.status == "ok"
    assert result.backup_id is None
    assert store["skill:root"]["version"] == "1.0.0"  # không đổi
    assert events == [
        "UPGRADE_STARTED",
        "UPGRADE_COMPATIBILITY_OK",
        "UPGRADE_DEPENDENCIES_OK",
    ]
    assert [s.component_id for s in result.plan] == ["root"]


def test_dry_run_incompatible_returns_failed(tmp_path):
    store = {"skill:root": {"version": "1.0.0"}}
    pipe = make_pipeline(store, tmp_path=tmp_path)
    result = pipe.run("skill", "root", "2.0.0", dry_run=True)
    assert result.status == "failed"
    assert result.step == "compatibility"


def test_migrate_raise_triggers_rollback_via_write_current(tmp_path):
    """DictMigrator không có rollback → fallback write_current(backup)."""
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0"}}
    migrator = DictMigrator(store)
    backup = BackupStore(tmp_path / "upgrade.db")

    def lookup(kind: str, component_id: str):
        payload = store.get(f"{kind}:{component_id}")
        return ComponentSpec(kind, component_id, payload["version"]) if payload else None

    def failing_migrate(kind, component_id, new_version):
        raise UpgradeError("boom during migrate")

    migrator.migrate = failing_migrate  # type: ignore[method-assign]
    pipe = UpgradePipeline(migrator, backup, DependencyResolver(lookup),
                           emit=lambda t, p: events.append(t))
    result = pipe.run("skill", "root", "1.1.0")
    assert result.status == "failed"
    assert result.step == "migrate"
    assert "boom" in result.reason
    # rollback fallback: write_current restore payload gốc
    assert store["skill:root"]["version"] == "1.0.0"
    assert "UPGRADE_ROLLED_BACK" in events


def test_health_fail_triggers_rollback(tmp_path):
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0"}}
    # migrator giả: migrate ghi version mới nhưng health verify sẽ fail vì
    # read_current trả version cũ (simulate migration không áp dụng)
    class FakeMigrator(DictMigrator):
        def migrate(self, kind, component_id, new_version):
            pass  # không áp dụng gì → health fail

    migrator = FakeMigrator(store)
    backup = BackupStore(tmp_path / "upgrade.db")

    def lookup(kind: str, component_id: str):
        payload = store.get(f"{kind}:{component_id}")
        return ComponentSpec(kind, component_id, payload["version"]) if payload else None

    pipe = UpgradePipeline(migrator, backup, DependencyResolver(lookup),
                           emit=lambda t, p: events.append(t))
    result = pipe.run("skill", "root", "1.1.0")
    assert result.status == "failed"
    assert result.step == "health"
    assert "health check failed" in result.reason
    # rollback qua write_current (FakeMigrator rollback = NotImplementedError)
    assert store["skill:root"]["version"] == "1.0.0"
    assert "UPGRADE_ROLLED_BACK" in events


def test_validate_hook_failure_rolls_back(tmp_path):
    store = {"skill:root": {"version": "1.0.0"}}
    pipe = make_pipeline(store, validate=lambda k, i, v: "contract mismatch", tmp_path=tmp_path)
    result = pipe.run("skill", "root", "1.1.0")
    assert result.status == "failed"
    assert result.step == "health"
    assert "contract mismatch" in result.reason
    assert store["skill:root"]["version"] == "1.0.0"


def test_rollback_error_best_effort(tmp_path):
    """rollback raise → reason ghi lỗi, không raise, rolled_back=False."""
    events: list[str] = []
    store = {"skill:root": {"version": "1.0.0"}}

    class BrokenRollbackMigrator(DictMigrator):
        def migrate(self, kind, component_id, new_version):
            store["skill:root"]["version"] = new_version

        def rollback(self, kind, component_id):
            raise UpgradeError("rollback exploded")

    migrator = BrokenRollbackMigrator(store)
    backup = BackupStore(tmp_path / "upgrade.db")

    def lookup(kind: str, component_id: str):
        payload = store.get(f"{kind}:{component_id}")
        return ComponentSpec(kind, component_id, payload["version"]) if payload else None

    def failing_migrate(kind, component_id, new_version):
        raise UpgradeError("migrate failed")

    migrator.migrate = failing_migrate  # type: ignore[method-assign]
    pipe = UpgradePipeline(migrator, backup, DependencyResolver(lookup),
                           emit=lambda t, p: events.append(t))
    result = pipe.run("skill", "root", "1.1.0")  # không raise
    assert result.status == "failed"
    assert result.reason == "migrate failed"
    rolled_back_event = events[-1]
    assert rolled_back_event == "UPGRADE_ROLLED_BACK"


def test_invalid_version_raises_valueerror(tmp_path):
    pipe = make_pipeline({"skill:root": {"version": "1.0.0"}}, tmp_path=tmp_path)
    with pytest.raises(ValueError):
        pipe.run("skill", "root", "not-a-version")


# -- SkillMigrator với SkillManager thật ----------------------------------------

DEMO_MANIFEST = {
    "id": "demo", "name": "Demo", "version": "1.0.0",
    "source": "zip", "dependencies": [],
}


def make_skill_manager(db_path) -> SkillManager:
    manager = SkillManager(db_path=str(db_path), source_loader=lambda source, ref: DEMO_MANIFEST)
    manager.resolve("zip", "demo")
    manager.validate("demo")
    manager.install("demo")
    manager.enable("demo")
    return manager


def test_skill_migrator_upgrade_ok(tmp_path):
    manager = make_skill_manager(tmp_path / "skills.db")

    migrator = SkillMigrator(manager)
    backup = BackupStore(tmp_path / "upgrade.db")

    def lookup(kind: str, component_id: str):
        found = manager.get(component_id)
        if found is None:
            return None
        return ComponentSpec("skill", component_id, found.version)

    pipe = UpgradePipeline(migrator, backup, DependencyResolver(lookup))
    result = pipe.run("skill", "demo", "1.1.0")
    assert result.status == "ok"
    updated = manager.get("demo")
    assert updated.version == "1.1.0"
    assert updated.state.value == "upgraded"


def test_skill_migrator_rollback_on_health_fail(tmp_path):
    manager = make_skill_manager(tmp_path / "skills.db")

    migrator = SkillMigrator(manager)
    backup = BackupStore(tmp_path / "upgrade.db")

    def lookup(kind: str, component_id: str):
        found = manager.get(component_id)
        if found is None:
            return None
        return ComponentSpec("skill", component_id, found.version)

    # validate luôn fail → health fail → rollback qua SkillManager.rollback
    pipe = UpgradePipeline(migrator, backup, DependencyResolver(lookup),
                           validate=lambda k, i, v: "always bad")
    result = pipe.run("skill", "demo", "1.1.0")
    assert result.status == "failed"
    assert result.step == "health"
    rolled = manager.get("demo")
    assert rolled.version == "1.0.0"
    assert rolled.state.value == "rolled_back"


def test_skill_migrator_not_found(tmp_path):
    db = tmp_path / "skills.db"
    manager = SkillManager(db_path=str(db))
    migrator = SkillMigrator(manager)
    assert migrator.read_current("skill", "missing") is None


def test_skill_migrator_bad_state_maps_to_upgrade_error(tmp_path):
    """Skill ở trạng thái RESOLVED (chưa validate) → upgrade raise → UpgradeError rõ."""
    manager = SkillManager(
        db_path=str(tmp_path / "skills.db"),
        source_loader=lambda source, ref: DEMO_MANIFEST,
    )
    manager.resolve("zip", "demo")  # state = resolved — không upgrade được
    migrator = SkillMigrator(manager)
    with pytest.raises(UpgradeError) as exc:
        migrator.migrate("skill", "demo", "1.1.0")
    assert "demo" in str(exc.value)


def test_skill_migrator_rollback_maps_error(tmp_path):
    manager = make_skill_manager(tmp_path / "skills.db")
    migrator = SkillMigrator(manager)
    # rollback khi chưa có history → SkillStateError → UpgradeError
    manager.remove("demo")
    with pytest.raises(UpgradeError):
        migrator.rollback("skill", "demo")


def test_skill_migrator_write_current_not_implemented(tmp_path):
    manager = make_skill_manager(tmp_path / "skills.db")
    migrator = SkillMigrator(manager)
    with pytest.raises(NotImplementedError):
        migrator.write_current("skill", "demo", {"version": "1.0.0"})
