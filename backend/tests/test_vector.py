"""Vector store tests."""

import math

import pytest

from aios_core.memory import SQLiteVectorStore


@pytest.fixture
def store(tmp_path):
    return SQLiteVectorStore(str(tmp_path / "vec.db"))


def test_add_search_roundtrip(store):
    store.add("a", [1.0, 0.0])
    store.add("b", [0.0, 1.0])
    hits = store.search([1.0, 0.0], top_k=2)
    assert hits[0][0] == "a"  # same vector → score 1.0
    assert abs(hits[0][1] - 1.0) < 1e-9


def test_cosine_identical_and_orthogonal(store):
    store.add("a", [1.0, 1.0, 1.0])
    hits = store.search([1.0, 1.0, 1.0])
    assert abs(hits[0][1] - 1.0) < 1e-9
    store.add("b", [1.0, -1.0, 0.0])
    hits = store.search([1.0, 1.0, 1.0], top_k=2)
    b_score = dict((i, s) for i, s, _ in hits)["b"]
    assert abs(b_score) < 1e-9  # orthogonal


def test_empty_vector_raises(store):
    with pytest.raises(ValueError, match="non-zero norm"):
        store.add("a", [])
    store.add("b", [1.0, 0.0])
    with pytest.raises(ValueError, match="non-zero norm"):
        store.search([0.0, 0.0])


def test_zero_vector_raises(store):
    with pytest.raises(ValueError, match="non-zero norm"):
        store.add("a", [0.0, 0.0, 0.0])
    store.add("b", [1.0, 0.0, 0.0])
    with pytest.raises(ValueError, match="non-zero norm"):
        store.search([0.0, 0.0, 0.0])


def test_dim_mismatch_add(store):
    store.add("a", [1.0, 0.0])
    with pytest.raises(ValueError, match="dim"):
        store.add("b", [1.0, 0.0, 0.0])


def test_dim_mismatch_search(store):
    store.add("a", [1.0, 0.0])
    with pytest.raises(ValueError, match="dim"):
        store.search([1.0, 0.0, 0.0])


def test_duplicate_id_raises(store):
    store.add("a", [1.0, 0.0])
    with pytest.raises(ValueError, match="already exists"):
        store.add("a", [0.0, 1.0])


def test_empty_store_search(store):
    assert store.search([1.0, 0.0]) == []


def test_top_k_larger_than_count(store):
    store.add("a", [1.0, 0.0])
    store.add("b", [0.0, 1.0])
    assert len(store.search([1.0, 0.0], top_k=10)) == 2


def test_top_k_non_positive_raises(store):
    store.add("a", [1.0, 0.0])
    with pytest.raises(ValueError, match="top_k"):
        store.search([1.0, 0.0], top_k=0)


def test_cosine_zero_norm_raises():
    from aios_core.memory.vector import _cosine

    with pytest.raises(ValueError, match="non-zero norm"):
        _cosine([0.0, 0.0], [1.0, 0.0])
    with pytest.raises(ValueError, match="non-zero norm"):
        _cosine([1.0, 0.0], [0.0, 0.0])


def test_delete_idempotent_and_count(store):
    store.add("a", [1.0, 0.0])
    store.add("b", [0.0, 1.0])
    assert store.count() == 2
    store.delete("a")
    store.delete("a")  # idempotent
    assert store.count() == 1


def test_metadata_roundtrip(store):
    store.add("a", [1.0, 0.0], metadata={"source": "doc1", "n": 5})
    hits = store.search([1.0, 0.0])
    assert hits[0][2] == {"source": "doc1", "n": 5}


def test_tie_break_deterministic(store):
    store.add("a", [1.0, 0.0])
    store.add("b", [1.0, 0.0])  # same vector → same score
    hits = store.search([1.0, 0.0], top_k=2)
    assert hits[0][0] == "a"  # tie-break by id asc
