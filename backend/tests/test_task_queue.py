"""TaskQueue tests (AC4-6, AC11-queue, C1-03/04/16, C2-01/05/08/15)."""

import threading

import pytest

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService
from aios_core.orchestrator.goals import QueueItemStatus, TaskQueue
from aios_core.orchestrator.goals.errors import QueueError


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def event_service(bus, tmp_path):
    return EventService(bus, tmp_path / "audit.db")


@pytest.fixture
def queue(event_service, tmp_path):
    return TaskQueue(event_service=event_service, db_path=tmp_path / "goals.db")


def test_dequeue_priority_order(queue):
    queue.enqueue("low", priority=1)
    queue.enqueue("high", priority=5)
    queue.enqueue("mid", priority=3)
    assert queue.dequeue().workflow_name == "high"
    assert queue.dequeue().workflow_name == "mid"
    assert queue.dequeue().workflow_name == "low"
    assert queue.dequeue() is None


def test_dequeue_fifo_same_priority(queue):
    queue.enqueue("a", priority=1)
    queue.enqueue("b", priority=1)
    queue.enqueue("c", priority=1)
    assert queue.dequeue().workflow_name == "a"
    assert queue.dequeue().workflow_name == "b"
    assert queue.dequeue().workflow_name == "c"


def test_dequeue_empty_none(queue):
    assert queue.dequeue() is None


def test_concurrent_enqueue_unique_positions(queue):
    errors = []

    def _enqueue(n):
        try:
            queue.enqueue(f"wf-{n}", priority=0)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_enqueue, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    items = queue.list_items()
    positions = sorted(i.position for i in items)
    assert positions == list(range(8))  # UNIQUE(position) held — no duplicates


def test_pause_blocks_dequeue(queue):
    item = queue.enqueue("a")
    queue.pause(item.id)
    assert queue.dequeue() is None
    queue.resume(item.id)
    assert queue.dequeue().workflow_name == "a"


def test_resume_requeues(queue):
    item = queue.enqueue("a")
    queue.pause(item.id)
    queue.resume(item.id)
    assert queue.dequeue().workflow_name == "a"


def test_pause_running_raises(queue):
    item = queue.enqueue("a")
    queue.dequeue()  # -> running
    with pytest.raises(QueueError, match="invalid queue transition"):
        queue.pause(item.id)


def test_reorder_changes_order(queue):
    a = queue.enqueue("a", priority=1)
    b = queue.enqueue("b", priority=1)
    c = queue.enqueue("c", priority=1)
    queue.reorder([c.id, b.id, a.id])
    assert queue.dequeue().workflow_name == "c"
    assert queue.dequeue().workflow_name == "b"
    assert queue.dequeue().workflow_name == "a"


def test_reorder_unknown_id_raises(queue):
    a = queue.enqueue("a", priority=1)
    b = queue.enqueue("b", priority=1)
    with pytest.raises(QueueError, match="exactly all queued"):
        queue.reorder([a.id, "bogus"])


def test_reorder_incomplete_list_raises(queue):
    # C2-01: incomplete list -> QueueError, NOT sqlite IntegrityError.
    a = queue.enqueue("a", priority=1)
    queue.enqueue("b", priority=1)
    with pytest.raises(QueueError, match="exactly all queued"):
        queue.reorder([a.id])


def test_clear_only_queued(queue):
    queue.enqueue("a")
    running = queue.dequeue()
    queue.enqueue("b")
    cleared = queue.clear()
    assert cleared == 1  # only queued "b"
    items = queue.list_items()
    assert [i.workflow_name for i in items] == ["a"]
    assert running is not None and running.status == QueueItemStatus.RUNNING


def test_persist_across_instances(event_service, tmp_path):
    db_path = tmp_path / "goals.db"
    q1 = TaskQueue(event_service=event_service, db_path=db_path)
    q1.enqueue("wf", priority=3, payload={"x": [1, 2]})
    q2 = TaskQueue(event_service=event_service, db_path=db_path)  # new session
    item = q2.dequeue()
    assert item is not None
    assert item.workflow_name == "wf"
    assert item.payload == {"x": [1, 2]}  # payload round-trip (R6)


def test_dequeue_atomic_sets_running(queue):
    item = queue.enqueue("wf")
    got = queue.dequeue()
    assert got is not None and got.id == item.id and got.status == QueueItemStatus.RUNNING
    assert queue.dequeue() is None  # running item not re-dequeued


def test_no_double_dequeue(queue):
    a = queue.enqueue("a")
    queue.enqueue("b")
    first = queue.dequeue()
    second = queue.dequeue()
    assert first.id == a.id
    assert second.workflow_name == "b"  # atomic: no double-claim of same item


def test_recover_stale_running_on_init(event_service, tmp_path):
    # C1-03: running item older than threshold requeued on init (R4: emits recover).
    db_path = tmp_path / "goals.db"
    q1 = TaskQueue(event_service=event_service, db_path=db_path)
    item = q1.enqueue("wf")
    q1.dequeue()  # -> running
    # Manually age the item beyond threshold.
    import sqlite3
    from contextlib import closing

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "UPDATE queue_items SET updated_at='2020-01-01T00:00:00+00:00' WHERE id=?",
            (item.id,),
        )
    q2 = TaskQueue(event_service=event_service, db_path=db_path)  # init -> recover
    queued = q2.list_items(status=QueueItemStatus.QUEUED)
    assert [i.id for i in queued] == [item.id]  # requeued
    recovered = q2.dequeue()
    assert recovered is not None and recovered.id == item.id
    assert recovered.status == QueueItemStatus.RUNNING  # dequeue claims it again


def test_recover_stale_running_fresh_item_untouched(event_service, tmp_path):
    db_path = tmp_path / "goals.db"
    q1 = TaskQueue(event_service=event_service, db_path=db_path)
    item = q1.enqueue("wf")
    q1.dequeue()  # running, fresh
    q2 = TaskQueue(event_service=event_service, db_path=db_path)
    assert q2.dequeue() is None  # still running, not requeued


def test_enqueue_unknown_goal_id_accepted(queue):
    # C1-16: queue is decoupled — no validation of goal/task ids.
    item = queue.enqueue("wf", goal_id="no-such-goal", task_id="no-such-task")
    assert item.goal_id == "no-such-goal"


def test_queue_events_emitted(queue, bus, event_service):
    events = []
    bus.subscribe(None, events.append)
    a = queue.enqueue("a")
    queue.enqueue("b")
    queue.dequeue()
    actions = [e.payload["action"] for e in events if e.type == EventType.QUEUE_UPDATED]
    assert "enqueue" in actions and "dequeue" in actions
    # bulk: clear emits 1 aggregated event (C2-08)
    queue.clear()
    clear_events = [e for e in events if e.type == EventType.QUEUE_UPDATED and e.payload["action"] == "clear"]
    assert len(clear_events) == 1 and clear_events[0].payload["count"] == 1
    # fail path: pause running -> QueueError -> no QUEUE_UPDATED (C2-15)
    before = len(events)
    with pytest.raises(QueueError):
        queue.pause(a.id)  # a is running now
    assert len(events) == before
    # audit
    audit_types = {a.type.value for a in event_service.query_audit()}
    assert "queue.updated" in audit_types
