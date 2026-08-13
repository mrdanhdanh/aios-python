"""GoalReporter tests (TASK-022) — Goal Manager nâng cao."""

from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService
from aios_core.orchestrator.goals.goal import GoalManager, TaskStatus
from aios_core.orchestrator.goals.reporting import GoalReporter


def make_manager(tmp_path):
    bus = EventBus()
    return GoalManager(EventService(bus, tmp_path / "audit.db"), tmp_path / "goals.db")


def test_report_empty(tmp_path):
    reporter = GoalReporter(make_manager(tmp_path))
    report = reporter.report()
    assert report.total == 0
    assert report.by_status == {
        "active": 0, "paused": 0, "completed": 0, "failed": 0, "cancelled": 0,
    }
    assert report.avg_progress == 0.0
    assert report.completed_tasks == 0 and report.failed_tasks == 0


def test_report_status_and_progress(tmp_path):
    manager = make_manager(tmp_path)
    g1 = manager.create_goal("G1", tasks=[{"title": "t1", "workflow_name": "w1"}])
    g2 = manager.create_goal("G2", tasks=[
        {"title": "t1", "workflow_name": "w1"},
        {"title": "t2", "workflow_name": "w2"},
    ])
    task_id = g2.tasks[0].id
    manager.update_task_status(g2.id, task_id, TaskStatus.QUEUED)
    manager.update_task_status(g2.id, task_id, TaskStatus.RUNNING)
    manager.update_task_status(g2.id, task_id, TaskStatus.COMPLETED)  # → G2 progress 0.5

    reporter = GoalReporter(manager)
    report = reporter.report()
    assert report.total == 2
    assert report.by_status["active"] == 2
    assert report.completed_tasks == 1
    assert report.failed_tasks == 0
    assert report.avg_progress == 0.25  # (0 + 0.5) / 2
    assert {g["id"] for g in report.goals} == {g1.id, g2.id}
    assert all("task_count" in g for g in report.goals)


def test_report_failed_tasks_count(tmp_path):
    manager = make_manager(tmp_path)
    g = manager.create_goal("G", tasks=[
        {"title": "a", "workflow_name": "w1"},
        {"title": "b", "workflow_name": "w2"},
    ])
    task_id = g.tasks[0].id
    manager.update_task_status(g.id, task_id, TaskStatus.QUEUED)
    manager.update_task_status(g.id, task_id, TaskStatus.RUNNING)
    manager.update_task_status(g.id, task_id, TaskStatus.FAILED)
    report = GoalReporter(manager).report()
    assert report.failed_tasks == 1
    assert report.completed_tasks == 0


def test_report_goal_detail(tmp_path):
    manager = make_manager(tmp_path)
    g = manager.create_goal("G", tasks=[{"title": "t1", "workflow_name": "w1"}])
    detail = GoalReporter(manager).report_goal(g.id)
    assert detail is not None
    assert detail["id"] == g.id
    assert detail["status"] == "active"
    assert len(detail["tasks"]) == 1
    assert detail["tasks"][0]["workflow_name"] == "w1"


def test_report_goal_missing(tmp_path):
    assert GoalReporter(make_manager(tmp_path)).report_goal("ghost") is None


def test_deterministic_sort(tmp_path):
    manager = make_manager(tmp_path)
    manager.create_goal("B")
    manager.create_goal("A")
    report = GoalReporter(manager).report()
    ids = [g["id"] for g in report.goals]
    assert ids == sorted(ids)
