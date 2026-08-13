"""Orchestrator v2 API tests (TASK-022) — 4 endpoints."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from aios_core.api.app import create_app
from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.kernel.services import EventService
from aios_core.observability.evaluation import EvaluationStore
from aios_core.observability.metrics import MetricsService
from aios_core.observability.prompt_history import PromptHistory
from aios_core.orchestrator.advisor import ImprovementAdvisor
from aios_core.orchestrator.evaluation_collector import EvaluationCollector
from aios_core.orchestrator.goals.goal import GoalManager, TaskStatus
from aios_core.orchestrator.goals.reporting import GoalReporter
from aios_core.orchestrator.supervisor import ExecutionSupervisor


def make_app(tmp_path, bus):
    db = tmp_path / "obs.db"
    metrics = MetricsService(bus, str(db) + ".metrics")
    evals = EvaluationStore(bus, str(db) + ".evals")
    prompts = PromptHistory(str(db) + ".prompts")
    goals = GoalManager(EventService(bus, tmp_path / "audit.db"), tmp_path / "goals.db")
    app = create_app(registries={
        "observability": {
            "metrics": metrics,
            "prompt_history": prompts,
            "evaluations": evals,
        },
        "goals": goals,
        "orchestrator_v2": {
            "advisor": ImprovementAdvisor(evals, metrics, prompts),
            "supervisor": ExecutionSupervisor(bus, task_queue_count=lambda: 3),
            "collector": EvaluationCollector(evals),
            "goal_reporter": GoalReporter(goals),
        },
    })
    return app, metrics, evals, goals


def _run_workflow(bus, execution_id, plan_id, t0):
    bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                      payload={"execution_id": execution_id, "plan_id": plan_id}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_COMPLETED,
                      payload={"execution_id": execution_id, "plan_id": plan_id}, timestamp=t0))


def test_advisor_suggestions_endpoint(tmp_path):
    bus = EventBus()
    app, _, evals, _ = make_app(tmp_path, bus)
    t0 = datetime.now(timezone.utc)
    _run_workflow(bus, "e1", "wf:bad", t0)
    _run_workflow(bus, "e2", "wf:bad", t0)
    evals.evaluate("e1", 0.2, "")
    evals.evaluate("e2", 0.1, "")

    with TestClient(app) as tc:
        resp = tc.get("/api/v1/orchestrator-v2/advisor/suggestions")
        assert resp.status_code == 200
        suggestions = resp.json()["data"]["suggestions"]
        assert any(s["kind"] == "workflow" and s["target"] == "wf:bad" for s in suggestions)


def test_supervisor_snapshot_endpoint(tmp_path):
    bus = EventBus()
    app, _, _, _ = make_app(tmp_path, bus)
    t0 = datetime.now(timezone.utc)
    bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                      payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))

    with TestClient(app) as tc:
        resp = tc.get("/api/v1/orchestrator-v2/supervisor/snapshot")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert [r["execution_id"] for r in data["running"]] == ["e1"]
        assert data["queue_size"] == 3


def test_goals_report_endpoint(tmp_path):
    bus = EventBus()
    app, _, _, goals = make_app(tmp_path, bus)
    g = goals.create_goal("G", tasks=[{"title": "t1", "workflow_name": "w1"}])
    task_id = g.tasks[0].id
    goals.update_task_status(g.id, task_id, TaskStatus.QUEUED)
    goals.update_task_status(g.id, task_id, TaskStatus.RUNNING)
    goals.update_task_status(g.id, task_id, TaskStatus.COMPLETED)

    with TestClient(app) as tc:
        resp = tc.get("/api/v1/orchestrator-v2/goals/report")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["by_status"]["completed"] == 1  # goal auto-completed khi mọi task xong
        assert data["completed_tasks"] == 1


def test_goal_report_detail_endpoint(tmp_path):
    bus = EventBus()
    app, _, _, goals = make_app(tmp_path, bus)
    g = goals.create_goal("G")

    with TestClient(app) as tc:
        resp = tc.get(f"/api/v1/orchestrator-v2/goals/{g.id}/report")
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "G"

        missing = tc.get("/api/v1/orchestrator-v2/goals/ghost/report")
        assert missing.status_code == 404
