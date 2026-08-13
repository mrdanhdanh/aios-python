"""Chat + WebSocket + serve tests (AC4, AC11, AC12)."""

import threading

import pytest
from fastapi.testclient import TestClient

from aios_core.api import create_app
from aios_core.kernel.events import Event, EventType


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


def test_chat_coding_intent(client):
    r = client.post("/api/v1/chat", json={"text": "generate api for users"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["intent"] == "coding"
    assert data["status"] == "ok"
    assert "generated code" in data["response"]


def test_chat_with_intent_hint(client):
    r = client.post("/api/v1/chat", json={"text": "tôi đau đầu", "intent": "medical"})
    assert r.status_code == 200
    assert r.json()["data"]["intent"] == "medical"


def test_chat_empty_text_400(client):
    r = client.post("/api/v1/chat", json={"text": "   "})
    assert r.status_code == 200
    assert r.json()["error"]["code"] == "invalid_request"


def test_chat_extra_field_forbidden(client):
    r = client.post("/api/v1/chat", json={"text": "x", "bogus": 1})
    assert r.status_code == 422  # pydantic extra=forbid -> RequestValidationError


def test_ws_events_realtime(app, client):
    kernel = app.state.kernel
    with client.websocket_connect("/api/v1/events/ws") as ws:
        # Publish from another thread (cross-thread — C1-04 pattern).
        def _publish():
            kernel.bus.publish(
                Event(type=EventType.WORKFLOW_COMPLETED, payload={"wf": "x"}, source="test")
            )

        t = threading.Thread(target=_publish)
        t.start()
        t.join()
        msg = ws.receive_json()
        assert msg["type"] == "workflow.completed"
        assert msg["payload"] == {"wf": "x"}


def test_cli_serve_parser():
    from aios_core.workflow import cli

    with pytest.raises(SystemExit) as exc:
        cli.main(["serve", "--help"])
    assert exc.value.code == 0


def test_serve_run_importable():
    from aios_core.api import serve

    assert callable(serve.run)
