"""TASK-072 — M10 API: overview + timeline (Dashboard 1.0)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from aios_core.api.app import create_app

    return TestClient(create_app())


def test_overview_shape(client):
    resp = client.get("/api/v1/m10/overview")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "health_score" in data
    assert "slo_release_ready" in data
    assert "security_blocking" in data
    assert "contract_breaking" in data


def test_overview_values(client):
    resp = client.get("/api/v1/m10/overview")
    data = resp.json()["data"]
    assert 0 <= data["health_score"] <= 100
    assert isinstance(data["slo_release_ready"], bool)
    assert isinstance(data["security_blocking"], bool)
    assert data["contract_breaking"] == 0  # Contract 1.0 frozen


def test_timeline_empty_db(client):
    resp = client.get("/api/v1/m10/timeline")
    assert resp.status_code == 200
    assert "data" in resp.json()
    assert isinstance(resp.json()["data"], list)


def test_timeline_with_data(client):
    # inject metrics rows qua observability registry
    app = client.app
    metrics_svc = app.state.registries["observability"]["metrics"]
    from aios_core.kernel.events import Event, EventType

    metrics_svc._on_event(Event(
        type=EventType.WORKFLOW_STARTED,
        payload={"execution_id": "e1", "plan_id": "p1"}, source="t",
    ))
    metrics_svc._on_event(Event(
        type=EventType.WORKFLOW_COMPLETED,
        payload={"execution_id": "e1", "plan_id": "p1"}, source="t",
    ))
    resp = client.get("/api/v1/m10/timeline")
    data = resp.json()["data"]
    assert len(data) >= 2
    # steps sort theo ts/seq
    seqs = [s["seq"] for s in data]
    assert seqs == sorted(seqs)


def test_timeline_limit(client):
    resp = client.get("/api/v1/m10/timeline?limit=5")
    assert resp.status_code == 200
