"""GoalManager tests (AC1-3, AC11-goal, C2-10/11/13)."""

import pytest

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService
from aios_core.orchestrator.goals import GoalError, GoalManager, GoalStatus, TaskStatus, TaskQueue
from aios_core.orchestrator.goals.errors import QueueError


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def event_service(bus, tmp_path):
    return EventService(bus, tmp_path / "audit.db")


@pytest.fixture
def manager(event_service, tmp_path):
    return GoalManager(event_service=event_service, db_path=tmp_path / "goals.db")


def _mk_goal(manager: GoalManager):
    return manager.create_goal(
        "Xây AIOS",
        description="milestone",
        tasks=[
            {"title": "t1", "workflow_name": "wf_a", "priority": 1},
            {"title": "t2", "workflow_name": "wf_b"},
            {"title": "t3", "workflow_name": "wf_c"},
        ],
    )


def _complete_task(manager: GoalManager, goal_id: str, task_id: str, result: str = "ok"):
    """Walk the valid state chain pending->queued->running->completed."""
    manager.update_task_status(goal_id, task_id, TaskStatus.QUEUED)
    manager.update_task_status(goal_id, task_id, TaskStatus.RUNNING)
    manager.update_task_status(goal_id, task_id, TaskStatus.COMPLETED, result=result)


def _fail_task(manager: GoalManager, goal_id: str, task_id: str):
    manager.update_task_status(goal_id, task_id, TaskStatus.QUEUED)
    manager.update_task_status(goal_id, task_id, TaskStatus.RUNNING)
    manager.update_task_status(goal_id, task_id, TaskStatus.FAILED)


def test_create_goal_with_tasks_and_get(manager):
    goal = _mk_goal(manager)
    assert goal.status == GoalStatus.ACTIVE
    assert len(goal.tasks) == 3
    assert [t.workflow_name for t in goal.tasks] == ["wf_a", "wf_b", "wf_c"]  # position order (C2-02)
    assert [t.position for t in goal.tasks] == [0, 1, 2]
    assert goal.tasks[0].priority == 1
    fetched = manager.get_goal(goal.id)
    assert fetched is not None
    assert fetched.title == "Xây AIOS"


def test_persist_across_instances(event_service, tmp_path):
    db_path = tmp_path / "goals.db"
    m1 = GoalManager(event_service=event_service, db_path=db_path)
    goal = m1.create_goal("g", tasks=[{"title": "t", "workflow_name": "wf"}])
    _complete_task(m1, goal.id, goal.tasks[0].id)
    m2 = GoalManager(event_service=event_service, db_path=db_path)  # new session
    fetched = m2.get_goal(goal.id)
    assert fetched is not None
    assert fetched.status == GoalStatus.COMPLETED
    assert fetched.tasks[0].status == TaskStatus.COMPLETED


def test_progress_recompute(manager):
    goal = _mk_goal(manager)
    assert manager.progress(goal.id) == pytest.approx(0.0)
    _complete_task(manager, goal.id, goal.tasks[0].id)
    assert manager.progress(goal.id) == pytest.approx(1 / 3)
    _complete_task(manager, goal.id, goal.tasks[1].id)
    assert manager.progress(goal.id) == pytest.approx(2 / 3)
    _complete_task(manager, goal.id, goal.tasks[2].id)
    assert manager.progress(goal.id) == pytest.approx(1.0)


def test_auto_completed(manager):
    goal = _mk_goal(manager)
    for task in goal.tasks:
        _complete_task(manager, goal.id, task.id)
    assert manager.get_goal(goal.id).status == GoalStatus.COMPLETED


def test_auto_failed(manager):
    goal = _mk_goal(manager)
    _fail_task(manager, goal.id, goal.tasks[0].id)
    assert manager.get_goal(goal.id).status == GoalStatus.FAILED


def test_paused_goal_not_auto_changed(manager):
    goal = _mk_goal(manager)
    manager.pause_goal(goal.id)
    _fail_task(manager, goal.id, goal.tasks[0].id)
    assert manager.get_goal(goal.id).status == GoalStatus.PAUSED


def test_resume_goal_recomputes_auto_status(manager):
    # C2-11: tasks completed while paused -> resume flips goal to completed.
    goal = _mk_goal(manager)
    manager.pause_goal(goal.id)
    for task in goal.tasks:
        _complete_task(manager, goal.id, task.id)
    assert manager.get_goal(goal.id).status == GoalStatus.PAUSED
    manager.resume_goal(goal.id)
    assert manager.get_goal(goal.id).status == GoalStatus.COMPLETED


def test_pause_resume_cancel_flow(manager):
    goal = _mk_goal(manager)
    paused = manager.pause_goal(goal.id)
    assert paused.status == GoalStatus.PAUSED
    resumed = manager.resume_goal(goal.id)
    assert resumed.status == GoalStatus.ACTIVE
    cancelled = manager.cancel_goal(goal.id)
    assert cancelled.status == GoalStatus.CANCELLED


def test_invalid_transition_raises(manager):
    goal = _mk_goal(manager)
    with pytest.raises(GoalError, match="invalid task transition"):
        manager.update_task_status(goal.id, goal.tasks[0].id, TaskStatus.RUNNING)  # pending->running
    manager.pause_goal(goal.id)
    manager.resume_goal(goal.id)  # paused->active is VALID
    manager.cancel_goal(goal.id)
    with pytest.raises(GoalError, match="invalid goal transition"):
        manager.cancel_goal(goal.id)  # cancelled is terminal
    with pytest.raises(GoalError, match="goal not found"):
        manager.progress("nope")  # C2-13


def test_goal_task_not_found_raises(manager):
    with pytest.raises(GoalError, match="goal not found"):
        manager.add_task("missing", "t", "wf")


def test_add_task_on_terminal_goal_raises(manager):
    goal = _mk_goal(manager)
    manager.cancel_goal(goal.id)
    with pytest.raises(GoalError, match="goal is terminal"):
        manager.add_task(goal.id, "t4", "wf_d")


def test_update_task_mismatch_goal_raises(manager):
    g1 = _mk_goal(manager)
    g2 = manager.create_goal("g2", tasks=[{"title": "x", "workflow_name": "wf"}])
    with pytest.raises(GoalError, match="not in goal"):
        manager.update_task_status(g2.id, g1.tasks[0].id, TaskStatus.QUEUED)


def test_cancel_goal_cascades_queue_items(event_service, tmp_path):
    # C1-02: queued queue items of the goal -> cancelled (same transaction).
    db_path = tmp_path / "goals.db"
    gm = GoalManager(event_service=event_service, db_path=db_path)
    tq = TaskQueue(event_service=event_service, db_path=db_path)
    goal = gm.create_goal("g", tasks=[{"title": "t", "workflow_name": "wf"}])
    tq.enqueue("wf", goal_id=goal.id)
    tq.enqueue("wf_other", goal_id="other-goal")
    gm.cancel_goal(goal.id)
    items = tq.list_items()
    by_goal = {i.goal_id: i.status.value for i in items}
    assert by_goal[goal.id] == "cancelled"
    assert by_goal["other-goal"] == "queued"  # unrelated goal untouched


def test_cancel_goal_cascades_tasks(manager):
    # R5: non-terminal tasks -> cancelled.
    goal = _mk_goal(manager)
    _complete_task(manager, goal.id, goal.tasks[0].id)
    manager.cancel_goal(goal.id)
    fetched = manager.get_goal(goal.id)
    statuses = {t.title: t.status for t in fetched.tasks}
    assert statuses["t1"] == TaskStatus.COMPLETED  # terminal untouched
    assert statuses["t2"] == TaskStatus.CANCELLED


def test_goal_events_emitted(manager, bus, event_service):
    bus_events = []
    bus.subscribe(None, bus_events.append)
    goal = manager.create_goal("g", tasks=[{"title": "t", "workflow_name": "wf"}])
    _complete_task(manager, goal.id, goal.tasks[0].id)
    types = {e.type for e in bus_events}
    assert EventType.GOAL_CREATED in types
    assert EventType.GOAL_TASK_UPDATED in types
    assert EventType.GOAL_STATUS_CHANGED in types  # auto completed (C2-15)
    # fail path emits nothing (C1-15): transition invalid -> no GOAL_TASK_UPDATED
    before = len(bus_events)
    with pytest.raises(GoalError):
        manager.update_task_status(goal.id, goal.tasks[0].id, TaskStatus.QUEUED)  # completed->queued invalid
    assert len(bus_events) == before
    # audit has records (Event objects)
    audit = event_service.query_audit()
    audit_types = {a.type.value for a in audit}
    assert "goal.created" in audit_types and "goal.task_updated" in audit_types


def test_choreography_enqueue_to_complete(event_service, tmp_path):
    # C2-10: enqueue -> update QUEUED -> dequeue -> update RUNNING -> completed.
    db_path = tmp_path / "goals.db"
    gm = GoalManager(event_service=event_service, db_path=db_path)
    tq = TaskQueue(event_service=event_service, db_path=db_path)
    goal = gm.create_goal("g", tasks=[{"title": "t", "workflow_name": "wf"}])
    task = goal.tasks[0]
    tq.enqueue("wf", task_id=task.id, goal_id=goal.id)
    gm.update_task_status(goal.id, task.id, TaskStatus.QUEUED)
    item = tq.dequeue()
    assert item is not None
    gm.update_task_status(goal.id, task.id, TaskStatus.RUNNING)
    gm.update_task_status(goal.id, task.id, TaskStatus.COMPLETED, result="ok")
    assert gm.get_goal(goal.id).status == GoalStatus.COMPLETED


def test_list_goals_filter_status_limit(manager):
    _mk_goal(manager)
    manager.create_goal("g2")
    completed = manager.list_goals(status=GoalStatus.ACTIVE, limit=1)
    assert len(completed) == 1
    assert len(manager.list_goals()) == 2
    assert manager.list_goals(status=GoalStatus.COMPLETED) == []


def test_empty_title_raises(manager):
    with pytest.raises(GoalError, match="title"):
        manager.create_goal("")
