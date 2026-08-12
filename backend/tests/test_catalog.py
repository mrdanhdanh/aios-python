"""System catalog tests."""

import pytest

from aios_core.catalog import CatalogError, SystemCatalog


@pytest.fixture
def cat():
    c = SystemCatalog()
    c.index_entry("workflow", "crud-gen", {"description": "CRUD API generator", "lang": "python"})
    c.index_entry("skill", "health-pack", {"tags": ["medical", "advice"]})
    return c


def test_index_get(cat):
    entry = cat.get("workflow", "crud-gen")
    assert entry.metadata["description"] == "CRUD API generator"


def test_upsert_replaces(cat):
    cat.index_entry("workflow", "crud-gen", {"description": "v2"})
    assert cat.get("workflow", "crud-gen").metadata["description"] == "v2"


def test_unknown_get(cat):
    with pytest.raises(CatalogError, match="Unknown catalog entry"):
        cat.get("workflow", "ghost")


def test_remove_idempotent(cat):
    cat.remove_entry("workflow", "crud-gen")
    cat.remove_entry("workflow", "crud-gen")  # idempotent
    assert cat.count() == 1


def test_search_empty_returns_all(cat):
    results = cat.search("")
    assert len(results) == 2


def test_search_case_insensitive_and_nested(cat):
    results = cat.search("CRUD")
    assert [e.id for e in results] == ["crud-gen"]
    results = cat.search("medical")
    assert [e.id for e in results] == ["health-pack"]


def test_search_kind_filter_exact(cat):
    results = cat.search("gen", kind="skill")
    assert results == []  # kind exact
    results = cat.search("", kind="skill")
    assert [e.id for e in results] == ["health-pack"]


def test_search_ignores_none_and_keys(cat):
    cat.index_entry("agent", "a1", {"note": None, "label": "hello"})
    # "None" must not match; keys (e.g. "note"/"label") must not match
    assert cat.search("none") == []
    assert cat.search("note") == []
    assert cat.search("hello") != []


def test_sorted_results(cat):
    cat.index_entry("workflow", "aaa-wf", {"d": "x"})
    results = cat.search("", kind="workflow")
    assert [e.id for e in results] == ["aaa-wf", "crud-gen"]  # sorted (kind, id)


def test_count(cat):
    assert cat.count() == 2
