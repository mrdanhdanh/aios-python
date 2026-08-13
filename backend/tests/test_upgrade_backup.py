"""BackupStore tests (TASK-020)."""

import sqlite3
from contextlib import closing

from aios_core.upgrade.backup import BackupStore


def test_backup_restore_roundtrip(tmp_path):
    store = BackupStore(tmp_path / "upgrade.db")
    bid = store.backup("skill", "my-skill", "1.0.0", {"version": "1.0.0", "state": "enabled"})
    assert isinstance(bid, int) and bid > 0
    payload = store.restore(bid)
    assert payload == {"version": "1.0.0", "state": "enabled"}


def test_restore_missing_raises(tmp_path):
    store = BackupStore(tmp_path / "upgrade.db")
    try:
        store.restore(999)
        assert False, "expected KeyError"
    except KeyError as exc:
        assert "backup not found" in str(exc)


def test_list_filters(tmp_path):
    store = BackupStore(tmp_path / "upgrade.db")
    store.backup("skill", "s1", "1.0.0", {"v": "1"})
    store.backup("skill", "s2", "1.0.0", {"v": "1"})
    store.backup("workflow", "w1", "1.0.0", {"v": "1"})

    all_records = store.list()
    assert len(all_records) == 3
    skills = store.list(kind="skill")
    assert len(skills) == 2
    s1 = store.list(component_id="s1")
    assert len(s1) == 1 and s1[0].component_id == "s1"
    both = store.list(kind="skill", component_id="s2")
    assert len(both) == 1 and both[0].kind == "skill"
    assert all(r.kind == "skill" for r in skills)
    assert all(r.created_at for r in all_records)


def test_persists_across_instances(tmp_path):
    db = tmp_path / "upgrade.db"
    store1 = BackupStore(db)
    bid = store1.backup("skill", "s1", "1.0.0", {"version": "1.0.0"})

    store2 = BackupStore(db)  # fresh instance, same file
    payload = store2.restore(bid)
    assert payload == {"version": "1.0.0"}
    assert len(store2.list()) == 1


def test_payload_fidelity_with_nested(tmp_path):
    store = BackupStore(tmp_path / "upgrade.db")
    payload = {"version": "2.0.0", "nested": {"a": [1, 2, 3], "b": None}, "flag": True}
    bid = store.backup("skill", "s1", "2.0.0", payload)
    assert store.restore(bid) == payload


def test_schema_created(tmp_path):
    db = tmp_path / "upgrade.db"
    BackupStore(db).backup("skill", "s1", "1.0.0", {"v": "1"})
    with closing(sqlite3.connect(db)) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='backups'"
        ).fetchone()
    assert row is not None
