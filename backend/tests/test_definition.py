"""Workflow definition tests."""

import pytest
from pydantic import ValidationError

from aios_core.workflow import WorkflowDefinition, WorkflowNode


def defn(**overrides):
    data = {
        "name": "crud",
        "version": "1.0.0",
        "description": "CRUD API generator",
        "nodes": [
            {"id": "n1", "type": "task", "name": "first"},
            {"id": "n2", "type": "llm", "name": "second", "depends_on": ["n1"]},
        ],
        "permissions": ["filesystem"],
    }
    data.update(overrides)
    return WorkflowDefinition(**data)


def test_valid_definition():
    d = defn()
    assert d.name == "crud"
    assert len(d.nodes) == 2
    assert d.retries == 0
    assert d.timeout_s == 300.0


def test_version_invalid():
    with pytest.raises(ValidationError):
        defn(version="1.0")


def test_duplicate_node_id():
    data = defn().model_dump()
    data["nodes"][1]["id"] = "n1"
    with pytest.raises(ValidationError, match="unique"):
        WorkflowDefinition(**data)


def test_cycle_self():
    with pytest.raises(ValidationError, match="cycle"):
        defn(nodes=[{"id": "a", "type": "task", "name": "a", "depends_on": ["a"]}])


def test_unknown_permission_scope():
    with pytest.raises(ValidationError, match="permission"):
        defn(permissions=["not-a-scope"])


def test_name_empty_or_whitespace():
    with pytest.raises(ValidationError, match="name"):
        defn(name="   ")
    with pytest.raises(ValidationError, match="name"):
        defn(name="")


def test_unknown_dependency():
    with pytest.raises(ValidationError, match="unknown"):
        defn(nodes=[{"id": "a", "type": "task", "name": "a", "depends_on": ["ghost"]}])


def test_empty_nodes():
    with pytest.raises(ValidationError):
        defn(nodes=[])


def test_negative_values():
    with pytest.raises(ValidationError):
        defn(retries=-1)
    with pytest.raises(ValidationError):
        defn(timeout_s=-5)
    with pytest.raises(ValidationError):
        defn(nodes=[{"id": "a", "type": "task", "name": "a", "timeout_s": -1}])


def test_extra_key_forbidden():
    with pytest.raises(ValidationError, match="Extra"):
        defn(extra_key=True)
    with pytest.raises(ValidationError, match="Extra"):
        WorkflowNode(id="a", type="task", name="a", unexpected=1)


def test_edges_property():
    d = defn()
    assert d.edges == [("n1", "n2")]


def test_roundtrip_from_dict():
    d = defn()
    restored = WorkflowDefinition.from_dict(d.model_dump())
    assert restored.model_dump() == d.model_dump()


def test_from_yaml(tmp_path):
    yaml_path = tmp_path / "wf.yaml"
    yaml_path.write_text(
        "name: from-yaml\nversion: 0.1.0\nnodes:\n  - id: a\n    type: task\n    name: A\n",
        encoding="utf-8",
    )
    d = WorkflowDefinition.from_yaml(yaml_path)
    assert d.name == "from-yaml"
    assert d.nodes[0].id == "a"


def test_node_defaults():
    node = WorkflowNode(id="x", type="task", name="X")
    assert node.agent == ""
    assert node.capabilities == []
    assert node.depends_on == []
    assert node.timeout_s is None
    assert node.retries is None
