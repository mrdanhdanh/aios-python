"""MetricsService tests (TASK-021)."""

from datetime import datetime, timedelta, timezone

from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.observability.metrics import MetricsService


def make_event(type_: EventType, execution_id: str, ts: datetime, **extra):
    payload = {"execution_id": execution_id, **extra}
    return Event(type=type_, payload=payload, timestamp=ts)


def test_counts_and_duration(tmp_path):
    bus = EventBus()
    svc = MetricsService(bus, tmp_path / "metrics.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(
        make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=2), plan_id="wf:a")
    )
    assert svc.counts() == {"workflow": 1, "tool": 0}
    assert svc.average_duration("workflow") == 2000.0
    assert svc.summary()["total"] == 1
    assert svc.summary()["counts"]["workflow"] == 1
    svc.close()


def test_tool_metrics_and_failures(tmp_path):
    bus = EventBus()
    svc = MetricsService(bus, tmp_path / "metrics.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.TOOL_STARTED, "e1", t0, node_id="n1", node_name="run"))
    bus.publish(make_event(EventType.TOOL_FINISHED, "e1", t0 + timedelta(milliseconds=500),
                           node_id="n1", node_name="run", ok=False))
    assert svc.counts()["tool"] == 1
    assert svc.tool_failures() == 1
    slowest = svc.slowest("tool")
    assert len(slowest) == 1 and slowest[0]["name"] == "run"
    svc.close()


def test_orphan_start_duration_null(tmp_path):
    bus = EventBus()
    svc = MetricsService(bus, tmp_path / "metrics.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    # no finish → orphan
    assert svc.average_duration("workflow") is None
    assert svc.counts()["workflow"] == 1
    svc.close()


def test_rerun_updates_latest_row(tmp_path):
    """Re-run cùng execution_id → chỉ row mới nhất được finish (P2-2)."""
    bus = EventBus()
    svc = MetricsService(bus, tmp_path / "metrics.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    # run 1 fails
    bus.publish(make_event(EventType.WORKFLOW_FAILED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    # run 2 starts again
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0 + timedelta(seconds=2), plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=3), plan_id="wf:a"))
    assert svc.counts()["workflow"] == 2
    recent = svc.recent()
    # row 2 finished (3s - 2s = 1s), row 1 finished (1s)
    durations = sorted(r["duration_ms"] for r in recent if r["duration_ms"] is not None)
    assert durations == [1000.0, 1000.0]
    svc.close()


def test_ignores_untracked_events(tmp_path):
    bus = EventBus()
    svc = MetricsService(bus, tmp_path / "metrics.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.SNAPSHOT_SAVED, "e1", t0))
    bus.publish(make_event(EventType.AGENT_STARTED, "e1", t0))
    assert svc.counts() == {"workflow": 0, "tool": 0}
    svc.close()


def test_persist_across_instances(tmp_path):
    bus = EventBus()
    db = tmp_path / "metrics.db"
    svc1 = MetricsService(bus, db)
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    svc1.close()

    svc2 = MetricsService(bus, db)
    assert svc2.counts()["workflow"] == 1
    assert svc2.average_duration("workflow") == 1000.0
    svc2.close()


def test_close_unsubscribes(tmp_path):
    bus = EventBus()
    svc = MetricsService(bus, tmp_path / "metrics.db")
    svc.close()
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    assert svc.counts()["workflow"] == 0
