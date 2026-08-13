"""Execution failure events (TASK-021) — WORKFLOW_FAILED/CANCELLED emissions."""

from aios_core.kernel.events import EventBus, EventType
from aios_core.kernel.services import (
    EventService,
    ExecutionService,
    PolicyService,
    ResourceService,
    StateService,
)
from aios_core.kernel.services.policy import PolicyDecision, PolicyRequest

from test_execution import make_plan


def _svc(tmp_path, policy=None, bus=None):
    bus = bus or EventBus()
    return ExecutionService(
        EventService(bus, tmp_path / "audit.db"),
        policy or PolicyService(bus),
        StateService(),
        ResourceService(),
    )


def _collect(bus, types):
    received = []
    for et in types:
        bus.subscribe(et, lambda ev, received=received: received.append(ev))
    return received


def test_node_failure_emits_workflow_failed(tmp_path):
    bus = EventBus()
    received = _collect(bus, (EventType.WORKFLOW_FAILED,))
    execution = _svc(tmp_path, bus=bus)
    plan = make_plan()

    def boom(node, results):
        raise RuntimeError("node exploded")

    result = execution.execute(plan, {"n1": boom, "n2": lambda n, r: 2})
    assert result.status.value == "failed"
    assert len(received) == 1
    event = received[0]
    assert event.type == EventType.WORKFLOW_FAILED
    assert event.payload["execution_id"] == plan.id
    assert "node exploded" in event.payload["reason"]


def test_policy_rejected_emits_workflow_failed(tmp_path):
    bus = EventBus()
    received = _collect(bus, (EventType.WORKFLOW_FAILED,))

    class DenyPolicy(PolicyService):
        def evaluate(self, request: PolicyRequest) -> PolicyDecision:
            return PolicyDecision(
                approved=False, requires_approval=False, sandbox_required=False,
                reason="denied by test", policy_version="test",
            )

    execution = _svc(tmp_path, policy=DenyPolicy(bus), bus=bus)
    result = execution.execute(make_plan(), {"n1": lambda n, r: 1})
    assert result.status.value == "failed"
    assert len(received) == 1
    assert "denied by test" in received[0].payload["reason"]


def test_cancel_emits_workflow_cancelled(tmp_path):
    bus = EventBus()
    received = _collect(bus, (EventType.WORKFLOW_CANCELLED,))
    execution = _svc(tmp_path, bus=bus)
    plan = make_plan()
    execution.cancel(plan.id)
    result = execution.execute(plan, {"n1": lambda n, r: 1})
    # cancel-before-execute → NO event (execution never started)
    assert result.status.value == "cancelled"
    assert received == []


def test_resume_missing_state_no_event(tmp_path):
    bus = EventBus()
    received = _collect(bus, (EventType.WORKFLOW_FAILED, EventType.WORKFLOW_CANCELLED))
    execution = _svc(tmp_path, bus=bus)
    result = execution.resume("ghost", {"n1": lambda n, r: 1})
    assert result.status.value == "failed"
    assert received == []  # resume early-fail: no WORKFLOW_STARTED → no emit


def test_success_path_no_failed_events(tmp_path):
    bus = EventBus()
    received = _collect(bus, (EventType.WORKFLOW_FAILED, EventType.WORKFLOW_CANCELLED))
    execution = _svc(tmp_path, bus=bus)
    result = execution.execute(make_plan(), {"n1": lambda n, r: 1, "n2": lambda n, r: 2})
    assert result.status.value == "completed"
    assert received == []
