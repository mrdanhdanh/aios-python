"""API router tests (AC1-AC10, AC12)."""

import pytest
from fastapi.testclient import TestClient

from aios_core.api import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    from aios_core.config import Settings

    settings = Settings()
    settings.goals.db_path = str(tmp_path / "goals.db")
    settings.skills.db_path = str(tmp_path / "skills.db")
    settings.memory.conversation_db_path = str(tmp_path / "conv.db")
    settings.memory.knowledge_db_path = str(tmp_path / "knowledge.db")  # TASK-023
    settings.audit.db_path = str(tmp_path / "audit.db")
    monkeypatch.setenv("AIOS_CONFIG_PATH", str(tmp_path / "nonexistent.yaml"))
    return TestClient(create_app(settings))


def test_docs_ok(client):
    assert client.get("/docs").status_code == 200


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data["health_score"], float)
    assert isinstance(data["components"], list)


def test_events_list(client):
    r = client.get("/api/v1/events")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


def test_events_invalid_type(client):
    r = client.get("/api/v1/events?type=bogus")
    assert r.status_code == 200
    assert r.json()["error"]["code"] == "invalid_event_type"


def test_catalog_list_and_search(client):
    r = client.get("/api/v1/catalog")
    assert r.status_code == 200
    entries = r.json()["data"]
    assert len(entries) >= 10  # populated (C2-07)
    r2 = client.get("/api/v1/catalog/search?q=tool")
    assert r2.status_code == 200
    assert len(r2.json()["data"]) >= 6


def test_goals_list_and_detail(client):
    r = client.get("/api/v1/goals")
    assert r.status_code == 200
    assert r.json()["data"] == []
    r2 = client.get("/api/v1/goals/missing")
    assert r2.status_code == 404


def test_skills_list_and_detail(client):
    r = client.get("/api/v1/skills")
    assert r.status_code == 200
    assert r.json()["data"] == []
    r2 = client.get("/api/v1/skills/missing")
    assert r2.status_code == 404


def test_tools_list_and_detail(client):
    r = client.get("/api/v1/tools")
    assert r.status_code == 200
    tools = r.json()["data"]
    assert len(tools) == 6
    assert tools[0]["tool_type"] == "python"
    r2 = client.get("/api/v1/tools/tool.python")
    assert r2.status_code == 200
    assert r2.json()["data"]["capabilities"] == ["execute_code"]


def test_artifacts_and_conversations(client):
    r = client.get("/api/v1/artifacts")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
    r2 = client.get("/api/v1/conversations")
    assert r2.status_code == 200
    assert r2.json()["data"] == []


def test_prompts_list(client):
    r = client.get("/api/v1/prompts")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)


def test_models_list(client):
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    models = r.json()["data"]
    assert any(m["name"] == "mock" and m["available"] for m in models)


def test_sandbox_stats(client):
    r = client.get("/api/v1/sandbox")
    assert r.status_code == 200
    assert "max_size" in r.json()["data"]
