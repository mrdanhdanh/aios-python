"""Workflow library tests."""

import threading

import pytest

from aios_core.workflow import WorkflowDefinition, WorkflowError, WorkflowLibrary


def defn(name="crud", description="CRUD API generator"):
    return WorkflowDefinition(
        name=name,
        version="1.0.0",
        description=description,
        nodes=[{"id": "a", "type": "task", "name": "A"}],
    )


def test_register_get_list():
    lib = WorkflowLibrary()
    lib.register(defn())
    lib.register(defn(name="doctor", description="medical"))
    assert lib.get("crud").name == "crud"
    assert lib.list() == ["crud", "doctor"]  # insertion order


def test_unknown_get_raises():
    lib = WorkflowLibrary()
    with pytest.raises(WorkflowError, match="Unknown workflow"):
        lib.get("nope")


def test_register_overwrite():
    lib = WorkflowLibrary()
    lib.register(defn())
    lib.register(defn(description="updated"))
    assert lib.get("crud").description == "updated"


def test_register_type_strict():
    lib = WorkflowLibrary()
    with pytest.raises(TypeError):
        lib.register({"name": "x"})  # not a WorkflowDefinition


def test_search():
    lib = WorkflowLibrary()
    lib.register(defn())
    lib.register(defn(name="data-pipeline", description="ETL and loading"))
    assert lib.search("CRUD") == ["crud"]  # case-insensitive
    assert lib.search("etl") == ["data-pipeline"]
    assert lib.search("") == []
    assert lib.search("   ") == []
    assert lib.search("nothing-here") == []


def test_promote_and_usage():
    lib = WorkflowLibrary()
    lib.register(defn())
    assert lib.promote("crud") == 1
    assert lib.promote("crud") == 2
    assert lib.usage("crud") == 2
    with pytest.raises(WorkflowError):
        lib.promote("ghost")
    with pytest.raises(WorkflowError):
        lib.usage("ghost")


def test_thread_safe():
    lib = WorkflowLibrary()
    lib.register(defn())
    errors: list[Exception] = []

    def worker():
        try:
            for _ in range(50):
                lib.register(defn(name="dup"))
                lib.search("crud")
                lib.promote("dup")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert lib.usage("dup") == 100
