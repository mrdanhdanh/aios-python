"""TASK-068 — Kill Switch (M10-F3)."""

from __future__ import annotations

import pytest

from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.kernel.kill_switch import KillSwitch, KillSwitchError
from aios_core.kernel.services import (
    EventService,
    ExecutionService,
    PolicyService,
    ResourceService,
    StateService,
)
from aios_core.kernel.execution_plan import ExecutionPlanBuilder


def make_plan(execution_id="plan-ks"):
    return ExecutionPlanBuilder.from_dict({
        "id": execution_id,
        "nodes": [
            {"id": "n1", "type": "task", "name": "first"},
            {"id": "n2", "type": "task", "name": "second", "depends_on": ["n1"]},
        ],
        "required_permissions": ["filesystem"],
    })


def make_execution(tmp_path):
    bus = EventBus()
    return ExecutionService(
        EventService(bus, tmp_path / "audit.db"),
        PolicyService(bus),
        StateService(),
        ResourceService(),
    ), bus


# ---------------------------------------------------------------------------
# AC1: stop_execution → cancel
# ---------------------------------------------------------------------------

def test_stop_execution_cancels(tmp_path):
    svc, bus = make_execution(tmp_path)
    switch = KillSwitch(cancel_execution=svc.cancel)
    # cancel trước execute → CANCELLED ngay (cancel-before-execute semantics)
    switch.stop_execution("plan-ks")
    result = svc.execute(make_plan(), {"n1": lambda n, r: "a", "n2": lambda n, r: "b"})
    assert result.status.value == "cancelled"


def test_stop_execution_without_hook_raises():
    switch = KillSwitch()
    with pytest.raises(KillSwitchError):
        switch.stop_execution("x")


# ---------------------------------------------------------------------------
# AC2: stop_goal → cascade cancel
# ---------------------------------------------------------------------------

def test_stop_goal_cascade(tmp_path):
    from aios_core.orchestrator.goals import GoalManager

    gm = GoalManager(EventService(EventBus(), tmp_path / "audit2.db"),
                     tmp_path / "goals.db")
    goal = gm.create_goal("g1", tasks=[{"title": "t1", "workflow_name": "w"}])
    switch = KillSwitch(cancel_goal=gm.cancel_goal)
    switch.stop_goal(goal.id)
    # goal + tasks cascade cancelled
    g = gm.get_goal(goal.id)
    assert g.status.value == "cancelled"
    assert all(t.status.value == "cancelled" for t in g.tasks)


# ---------------------------------------------------------------------------
# AC3-AC7: emergency
# ---------------------------------------------------------------------------

def test_emergency_stop_state_and_event():
    events = []
    switch = KillSwitch(emit=lambda t, p: events.append((t, p)))
    state = switch.emergency_stop(running=["e1", "e2"])
    assert state.emergency is True
    assert state.reversible == ["e1", "e2"]
    assert events[0][0] == "emergency.stopped"
    assert events[0][1]["emergency"] is True


def test_emergency_blocks_new_execution():
    switch = KillSwitch()
    switch.emergency_stop()
    assert switch.preflight() is False
    assert switch.state.blocked_executions == 1
    assert switch.preflight() is False
    assert switch.state.blocked_executions == 2


def test_emergency_blocks_tool_calls():
    switch = KillSwitch()
    switch.emergency_stop()
    assert switch.preflight_tool() is False
    assert switch.state.blocked_tool_calls == 1


def test_release_restores():
    switch = KillSwitch(emit=lambda t, p: None)
    switch.emergency_stop()
    switch.release()
    assert switch.state.emergency is False
    assert switch.preflight() is True
    assert switch.preflight_tool() is True
    # release khi chưa emergency → no-op không lỗi
    switch.release()
    assert switch.state.released is True


def test_emergency_idempotent():
    events = []
    switch = KillSwitch(emit=lambda t, p: events.append(t))
    switch.emergency_stop()
    switch.emergency_stop()  # lần 2 no-op
    assert events == ["emergency.stopped"]


def test_cancel_pending_approvals():
    switch = KillSwitch()
    switch.emergency_stop()
    assert switch.cancel_pending_approvals() == 1
    assert switch.cancel_pending_approvals() == 2


def test_event_types_registered():
    assert EventType.EMERGENCY_STOPPED.value == "emergency.stopped"
    assert EventType.EMERGENCY_RELEASED.value == "emergency.released"


# ---------------------------------------------------------------------------
# AC8: CLI
# ---------------------------------------------------------------------------

def test_cli_status_and_emergency(capsys):
    from aios_core.workflow.cli import main

    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert '"emergency": false' in out


def test_cli_emergency_stop_then_block(capsys):
    """emergency-stop → execution mới bị chặn (gate preflight)."""
    from aios_core.kernel import RuntimeKernel
    from aios_core.kernel.kill_switch import KillSwitch

    kernel = RuntimeKernel.create()
    switch = kernel.container.resolve(KillSwitch)
    switch.emergency_stop()
    assert switch.preflight() is False
    assert switch.state.blocked_executions >= 1
    switch.release()  # dọn dẹp cho các test khác


# ---------------------------------------------------------------------------
# wiring
# ---------------------------------------------------------------------------

def test_kill_switch_wired_in_kernel():
    from aios_core.kernel import RuntimeKernel
    from aios_core.kernel.kill_switch import KillSwitch

    kernel = RuntimeKernel.create()
    switch = kernel.container.resolve(KillSwitch)
    assert switch is not None
    assert switch.preflight() is True  # không emergency mặc định
