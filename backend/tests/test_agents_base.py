"""Base assistant contract tests (AC1-part, AC2, AC3)."""

import pytest

from aios_core.agents import (
    Assistant,
    AssistantRequest,
    AssistantResponse,
    GeneralAssistant,
)
from aios_core.models import MockModel


class DummyAssistant(Assistant):
    name = "dummy"
    intent = "chat"
    description = "test assistant"

    def __init__(self, event_sink=None, raise_process=False):
        super().__init__(event_sink=event_sink)
        self._raise_process = raise_process

    def _process(self, request):
        if self._raise_process:
            raise RuntimeError("boom")
        return AssistantResponse(text=f"ok:{request.text}", intent=self.intent)


def test_empty_text_returns_error_without_events():
    events = []
    assistant = DummyAssistant(event_sink=lambda t, p: events.append((t, p)))
    response = assistant.handle(AssistantRequest(text="   "))
    assert response.status == "error"
    assert "empty request text" in response.text
    assert events == []  # R3.1: empty-text path emits nothing


def test_handle_emits_started_finished():
    events = []
    assistant = DummyAssistant(event_sink=lambda t, p: events.append((t, p)))
    response = assistant.handle(AssistantRequest(text="hi", session_id="s1"))
    assert response.status == "ok"
    assert response.text == "ok:hi"
    types = [t for t, _ in events]
    assert types == ["agent.started", "agent.finished"]
    assert events[0][1]["agent"] == "dummy"
    assert events[1][1]["status"] == "ok"
    assert events[1][1]["session_id"] == "s1"


def test_event_sink_error_best_effort():
    def _boom(event_type, payload):
        raise RuntimeError("sink down")

    assistant = DummyAssistant(event_sink=_boom)
    response = assistant.handle(AssistantRequest(text="hi"))
    assert response.status == "ok"  # event failure must not break response


def test_event_sink_none_ok():
    assistant = DummyAssistant()
    response = assistant.handle(AssistantRequest(text="hi"))
    assert response.status == "ok"


def test_process_raise_returns_error_status():
    events = []
    assistant = DummyAssistant(event_sink=lambda t, p: events.append(t), raise_process=True)
    response = assistant.handle(AssistantRequest(text="hi"))
    assert response.status == "error"
    assert "dummy failed" in response.text
    assert response.metadata["error"] == "boom"
    assert events[-1] == "agent.finished"  # finished still emitted on error


def test_general_deterministic_template():
    assistant = GeneralAssistant()
    r1 = assistant.handle(AssistantRequest(text="xin chào"))
    r2 = assistant.handle(AssistantRequest(text="xin chào"))
    assert r1.status == "ok"
    assert r1.text == "Bạn nói: xin chào"
    assert r1.text == r2.text
    assert r1.metadata["model_called"] is False


def test_general_knowledge_bullets():
    assistant = GeneralAssistant()
    response = assistant.handle(
        AssistantRequest(text="hi", context={"knowledge": ["a", "b", "c", "d", "e", "f"]})
    )
    assert response.text.count("\n- ") == 5  # capped at 5


def test_general_with_model():
    assistant = GeneralAssistant(model=MockModel(responses=["model reply"]))
    response = assistant.handle(AssistantRequest(text="hello"))
    assert response.status == "ok"
    assert response.metadata["model_called"] is True
    assert response.metadata["model"] == "mock"
    assert response.text == "model reply"


def test_general_model_error_fallback():
    class _Boom:
        name = "boom"

        def chat(self, messages, temperature=0.7):
            raise RuntimeError("model offline")

    assistant = GeneralAssistant(model=_Boom())  # type: ignore[arg-type]
    response = assistant.handle(AssistantRequest(text="hello"))
    assert response.status == "ok"
    assert response.metadata["model_called"] is False
    assert "model offline" in response.metadata["model_error"]
    assert response.text.startswith("Bạn nói:")
