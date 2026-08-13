"""ExecutionSupervisor tests (TASK-022)."""

from datetime import datetime, timezone

from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.orchestrator.supervisor import ExecutionSupervisor


def _ev(type_, execution_id, plan_id="wf:a", ts=None):
    return Event(type=type_,
                 payload={"execution_id": execution_id, "plan_id": plan_id},
                 timestamp=ts or datetime.now(timezone.utc))


def test_tracks_running_and_finished(tmp_path):
    bus = EventBus()
    sup = ExecutionSupervisor(bus)
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e1"))
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e2"))
    bus.publish(_ev(EventType.WORKFLOW_COMPLETED, "e1"))
    snap = sup.snapshot()
    assert [r["execution_id"] for r in snap.running] == ["e2"]
    assert snap.recent_completed == 1
    assert snap.recent_failed == 0
    sup.close()


def test_failed_includes_cancelled(tmp_path):
    bus = EventBus()
    sup = ExecutionSupervisor(bus)
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e1"))
    bus.publish(_ev(EventType.WORKFLOW_FAILED, "e1"))
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e2"))
    bus.publish(_ev(EventType.WORKFLOW_CANCELLED, "e2"))
    snap = sup.snapshot()
    assert snap.recent_failed == 2  # FAILED + CANCELLED (R3-1)
    sup.close()


def test_stuck_detection_with_fake_clock(tmp_path):
    bus = EventBus()
    clock = iter([10.0, 20.0, 30.0])
    sup = ExecutionSupervisor(bus, stuck_after_s=5.0, clock=lambda: next(clock))
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e1"))   # clock 10
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e2"))   # clock 20
    snap = sup.snapshot()                                # clock 30
    # e1: 30 - 10 = 20 > 5 → stuck; e2: 30 - 20 = 10 > 5 → stuck
    assert len(snap.stuck) == 2
    sup.close()


def test_no_stuck_recent_start(tmp_path):
    bus = EventBus()
    clock = iter([10.0, 11.0, 12.0])
    sup = ExecutionSupervisor(bus, stuck_after_s=5.0, clock=lambda: next(clock))
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e1"))  # 10
    snap = sup.snapshot()                                 # 12 → 12-10=2 < 5
    assert snap.stuck == ()
    sup.close()


def test_queue_size_hook(tmp_path):
    bus = EventBus()
    sup = ExecutionSupervisor(bus, task_queue_count=lambda: 7)
    assert sup.snapshot().queue_size == 7
    sup.close()


def test_close_stops_tracking(tmp_path):
    bus = EventBus()
    sup = ExecutionSupervisor(bus)
    sup.close()
    bus.publish(_ev(EventType.WORKFLOW_STARTED, "e1"))
    snap = sup.snapshot()
    assert snap.running == ()
    assert snap.recent_completed == 0


def test_ignores_events_without_execution_id(tmp_path):
    bus = EventBus()
    sup = ExecutionSupervisor(bus)
    bus.publish(Event(type=EventType.WORKFLOW_STARTED, payload={}))
    assert sup.snapshot().running == ()
    sup.close()
