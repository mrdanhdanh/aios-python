"""State service tests."""

import copy

from aios_core.kernel.services import StateService


def test_set_get():
    svc = StateService()
    svc.set_state("e1", {"nodes": {"a": "pending"}})
    assert svc.get_state("e1")["nodes"]["a"] == "pending"


def test_get_returns_copy():
    svc = StateService()
    svc.set_state("e1", {"nodes": {"a": "pending"}})
    state = svc.get_state("e1")
    state["nodes"]["a"] = "completed"
    assert svc.get_state("e1")["nodes"]["a"] == "pending"  # original untouched


def test_update_state():
    svc = StateService()
    svc.update_state("e1", nodes={"a": "running"})
    svc.update_state("e1", results={"a": 42})
    state = svc.get_state("e1")
    assert state["nodes"]["a"] == "running"
    assert state["results"]["a"] == 42


def test_snapshot_deep_copy():
    svc = StateService()
    svc.set_state("e1", {"results": {"a": {"nested": [1, 2, 3]}}})
    snap = svc.snapshot("e1")
    snap["results"]["a"]["nested"].append(4)
    assert svc.get_state("e1")["results"]["a"]["nested"] == [1, 2, 3]


def test_snapshot_fallback_repr():
    import threading

    class NonCopyable:
        def __init__(self):
            self.lock = threading.Lock()  # not deep-copyable

    svc = StateService()
    svc.set_state("e1", {"results": {"a": NonCopyable()}})
    snap = svc.snapshot("e1")  # must not crash
    assert isinstance(snap["results"]["a"], str)  # repr fallback


def test_restore_replaces():
    svc = StateService()
    svc.set_state("e1", {"nodes": {"a": "pending"}})
    svc.restore("e1", {"nodes": {"b": "completed"}})
    assert svc.get_state("e1") == {"nodes": {"b": "completed"}}


def test_delete():
    svc = StateService()
    svc.set_state("e1", {})
    svc.delete("e1")
    assert svc.get_state("e1") is None


def test_missing_returns_none():
    svc = StateService()
    assert svc.get_state("nope") is None
    assert svc.snapshot("nope") == {}
