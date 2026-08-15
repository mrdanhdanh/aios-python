"""TASK-044 — Plugin Runtime (M8-E2) tests."""

from __future__ import annotations

import json

import pytest

from aios_core.plugins import (
    PluginCompatibilityError,
    PluginDependencyError,
    PluginError,
    PluginManager,
    PluginRegistry,
    PluginState,
    PluginType,
    check_compatibility,
    parse_constraint,
)
from aios_core.plugins.compat import Constraint

MANIFEST_BASE = {
    "id": "github.integration",
    "name": "GitHub Integration",
    "version": "1.2.0",
    "aios": {"min": "1.8.0", "max": "2.x"},
    "plugin_type": "integration",
    "provides": [
        {"kind": "capability", "id": "github.repository"},
        {"kind": "tool", "id": "github.search"},
    ],
    "permissions": ["repository.read", "repository.write"],
}


def make_manager(tmp_path, aios_version="1.9.0", strict=True, sink=None):
    return PluginManager(
        db_path=tmp_path / "plugins.db",
        aios_version=aios_version,
        strict=strict,
        event_sink=sink,
    )


def resolve_github(manager, **overrides):
    manifest = {**MANIFEST_BASE, **overrides}
    return manager.resolve("github.integration", manifest)


# -- compat -------------------------------------------------------------------


def test_parse_constraint_forms():
    assert parse_constraint("*") == Constraint(raw="*")
    assert parse_constraint("2.x").major == 2
    assert parse_constraint("2.x").minor is None
    assert parse_constraint("1.8.0").patch == 0
    with pytest.raises(PluginCompatibilityError):
        parse_constraint("x.y")
    with pytest.raises(PluginCompatibilityError):
        parse_constraint("not-a-version")


def test_check_compatibility_ranges():
    assert check_compatibility("1.8.0", "2.x", "1.9.0")
    assert check_compatibility("1.8.0", "2.x", "2.5.1")
    assert not check_compatibility("1.8.0", "2.x", "3.0.0")
    assert not check_compatibility("1.8.0", "2.x", "1.7.9")
    assert check_compatibility("*", "*", "0.0.1")
    assert check_compatibility("2.0.0", "*", "2.1.0")


# -- lifecycle ----------------------------------------------------------------


def test_full_lifecycle(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    assert manager.get("github.integration").state == PluginState.RESOLVED
    manager.validate("github.integration")
    manager.install("github.integration")
    assert manager.get("github.integration").installed_at is not None
    manager.enable("github.integration")
    assert manager.get("github.integration").state == PluginState.ENABLED
    manager.disable("github.integration")
    assert manager.get("github.integration").state == PluginState.DISABLED
    manager.unload("github.integration")
    assert manager.get("github.integration").state == PluginState.UNLOADED
    manager.reload("github.integration")
    assert manager.get("github.integration").state == PluginState.RELOADED
    manager.upgrade("github.integration", "1.3.0")
    assert manager.get("github.integration").version == "1.3.0"
    manager.rollback("github.integration")
    assert manager.get("github.integration").version == "1.2.0"
    manager.remove("github.integration")
    assert manager.get("github.integration").state == PluginState.REMOVED


def test_resolve_compat_rejected(tmp_path):
    manager = make_manager(tmp_path, aios_version="1.7.0")
    with pytest.raises(PluginCompatibilityError):
        resolve_github(manager)


def test_resolve_duplicate_rejected(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    with pytest.raises(PluginError, match="already exists"):
        resolve_github(manager)


def test_invalid_transition(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    with pytest.raises(PluginError):
        manager.enable("github.integration")  # resolved -> enable không hợp lệ


def test_upgrade_requires_newer(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    with pytest.raises(PluginError, match="must be > current"):
        manager.upgrade("github.integration", "1.1.0")


def test_rollback_no_history(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    with pytest.raises(PluginError):
        manager.rollback("github.integration")


def test_rollback_restores_full_manifest(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager, description="v1 description")
    manager.validate("github.integration")
    manager.install("github.integration")
    manager.upgrade("github.integration", "2.0.0")
    upgraded = manager.get("github.integration")
    assert upgraded.version == "2.0.0"
    manager.rollback("github.integration")
    rolled = manager.get("github.integration")
    assert rolled.version == "1.2.0"
    assert rolled.manifest["description"] == "v1 description"


# -- dependencies -------------------------------------------------------------


def test_dependency_check(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    # dep chỉ RESOLVED (chưa install) → validate plugin phụ thuộc phải fail
    dep_manifest = {
        **MANIFEST_BASE,
        "id": "github.pr",
        "name": "GitHub PR",
        "version": "1.0.0",
        "dependencies": ["github.integration@>=1.2.0"],
    }
    manager.resolve("github.pr", dep_manifest)
    with pytest.raises(PluginDependencyError, match="not installed"):
        manager.validate("github.pr")


def test_dependency_version_gate(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    dep_manifest = {
        **MANIFEST_BASE,
        "id": "github.pr",
        "name": "GitHub PR",
        "version": "1.0.0",
        "dependencies": ["github.integration@>=2.0.0"],
    }
    manager.resolve("github.pr", dep_manifest)
    with pytest.raises(PluginDependencyError, match="not compatible"):
        manager.validate("github.pr")


def test_remove_blocked_by_dependent(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    manager.enable("github.integration")
    dep_manifest = {
        **MANIFEST_BASE,
        "id": "github.pr",
        "name": "GitHub PR",
        "version": "1.0.0",
        "dependencies": ["github.integration"],
    }
    manager.resolve("github.pr", dep_manifest)
    manager.validate("github.pr")
    manager.install("github.pr")
    with pytest.raises(PluginDependencyError, match="depends on it"):
        manager.remove("github.integration")
    with pytest.raises(PluginDependencyError, match="depends on it"):
        manager.rollback("github.integration")


def test_remove_ok_without_dependents(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    manager.remove("github.integration")
    assert manager.get("github.integration").state == PluginState.REMOVED


# -- provides -----------------------------------------------------------------


def test_provides_only_active(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    # chưa enable → chưa xuất hiện
    assert manager.provides("tool") == {}
    manager.enable("github.integration")
    assert manager.provides("tool") == {"github.search": "github.integration"}
    assert manager.provides("capability") == {"github.repository": "github.integration"}
    manager.disable("github.integration")
    assert manager.provides("tool") == {}
    manager.unload("github.integration")
    manager.reload("github.integration")
    assert manager.provides("tool") == {"github.search": "github.integration"}


def test_provides_after_restart(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    manager.enable("github.integration")
    # instance mới rebuild index từ DB
    fresh = make_manager(tmp_path)
    assert fresh.provides("tool") == {"github.search": "github.integration"}


# -- events + concurrency ------------------------------------------------------


def test_events_emitted(tmp_path):
    events = []
    manager = make_manager(tmp_path, sink=lambda kind, payload: events.append((kind, payload)))
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    kinds = [kind for kind, _ in events]
    assert kinds == ["plugin.resolved", "plugin.installed"]


def test_concurrent_state_change_rejected(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")  # DB thực: installed
    # giả lập view stale: manager vẫn đọc state cũ 'validated'
    original = manager._get_row  # noqa: SLF001

    def stale_row(conn, plugin_id):
        row = original(conn, plugin_id)
        if row is None:
            return None
        return tuple(row[:4]) + ("validated",) + tuple(row[5:])

    manager._get_row = stale_row  # type: ignore[method-assign]  # noqa: SLF001
    with pytest.raises(PluginError, match="state changed concurrently"):
        manager.install("github.integration")


# -- registry ------------------------------------------------------------------


def test_registry_views(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    manager.validate("github.integration")
    manager.install("github.integration")
    registry = PluginRegistry(tmp_path / "plugins.db")
    assert registry.get("github.integration") is not None
    assert len(registry.list()) == 1
    assert len(registry.list_by_state(PluginState.INSTALLED)) == 1
    assert len(registry.list_by_kind(PluginType.INTEGRATION)) == 1
    assert registry.provides("tool") == {}


def test_manifest_extra_forbidden():
    from aios_core.plugins.contracts import PluginManifest

    with pytest.raises(Exception):
        PluginManifest.validate_manifest(**{**MANIFEST_BASE, "unknown_field": 1})


def test_manifest_json_roundtrip(tmp_path):
    manager = make_manager(tmp_path)
    resolve_github(manager)
    plugin = manager.get("github.integration")
    assert plugin.manifest["provides"][0]["id"] == "github.repository"
    assert plugin.manifest["permissions"] == ["repository.read", "repository.write"]
