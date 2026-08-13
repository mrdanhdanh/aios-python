"""SkillManager lifecycle tests (AC4-AC12) + optimistic (C1-03) + dependents (R1)."""

import pytest

from aios_core.skills import (
    SkillManager,
    SkillSource,
    SkillState,
    ZipSource,
)
from aios_core.skills.errors import SkillError, SkillStateError


@pytest.fixture
def manager(tmp_path):
    zip_source = ZipSource()

    def loader(source, ref):
        if source == SkillSource.ZIP:
            return zip_source.load(ref)
        raise SkillError(f"no fixture for {source.value}")

    m = SkillManager(db_path=tmp_path / "skills.db", source_loader=loader,
                     event_sink=lambda et, pl: None)
    m.resolve(SkillSource.ZIP, "demo-pack")  # skill.demo_zip
    return m


def test_resolve_duplicate_raises(manager):
    with pytest.raises(SkillError, match="already exists"):
        manager.resolve(SkillSource.ZIP, "demo-pack")


def test_resolve_unknown_ref(manager):
    from aios_core.skills.errors import SkillError as SE

    with pytest.raises(SE, match="unknown zip ref"):
        manager.resolve(SkillSource.ZIP, "nope")


def test_validate_deps(manager):
    # skill.demo_zip has no deps -> validate passes.
    sk = manager.validate("skill.demo_zip")
    assert sk.state == SkillState.VALIDATED


def test_validate_dep_not_found(tmp_path):
    from aios_core.skills import GitSource

    m = SkillManager(db_path=tmp_path / "s.db", source_loader=lambda s, r: {
        "id": "sx", "name": "SX", "version": "1.0.0", "source": "git",
        "dependencies": ["ghost@>=1.0.0"],
    })
    m.resolve(SkillSource.GIT, "x")
    with pytest.raises(SkillError, match="dependency not found"):
        m.validate("sx")


def test_validate_dep_not_installed(tmp_path):
    db = tmp_path / "s.db"

    def loader(s, r):
        return {"id": "depx", "name": "DEPX", "version": "1.0.0", "source": "zip"}

    m = SkillManager(db_path=db, source_loader=loader)
    m.resolve(SkillSource.ZIP, "x")  # dep resolved only — NOT installed

    m2 = SkillManager(db_path=db, source_loader=lambda s, r: {
        "id": "leaf2", "name": "LEAF2", "version": "1.0.0", "source": "zip",
        "dependencies": ["depx"],
    })
    m2.resolve(SkillSource.ZIP, "y")
    with pytest.raises(SkillError, match="dependency not installed"):
        m2.validate("leaf2")


def test_lifecycle_chain(manager):
    sk = manager.validate("skill.demo_zip")
    sk = manager.install("skill.demo_zip")
    assert sk.state == SkillState.INSTALLED and sk.installed_at is not None
    sk = manager.enable("skill.demo_zip")
    assert sk.state == SkillState.ENABLED and sk.is_active()
    sk = manager.disable("skill.demo_zip")
    assert sk.state == SkillState.DISABLED and not sk.is_active()
    sk = manager.enable("skill.demo_zip")
    sk = manager.unload("skill.demo_zip")
    assert sk.state == SkillState.UNLOADED
    sk = manager.reload("skill.demo_zip")
    assert sk.state == SkillState.RELOADED and sk.is_active()


def test_upgrade_requires_greater(manager):
    manager.validate("skill.demo_zip")
    with pytest.raises(SkillError, match="greater"):
        manager.upgrade("skill.demo_zip", "1.0.0")
    with pytest.raises(SkillError, match="invalid new version"):
        manager.upgrade("skill.demo_zip", "abc")


def test_upgrade_and_rollback(manager):
    manager.validate("skill.demo_zip")
    manager.install("skill.demo_zip")
    manager.enable("skill.demo_zip")
    sk = manager.upgrade("skill.demo_zip", "2.0.0")
    assert sk.version == "2.0.0" and sk.state == SkillState.UPGRADED
    assert not sk.is_active()  # C1-06: upgrade from enabled -> not active anymore
    sk = manager.rollback("skill.demo_zip")
    assert sk.version == "1.0.0" and sk.state == SkillState.ROLLED_BACK


def test_rollback_no_history(manager):
    manager.validate("skill.demo_zip")
    manager.install("skill.demo_zip")
    manager.enable("skill.demo_zip")
    with pytest.raises(SkillStateError, match="no history"):
        manager.rollback("skill.demo_zip")


def test_remove_terminal(manager):
    manager.validate("skill.demo_zip")
    sk = manager.remove("skill.demo_zip")
    assert sk.state == SkillState.REMOVED
    with pytest.raises(SkillStateError, match="terminal"):
        manager.enable("skill.demo_zip")


def test_persist_across_restart(tmp_path):
    db = tmp_path / "skills.db"
    m1 = SkillManager(db_path=db, source_loader=lambda s, r: {
        "id": "sp", "name": "SP", "version": "1.0.0", "source": "zip",
    })
    m1.resolve(SkillSource.ZIP, "x")
    m1.validate("sp")
    m1.install("sp")
    m1.enable("sp")
    m2 = SkillManager(db_path=db)  # new instance, same DB
    sk = m2.get("sp")
    assert sk is not None and sk.state == SkillState.ENABLED


def test_optimistic_concurrency_two_instances(tmp_path):
    db = tmp_path / "skills.db"

    def loader(s, r):
        return {"id": "so", "name": "SO", "version": "1.0.0", "source": "zip"}

    m1 = SkillManager(db_path=db, source_loader=loader)
    m1.resolve(SkillSource.ZIP, "x")
    m1.validate("so")
    m1.install("so")
    m2 = SkillManager(db_path=db)
    # m1 removes; m2 then tries enable — must fail (state changed concurrently /
    # terminal), never resurrect the record.
    m1.remove("so")
    with pytest.raises(SkillStateError):
        m2.enable("so")


def test_rollback_dependent_broken(tmp_path):
    from aios_core.skills import build_default_sources

    sources = build_default_sources()
    db = tmp_path / "skills.db"
    m = SkillManager(db_path=db, source_loader=lambda s, r: dict(sources[s].load(r)))
    m.resolve(SkillSource.ZIP, "demo-pack")  # skill.demo_zip v1.0.0
    m.validate("skill.demo_zip")
    m.install("skill.demo_zip")
    # dependent needs >=2.0.0
    m2 = SkillManager(db_path=db, source_loader=lambda s, r: {
        "id": "dep1", "name": "DEP1", "version": "1.0.0", "source": "zip",
        "dependencies": ["skill.demo_zip@>=2.0.0"],
    })
    m2.resolve(SkillSource.ZIP, "x")
    # install dep1: validate fails since dep is 1.0.0 < 2.0.0
    with pytest.raises(SkillError, match="not compatible"):
        m2.validate("dep1")


def test_remove_blocked_by_active_dependent(tmp_path):
    db = tmp_path / "skills.db"
    m = SkillManager(db_path=db, source_loader=lambda s, r: {
        "id": "base", "name": "BASE", "version": "1.0.0", "source": "zip"})
    m.resolve(SkillSource.ZIP, "x")
    m.validate("base")
    m.install("base")
    m.enable("base")
    # dependent active depends on base (plain "id")
    m2 = SkillManager(db_path=db, source_loader=lambda s, r: {
        "id": "leaf", "name": "LEAF", "version": "1.0.0", "source": "zip",
        "dependencies": ["base"]})
    m2.resolve(SkillSource.ZIP, "y")
    m2.validate("leaf")
    m2.install("leaf")
    m2.enable("leaf")
    with pytest.raises(SkillError, match="dependent broken"):
        m.remove("base")
    # disable dependent -> remove ok
    m2.disable("leaf")
    m.remove("base")


def test_registry_read_through(manager):
    from aios_core.skills import SkillRegistry

    reg = SkillRegistry(manager._db_path)
    assert reg.get("skill.demo_zip") is not None
    assert reg.get("nope") is None
    assert [s.id for s in reg.list_by_capability("demo_cap")] == ["skill.demo_zip"]
    assert len(reg.list_by_state(SkillState.RESOLVED)) == 1


def test_check_constraint_domain_only(tmp_path):
    # C1-02: DB CHECK chỉ enforce domain — chèn resolved->enabled trực tiếp được.
    import sqlite3
    from contextlib import closing

    db = tmp_path / "skills.db"
    SkillManager(db_path=db, source_loader=lambda s, r: {
        "id": "z", "name": "Z", "version": "1.0.0", "source": "zip"})
    with closing(sqlite3.connect(db)) as conn, conn:
        conn.execute(
            "INSERT INTO skills (id, name, version, source, state, manifest_json,"
            " history_json, created_at, updated_at) VALUES ('z','Z','1.0.0','zip','enabled','{}','[]','t','t')"
        )
        assert conn.execute("SELECT state FROM skills WHERE id='z'").fetchone()[0] == "enabled"
    with pytest.raises(Exception):
        with closing(sqlite3.connect(db)) as conn, conn:
            conn.execute(
                "INSERT INTO skills (id, name, version, source, state, manifest_json,"
                " history_json, created_at, updated_at) VALUES ('b','B','1.0.0','zip','bogus','{}','[]','t','t')"
            )
