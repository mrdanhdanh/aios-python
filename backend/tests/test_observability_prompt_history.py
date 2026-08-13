"""PromptHistory tests (TASK-021)."""

from aios_core.observability.prompt_history import PromptHistory


def test_record_and_list(tmp_path):
    store = PromptHistory(tmp_path / "ph.db")
    rid = store.record("explain", "1.0.0", {"code": "x=1"}, "explained")
    assert rid > 0
    records = store.list()
    assert len(records) == 1
    assert records[0].prompt_id == "explain"
    assert records[0].version == "1.0.0"
    assert records[0].variables == {"code": "x=1"}
    assert records[0].output == "explained"
    assert store.count() == 1


def test_list_filter_and_limit(tmp_path):
    store = PromptHistory(tmp_path / "ph.db")
    store.record("a", "1.0.0", {}, "o1")
    store.record("b", "1.0.0", {}, "o2")
    store.record("a", "1.1.0", {}, "o3")
    only_a = store.list(prompt_id="a")
    assert [r.output for r in only_a] == ["o3", "o1"]
    limited = store.list(limit=2)
    assert len(limited) == 2


def test_variables_fidelity_sorted(tmp_path):
    store = PromptHistory(tmp_path / "ph.db")
    store.record("p", "1.0.0", {"z": 1, "a": {"n": [1, 2]}, "b": None}, "out")
    r = store.list()[0]
    assert r.variables == {"z": 1, "a": {"n": [1, 2]}, "b": None}


def test_persist_across_instances(tmp_path):
    db = tmp_path / "ph.db"
    PromptHistory(db).record("p", "1.0.0", {"x": 1}, "out")
    store2 = PromptHistory(db)
    assert store2.count() == 1
    assert store2.list()[0].prompt_id == "p"
