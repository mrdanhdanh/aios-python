"""Orchestrator pipeline tests (6 case AC5 + AC6 offline-first + stats)."""

from aios_core.models import MockModel
from aios_core.orchestrator import (
    AgentSelector,
    Normalizer,
    Orchestrator,
    Planner,
    PlannerStub,
    RuleEngine,
    WorkflowMatcher,
    default_rules,
)
from aios_core.workflow import WorkflowDefinition, WorkflowLibrary


def make_library():
    lib = WorkflowLibrary()
    lib.register(
        WorkflowDefinition(
            name="crud_generator",
            version="1.0.0",
            description="CRUD API generator with tests",
            nodes=[{"id": "a", "type": "task", "name": "A"}],
        )
    )
    return lib


def make_orchestrator(planner=None, model=None):
    lib = make_library()
    return Orchestrator(
        rule_engine=default_rules(),
        workflow_matcher=WorkflowMatcher(lib),
        planner=planner or PlannerStub(),
        normalizer=Normalizer(library=lib),
        agent_selector=AgentSelector(),
        model=model,
        library=lib,
    )


def test_rule_resolves_coding():
    orch = make_orchestrator()
    resp = orch.handle("generate api for users")
    assert resp.intent == "coding"
    assert resp.agent == "coder"
    assert resp.resolved_by == "rule"


def test_rule_with_workflow_name():
    # "generate api" → rule coding/coder + matcher token search "api" → crud_generator
    orch = make_orchestrator()
    resp = orch.handle("generate api")
    assert resp.agent == "coder"
    assert resp.workflow_name == "crud_generator"
    assert resp.resolved_by == "rule"


def test_medical():
    orch = make_orchestrator()
    resp = orch.handle("medical question about headache")
    assert resp.intent == "medical"
    assert resp.agent == "doctor"
    assert resp.resolved_by == "rule"


def test_workflow_matcher_path():
    orch = make_orchestrator()
    # "review" is not a rule pattern → matcher token search → review_pr? No —
    # fixture library only has crud_generator; use a token matching it.
    resp = orch.handle("please make a generator tool")
    assert resp.intent == "workflow"
    assert resp.workflow_name == "crud_generator"
    assert resp.resolved_by == "workflow"


def test_hash_normalizer():
    orch = make_orchestrator()
    resp = orch.handle("#just chatting")
    assert resp.intent == "chat"
    assert resp.resolved_by == "normalizer"


def test_planner_fallback():
    stub = PlannerStub(intent_map={"mystery request": "coding"})
    orch = make_orchestrator(planner=stub)
    resp = orch.handle("mystery request")
    assert resp.intent == "coding"
    assert resp.resolved_by == "fallback"
    assert resp.plan is not None
    assert resp.plan.llm_used is False


def test_offline_first_100_requests():
    """AC6: 70 rule + 20 workflow + 10 lạ với Planner thật + MockModel → llm_calls == 10."""
    model = MockModel(responses=["intent: chat"], loop=True)
    planner = Planner()
    orch = make_orchestrator(planner=planner, model=model)

    rule_samples = [
        "generate api", "medical help", "system status", "install skill x",
        "upgrade now", "diagnose error", "hello world",
    ]
    wf_samples = ["crud generator", "i need crud api", "generate a crud api please"]
    for i in range(70):
        orch.handle(rule_samples[i % len(rule_samples)])
    for i in range(20):
        orch.handle(wf_samples[i % len(wf_samples)])
    for i in range(10):
        orch.handle(f"completely unknown request {i}")

    stats = orch.stats()
    assert stats["total_requests"] == 100
    assert stats["llm_calls"] == 10  # only the 10 unknown ones


def test_stats_reset():
    model = MockModel(responses=["intent: chat"], loop=True)
    planner = Planner()
    orch = make_orchestrator(planner=planner, model=model)
    orch.handle("unknown request 1")
    assert orch.stats()["llm_calls"] == 1
    orch.reset()
    assert orch.stats() == {"total_requests": 0, "llm_calls": 0}
    # after reset: fresh count
    orch.handle("unknown request 2")
    assert orch.stats()["llm_calls"] == 1


def test_stats_copy():
    orch = make_orchestrator()
    orch.handle("hello")
    stats = orch.stats()
    stats["total_requests"] = 999  # mutate the copy
    assert orch.stats()["total_requests"] == 1


def test_dict_input():
    orch = make_orchestrator()
    resp = orch.handle({"text": "medical check", "source": "api"})
    assert resp.source == "api"
    assert resp.agent == "doctor"
