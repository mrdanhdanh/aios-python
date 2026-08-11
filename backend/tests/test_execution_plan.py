"""Execution plan tests: build, validation, roundtrip."""

import copy

import pytest
from pydantic import ValidationError

from aios_core.kernel.execution_plan import (
    ExecutionPlan,
    ExecutionPlanBuilder,
    PlanNodeType,
)

VALID_DATA = {
    "id": "plan-1",
    "request_ref": "req-1",
    "nodes": [
        {
            "id": "n1",
            "type": "task",
            "name": "first",
            "capabilities": ["execute_code"],
            "timeout_s": 60,
            "retries": 1,
        },
        {
            "id": "n2",
            "type": "llm",
            "name": "second",
            "depends_on": ["n1"],
        },
    ],
    "estimated_cost": 1.5,
    "estimated_tokens": 5000,
    "required_permissions": ["filesystem"],
    "required_resources": {"gpu": 1},
}


def _data() -> dict:
    """Fresh deep copy of VALID_DATA (tests mutate nested lists)."""
    return copy.deepcopy(VALID_DATA)


def test_build_valid_plan():
    plan = ExecutionPlanBuilder.from_dict(_data())
    assert plan.id == "plan-1"
    assert len(plan.nodes) == 2
    assert plan.nodes[0].type == PlanNodeType.TASK
    assert plan.nodes[1].depends_on == ["n1"]
    assert plan.estimated_tokens == 5000


def test_duplicate_node_id_raises():
    data = _data()
    data["nodes"][1]["id"] = "n1"
    with pytest.raises(ValidationError, match="unique"):
        ExecutionPlanBuilder.from_dict(data)


def test_unknown_dependency_raises():
    data = _data()
    data["nodes"][1]["depends_on"] = ["nope"]
    with pytest.raises(ValidationError, match="unknown"):
        ExecutionPlanBuilder.from_dict(data)


def test_cycle_raises():
    data = _data()
    data["nodes"][1]["depends_on"] = ["n1"]
    data["nodes"][0]["depends_on"] = ["n2"]  # n1 -> n2 -> n1
    with pytest.raises(ValidationError, match="cycle"):
        ExecutionPlanBuilder.from_dict(data)


def test_self_dependency_raises():
    data = _data()
    data["nodes"][0]["depends_on"] = ["n1"]
    with pytest.raises(ValidationError, match="cycle"):
        ExecutionPlanBuilder.from_dict(data)


def test_empty_nodes_raises():
    data = _data()
    data["nodes"] = []
    with pytest.raises(ValidationError):
        ExecutionPlanBuilder.from_dict(data)


def test_negative_cost_raises():
    data = _data()
    data["estimated_cost"] = -1
    with pytest.raises(ValidationError):
        ExecutionPlanBuilder.from_dict(data)


def test_negative_tokens_raises():
    data = _data()
    data["estimated_tokens"] = -5
    with pytest.raises(ValidationError):
        ExecutionPlanBuilder.from_dict(data)


def test_extra_key_forbidden():
    data = _data()
    data["unexpected"] = True
    with pytest.raises(ValidationError, match="Extra"):
        ExecutionPlanBuilder.from_dict(data)


def test_roundtrip_equality():
    plan = ExecutionPlanBuilder.from_dict(_data())
    restored = ExecutionPlanBuilder.from_dict(plan.to_dict())
    assert restored.model_dump(mode="json") == plan.model_dump(mode="json")


def test_node_negative_timeout_raises():
    data = _data()
    data["nodes"][0]["timeout_s"] = -1
    with pytest.raises(ValidationError):
        ExecutionPlanBuilder.from_dict(data)
