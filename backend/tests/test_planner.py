"""Planner tests (stub deterministic + real with fake model)."""

import pytest

from aios_core.models import ChatMessage, ChatResponse, MockModel, ModelContract
from aios_core.orchestrator import Planner, PlannerStub
from aios_core.workflow import WorkflowDefinition, WorkflowLibrary


def library():
    lib = WorkflowLibrary()
    lib.register(
        WorkflowDefinition(
            name="crud_generator",
            version="1.0.0",
            description="x",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
        )
    )
    return lib


class FakeModel(ModelContract):
    def __init__(self, response: str, available: bool = True):
        self._response = response
        self._available = available
        self.calls = 0

    @property
    def name(self) -> str:
        return "fake"

    def is_available(self) -> bool:
        return self._available

    def metadata(self):
        from aios_core import __version__
        from aios_core.metadata import AiOSMetadata

        return AiOSMetadata(id="models.fake", name="fake", version=__version__, author="a", license="MIT")

    def _chat(self, messages, temperature, max_tokens):
        self.calls += 1
        return ChatResponse(content=self._response, model="fake")


class BrokenModel(FakeModel):
    def _chat(self, messages, temperature, max_tokens):
        self.calls += 1
        from aios_core.models import ModelError

        raise ModelError("model exploded")  # ModelError (not RuntimeError) is caught


def test_planner_stub_deterministic():
    stub = PlannerStub(intent_map={"build a crud": "coding"})
    plan = stub.plan("build a crud", None, library())
    assert plan.intent == "coding"
    assert plan.llm_used is False
    assert stub.calls == 0
    assert plan.error is False


def test_planner_stub_unknown_defaults_chat():
    stub = PlannerStub()
    assert stub.plan("weird text", None, library()).intent == "chat"


def test_planner_real_parses():
    model = FakeModel(response="intent: coding\nworkflow: crud_generator\nreasoning: ok")
    planner = Planner()
    plan = planner.plan("build api", model, library())
    assert plan.intent == "coding"
    assert plan.workflow_names == ["crud_generator"]
    assert plan.llm_used is True
    assert plan.error is False
    assert planner.calls == 1


def test_planner_unavailable():
    model = FakeModel(response="intent: coding", available=False)
    planner = Planner()
    plan = planner.plan("x", model, library())
    assert plan.intent == "chat"
    assert plan.error is True
    assert plan.llm_used is False


def test_planner_unparseable():
    model = FakeModel(response="I don't understand")
    planner = Planner()
    plan = planner.plan("x", model, library())
    assert plan.intent == "chat"
    assert plan.error is True
    assert planner.calls == 1


def test_planner_calls_counted_on_error():
    model = BrokenModel(response="")
    planner = Planner()
    plan = planner.plan("x", model, library())
    assert plan.error is True
    assert planner.calls == 1  # counted even when the call raises


def test_planner_reset_calls():
    model = FakeModel(response="intent: chat")
    planner = Planner()
    planner.plan("x", model, library())
    assert planner.calls == 1
    planner.reset_calls()
    assert planner.calls == 0
