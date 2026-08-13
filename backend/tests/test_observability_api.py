"""Observability API tests (TASK-021) — 5 GET + 1 POST feedback."""

from datetime import datetime, timezone

from aios_core.api.app import create_app
from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.observability.arch_health import ArchitectureHealth
from aios_core.observability.doctor import HealthDoctor
from aios_core.observability.evaluation import EvaluationStore
from aios_core.observability.metrics import MetricsService
from aios_core.observability.prompt_history import PromptHistory

from test_api import client  # noqa: F401 — reuse the app fixture pattern


def make_app(tmp_path, bus):
    """App with observability registries wired to a shared bus + tmp DBs."""
    from aios_core.healthcheck import HealthRegistry

    db = tmp_path / "obs.db"
    metrics = MetricsService(bus, str(db) + ".metrics")
    prompt_store = PromptHistory(str(db) + ".prompts")
    evals = EvaluationStore(bus, str(db) + ".evals")
    doctor = HealthDoctor(HealthRegistry(), diagnostics=[], metrics_summary=metrics.summary)
    app = create_app(registries={
        "observability": {
            "metrics": metrics,
            "prompt_history": prompt_store,
            "doctor": doctor,
            "arch_health": ArchitectureHealth(),
            "evaluations": evals,
        }
    })
    return app, metrics, prompt_store, evals


def test_metrics_endpoint(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, metrics, _, _ = make_app(tmp_path, bus)
    t0 = datetime.now(timezone.utc)
    bus.publish(Event(type=EventType.WORKFLOW_STARTED, payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_COMPLETED, payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))

    with TestClient(app) as tc:
        resp = tc.get("/api/v1/observability/metrics")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["counts"]["workflow"] == 1
        assert "total" in data and "tool_failures" in data
    metrics.close()


def test_prompt_history_endpoint(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, _, prompt_store, _ = make_app(tmp_path, bus)
    prompt_store.record("explain", "1.0.0", {"code": "x"}, "out")

    with TestClient(app) as tc:
        resp = tc.get("/api/v1/observability/prompt-history")
        assert resp.status_code == 200
        records = resp.json()["data"]["records"]
        assert len(records) == 1 and records[0]["prompt_id"] == "explain"


def test_doctor_endpoint(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, _, _, _ = make_app(tmp_path, bus)
    with TestClient(app) as tc:
        resp = tc.get("/api/v1/observability/doctor")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "status" in data and "checks" in data and "diagnostics" in data


def test_arch_health_endpoint(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, _, _, _ = make_app(tmp_path, bus)
    with TestClient(app) as tc:
        resp = tc.get("/api/v1/observability/arch-health")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "healthy" in data and "violations" in data


def test_evaluations_get_and_feedback(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, _, _, evals = make_app(tmp_path, bus)
    t0 = datetime.now(timezone.utc)
    bus.publish(Event(type=EventType.WORKFLOW_STARTED, payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_COMPLETED, payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))

    with TestClient(app) as tc:
        resp = tc.get("/api/v1/observability/evaluations")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["evaluations"]) == 1
        assert data["evaluations"][0]["quality"] is None

        fb = tc.post("/api/v1/observability/evaluations/e1/feedback",
                     json={"quality": 0.8, "feedback": "good"})
        assert fb.status_code == 200
        assert fb.json()["data"]["quality"] == 0.8

        after = tc.get("/api/v1/observability/evaluations")
        assert after.json()["data"]["evaluations"][0]["quality"] == 0.8
        assert after.json()["data"]["average_quality"] == 0.8
    evals.close()


def test_feedback_404_when_no_row(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, _, _, _ = make_app(tmp_path, bus)
    with TestClient(app) as tc:
        resp = tc.post("/api/v1/observability/evaluations/ghost/feedback",
                       json={"quality": 0.5})
        assert resp.status_code == 404


def test_feedback_invalid_quality(tmp_path):
    from fastapi.testclient import TestClient

    bus = EventBus()
    app, _, _, _ = make_app(tmp_path, bus)
    with TestClient(app) as tc:
        resp = tc.post("/api/v1/observability/evaluations/ghost/feedback",
                       json={"quality": 5.0})
        assert resp.status_code == 422
