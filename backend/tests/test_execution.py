"""Execution service tests: topo, retry, timeout, cancel, resume, policy."""

import threading
import time

import pytest

from aios_core.config import ResourcesSettings
from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.execution_plan import ExecutionPlanBuilder
from aios_core.kernel.services import (
    EventService,
    ExecutionService,
    ExecutionStatus,
    Policy,
    PolicyService,
    ResourceService,
    StateService,
)


def make_plan(**overrides):
    data = {
        "id": "plan-test",
        "nodes": [
            {"id": "n1", "type": "task", "name": "first"},
            {"id": "n2", "type": "task", "name": "second", "depends_on": ["n1"]},
        ],
        "required_permissions": ["filesystem"],
    }
    data.update(overrides)
    return ExecutionPlanBuilder.from_dict(data)


@pytest.fixture
def svc(tmp_path):
    bus = EventBus()
    return ExecutionService(
        EventService(bus, tmp_path / "audit.db"),
        PolicyService(bus),
        StateService(),
        ResourceService(),
    )


def test_topo_order(svc):
    order = []
    plan = make_plan()
    result = svc.execute(
        plan,
        {"n1": lambda n, r: order.append("n1"), "n2": lambda n, r: order.append("n2")},
    )
    assert result.status == ExecutionStatus.COMPLETED
    assert order == ["n1", "n2"]
    assert set(result.node_results.keys()) == {"n1", "n2"}


def test_retry_success(svc):
    attempts = {"n": 0}

    def flaky(node, results):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("retry me")
        return "ok"

    plan = make_plan(nodes=[{"id": "n1", "type": "task", "name": "f", "retries": 2}])
    result = svc.execute(plan, {"n1": flaky})
    assert result.status == ExecutionStatus.COMPLETED
    assert result.node_results["n1"] == "ok"
    assert attempts["n"] == 3


def test_retry_exhausted_fail_fast(svc):
    ran = []
    plan = make_plan(
        nodes=[
            {"id": "bad", "type": "task", "name": "b", "retries": 1},
            {"id": "other", "type": "task", "name": "o"},
        ]
    )
    result = svc.execute(
        plan,
        {"bad": lambda n, r: (_ for _ in ()).throw(RuntimeError("always")), "other": lambda n, r: ran.append(1)},
    )
    assert result.status == ExecutionStatus.FAILED
    assert "bad" in result.reason
    assert ran == []  # fail-fast: independent node did not run


def test_timeout_is_retryable(svc):
    attempts = {"n": 0}

    def slow(node, results):
        attempts["n"] += 1
        time.sleep(0.2)  # longer than timeout
        return "late"

    plan = make_plan(
        nodes=[{"id": "n1", "type": "task", "name": "s", "timeout_s": 0.05, "retries": 1}]
    )
    result = svc.execute(plan, {"n1": slow})
    assert result.status == ExecutionStatus.FAILED
    assert attempts["n"] == 2  # both attempts timed out


def test_timeout_zero_no_timeout(svc):
    plan = make_plan(nodes=[{"id": "n1", "type": "task", "name": "f", "timeout_s": 0}])
    result = svc.execute(plan, {"n1": lambda n, r: "fast"})
    assert result.status == ExecutionStatus.COMPLETED


def test_cancel_between_nodes(svc):
    node1_done = threading.Event()
    release_node1 = threading.Event()
    node2_ran = []

    def n1(node, results):
        node1_done.set()
        release_node1.wait(2.0)  # hold node 1 until main thread cancels
        return "done1"

    plan = make_plan()
    t = threading.Thread(
        target=lambda: svc.execute(plan, {"n1": n1, "n2": lambda n, r: node2_ran.append(1)})
    )
    t.start()
    assert node1_done.wait(1.0)
    svc.cancel(plan.id)
    release_node1.set()
    t.join(2.0)
    assert node2_ran == []  # cancel flag set before node 2 ran


def test_cancel_before_execute_immediate(svc):
    plan = make_plan()
    svc.cancel(plan.id)  # cancel before execute
    ran = []
    result = svc.execute(plan, {"n1": lambda n, r: ran.append(1), "n2": lambda n, r: ran.append(2)})
    assert result.status == ExecutionStatus.CANCELLED
    assert result.reason == "cancelled"
    assert ran == []


def test_cancel_unknown_noop(svc):
    svc.cancel("nope")  # no error


def test_snapshot_resume(svc):
    plan = make_plan()
    order = []
    result = svc.execute(plan, {"n1": lambda n, r: order.append("n1") or "r1"})
    # node 2 has no runner → failed, but n1 completed + snapshot saved
    assert result.status == ExecutionStatus.FAILED
    assert "no runner" in result.reason

    # resume with a runner for node 2 only
    order2 = []
    result2 = svc.resume(plan.id, {"n2": lambda n, r: order2.append("n2") or "r2"})
    assert result2.status == ExecutionStatus.COMPLETED
    assert order2 == ["n2"]  # node 1 not re-run
    assert result2.node_results["n2"] == "r2"


def test_resume_plan_mismatch(svc):
    plan = make_plan()
    svc.execute(plan, {"n1": lambda n, r: "r1"})  # fail at n2 (no runner)
    other = make_plan(id="plan-other", nodes=[{"id": "x", "type": "task", "name": "x"}])
    svc.execute(other, {"x": lambda n, r: 1})
    result = svc.resume(other.id, {"x": lambda n, r: 2})
    # resume runs from snapshot; x already completed → skipped, ok
    assert result.status == ExecutionStatus.COMPLETED


def test_policy_deny(svc, tmp_path):
    bus = EventBus()
    policy = Policy(deny_scopes=["network"])
    execution = ExecutionService(
        EventService(bus, tmp_path / "a.db"),
        PolicyService(bus, policy),
        StateService(),
        ResourceService(),
    )
    ran = []
    plan = make_plan(required_permissions=["network"])
    result = execution.execute(plan, {"n1": lambda n, r: ran.append(1)})
    assert result.status == ExecutionStatus.FAILED
    assert "policy rejected" in result.reason
    assert ran == []


def test_approval_required_blocks(svc, tmp_path):
    bus = EventBus()
    execution = ExecutionService(
        EventService(bus, tmp_path / "a.db"),
        PolicyService(bus, Policy(require_approval=True)),
        StateService(),
        ResourceService(),
    )
    ran = []
    result = execution.execute(make_plan(), {"n1": lambda n, r: ran.append(1)})
    assert result.status == ExecutionStatus.FAILED
    assert "approval required" in result.reason
    assert ran == []


def test_resource_unavailable_and_release(tmp_path):
    bus = EventBus()
    resources = ResourceService(ResourcesSettings(max_tokens=10))
    execution = ExecutionService(
        EventService(bus, tmp_path / "a.db"),
        PolicyService(bus),
        StateService(),
        resources,
    )
    plan = make_plan(estimated_tokens=100)  # exceeds budget
    ran = []
    result = execution.execute(plan, {"n1": lambda n, r: ran.append(1)})
    assert result.status == ExecutionStatus.FAILED
    assert result.reason == "resource unavailable"
    assert ran == []
    assert resources.stats()["used_tokens"] == 0


def test_release_after_fail(tmp_path):
    bus = EventBus()
    resources = ResourceService(ResourcesSettings(max_tokens=100, max_concurrent=5))
    execution = ExecutionService(
        EventService(bus, tmp_path / "a.db"),
        PolicyService(bus),
        StateService(),
        resources,
    )
    plan = make_plan(estimated_tokens=50)
    result = execution.execute(plan, {"n1": lambda n, r: (_ for _ in ()).throw(RuntimeError("x"))})
    assert result.status == ExecutionStatus.FAILED
    stats = resources.stats()
    assert stats["used_tokens"] == 0
    assert stats["running"] == 0


def test_events_emitted(tmp_path):
    bus = EventBus()
    received = []
    for et in (EventType.WORKFLOW_STARTED, EventType.WORKFLOW_COMPLETED):
        bus.subscribe(et, lambda ev, received=received: received.append(ev))
    execution = ExecutionService(
        EventService(bus, tmp_path / "a.db"),
        PolicyService(bus),
        StateService(),
        ResourceService(),
    )
    result = execution.execute(make_plan(), {"n1": lambda n, r: 1, "n2": lambda n, r: 2})
    assert result.status == ExecutionStatus.COMPLETED
    assert [e.type for e in received] == [EventType.WORKFLOW_STARTED, EventType.WORKFLOW_COMPLETED]
    assert received[0].payload["execution_id"] == "plan-test"


def test_results_saved_in_state(svc):
    plan = make_plan()
    svc.execute(plan, {"n1": lambda n, r: "r1", "n2": lambda n, r: "r2"})
    state = svc._state.get_state("plan-test")  # noqa: SLF001
    assert state["results"] == {"n1": "r1", "n2": "r2"}
    assert state["nodes"]["n1"] == "completed"
