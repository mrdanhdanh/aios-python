"""EvaluationStore tests (TASK-021)."""

from datetime import datetime, timedelta, timezone

import pytest

from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.observability.evaluation import EvaluationStore


def make_event(type_: EventType, execution_id: str, ts: datetime, **extra):
    return Event(type=type_, payload={"execution_id": execution_id, **extra}, timestamp=ts)


def test_auto_record_completed(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    rows = store.list()
    assert len(rows) == 1
    assert rows[0].success is True
    assert rows[0].workflow_id == "wf:a"
    assert rows[0].duration_ms == 1000.0
    assert store.counts() == {"success": 1, "failed": 0, "total": 1}
    store.close()


def test_auto_record_failed_and_cancelled(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_FAILED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e2", t0, plan_id="wf:b"))
    bus.publish(make_event(EventType.WORKFLOW_CANCELLED, "e2", t0 + timedelta(seconds=2), plan_id="wf:b"))
    assert store.counts() == {"success": 0, "failed": 2, "total": 2}
    assert all(not r.success for r in store.list())
    store.close()


def test_orphan_finish_duration_null(tmp_path):
    """Finish không có STARTED trước đó (restart) → duration NULL."""
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0, plan_id="wf:a"))
    rows = store.list()
    assert rows[0].duration_ms is None
    store.close()


def test_evaluate_attaches_quality(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    store.evaluate("e1", 0.9, "great")
    rows = store.list()
    assert rows[0].quality == 0.9
    assert rows[0].feedback == "great"
    assert store.average_quality() == 0.9
    assert store.average_quality("wf:a") == 0.9
    assert store.average_quality("other") is None
    store.close()


def test_evaluate_missing_row_raises(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    with pytest.raises(KeyError):
        store.evaluate("ghost", 0.5)
    store.close()


def test_average_quality_none_when_no_rows(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    assert store.average_quality() is None
    store.close()


def test_persist_across_instances(tmp_path):
    bus = EventBus()
    db = tmp_path / "evals.db"
    store1 = EvaluationStore(bus, db)
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    store1.close()

    store2 = EvaluationStore(bus, db)
    assert store2.counts()["total"] == 1
    store2.close()


def test_list_filter_by_workflow(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "evals.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e1", t0, plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e1", t0 + timedelta(seconds=1), plan_id="wf:a"))
    bus.publish(make_event(EventType.WORKFLOW_STARTED, "e2", t0, plan_id="wf:b"))
    bus.publish(make_event(EventType.WORKFLOW_COMPLETED, "e2", t0 + timedelta(seconds=1), plan_id="wf:b"))
    assert len(store.list(workflow_id="wf:a")) == 1
    assert len(store.list(workflow_id="nope")) == 0
    store.close()
