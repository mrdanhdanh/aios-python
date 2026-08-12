"""Workflow compiler tests."""

import pytest

from aios_core.kernel.execution_plan import ExecutionPlanStatus
from aios_core.workflow import LangGraphCompiler, MockCompiler, WorkflowDefinition


def defn(**overrides):
    data = {
        "name": "wf-x",
        "version": "1.0.0",
        "nodes": [
            {"id": "n1", "type": "task", "name": "first"},
            {"id": "n2", "type": "llm", "name": "second", "depends_on": ["n1"]},
        ],
        "permissions": ["filesystem"],
        "resources": {"gpu": 1},
    }
    data.update(overrides)
    return WorkflowDefinition(**data)


def test_compile_mapping():
    plan = MockCompiler().compile(defn())
    assert plan.id == "wf:wf-x"
    assert plan.request_ref == "wf-x"
    assert len(plan.nodes) == 2
    assert plan.required_permissions == ["filesystem"]
    assert plan.required_resources == {"gpu": 1}
    assert plan.status == ExecutionPlanStatus.READY
    assert plan.created_at


def test_merge_defaults():
    d = defn(
        retries=2,
        timeout_s=60.0,
        nodes=[
            {"id": "a", "type": "task", "name": "A"},
            {"id": "b", "type": "task", "name": "B", "timeout_s": 5.0, "retries": 3},
        ],
    )
    plan = MockCompiler().compile(d)
    assert plan.nodes[0].retries == 2  # definition default
    assert plan.nodes[0].timeout_s == 60.0
    assert plan.nodes[1].retries == 3  # node override
    assert plan.nodes[1].timeout_s == 5.0


def test_merge_zero_preserved():
    # timeout_s=0 (no timeout) must NOT be overridden by definition default.
    d = defn(timeout_s=60.0, nodes=[{"id": "a", "type": "task", "name": "A", "timeout_s": 0.0}])
    plan = MockCompiler().compile(d)
    assert plan.nodes[0].timeout_s == 0.0
    # retries=0 (1 attempt) preserved too
    d2 = defn(retries=2, nodes=[{"id": "a", "type": "task", "name": "A", "retries": 0}])
    assert MockCompiler().compile(d2).nodes[0].retries == 0


def test_langgraph_stub():
    compiler = LangGraphCompiler()
    assert compiler.is_available() is False
    with pytest.raises(NotImplementedError):
        compiler.compile(defn())


def test_compile_output_runs_end_to_end(tmp_path):
    from aios_core.kernel import EventBus
    from aios_core.kernel.services import (
        EventService,
        ExecutionService,
        ExecutionStatus,
        PolicyService,
        ResourceService,
        StateService,
    )

    bus = EventBus()
    execution = ExecutionService(
        EventService(bus, str(tmp_path / "audit.db")),
        PolicyService(bus),
        StateService(),
        ResourceService(),
    )
    plan = MockCompiler().compile(defn(permissions=["filesystem"]))
    runner = {"n1": lambda n, r: "r1", "n2": lambda n, r: "r2"}
    result = execution.execute(plan, runner)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.node_results == {"n1": "r1", "n2": "r2"}
