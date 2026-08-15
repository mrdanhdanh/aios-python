"""TASK-046 — Ecosystem Registry (M8-E4) tests."""

import pytest

from aios_core.ecosystem import EcosystemEntry, EcosystemRegistry, EntryKind, Publisher

ENTRY = {
    "kind": "plugin",
    "id": "github.integration",
    "version": "1.2.0",
    "name": "GitHub Integration",
    "description": "GitHub repository + PR tools",
    "contract_namespace": "extension",
    "permissions": ["repository.read"],
    "dependencies": ["aios-core"],
    "compatibility": {"min": "1.8.0", "max": "2.x"},
    "capabilities": ["github.repository"],
    "publisher": {"id": "danh", "name": "Danh", "signing_key_id": "k1"},
    "signature": "abc123",
}


def test_entry_validation_extra_forbidden_and_semver():
    assert EcosystemEntry.validate_entry(**ENTRY).kind == EntryKind.PLUGIN
    with pytest.raises(Exception):
        EcosystemEntry.validate_entry(**{**ENTRY, "unknown": 1})
    with pytest.raises(Exception):
        EcosystemEntry.validate_entry(**{**ENTRY, "version": "not-semver"})


def test_index_get_update_persist(tmp_path):
    reg = EcosystemRegistry(tmp_path / "eco.db")
    entry = reg.index_entry(ENTRY)
    assert reg.get("plugin", "github.integration").id == entry.id
    assert reg.count() == 1
    # update (upsert)
    reg.index_entry({**ENTRY, "version": "1.3.0"})
    assert reg.get("plugin", "github.integration").version == "1.3.0"
    assert reg.count() == 1
    # persist qua restart
    fresh = EcosystemRegistry(tmp_path / "eco.db")
    assert fresh.count() == 1
    assert fresh.get("plugin", "github.integration").version == "1.3.0"


def test_search_deterministic_and_filters(tmp_path):
    reg = EcosystemRegistry(tmp_path / "eco.db")
    reg.index_entry(ENTRY)
    reg.index_entry({**ENTRY, "id": "oracle.integration", "name": "Oracle",
                     "description": "database tools", "kind": "integration"})
    hits = reg.search("github")
    assert [e.id for e in hits] == ["github.integration"]
    hits = reg.search("")  # tất cả, sort deterministic theo (kind, id)
    assert [e.id for e in hits] == ["oracle.integration", "github.integration"]
    hits = reg.search("", kind="integration")
    assert [e.id for e in hits] == ["oracle.integration"]
    hits = reg.search("danh")  # publisher id
    assert len(hits) == 2


def test_remove_entry(tmp_path):
    reg = EcosystemRegistry(tmp_path / "eco.db")
    reg.index_entry(ENTRY)
    assert reg.remove_entry("plugin", "github.integration") is True
    assert reg.remove_entry("plugin", "github.integration") is False
    assert reg.count() == 0


def test_list_by_kind(tmp_path):
    reg = EcosystemRegistry(tmp_path / "eco.db")
    reg.index_entry(ENTRY)
    reg.index_entry({**ENTRY, "id": "jira.integration", "kind": "integration"})
    assert len(reg.list_entries("plugin")) == 1
    assert len(reg.list_entries()) == 2


def test_index_accepts_model_directly(tmp_path):
    reg = EcosystemRegistry(tmp_path / "eco.db")
    model = EcosystemEntry.validate_entry(**ENTRY)
    reg.index_entry(model)
    assert reg.count() == 1
