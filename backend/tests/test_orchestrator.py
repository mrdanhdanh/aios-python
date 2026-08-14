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


def test_offline_first_corpus():
    """AC6 (mục 20 brief): offline-first đo thực tế trên corpus ≥50 requests ĐẠI DIỆN.

    Mỗi request có intent rõ ràng + expected route. Chạy với MockModel (0 real call),
    assert per-request route KHÔNG dùng Planner, và assert tỷ lệ đo được:
        deterministic_route_rate >= 70% (target) / >= 90% (stretch)
        planner_call_rate <= 30%
    """
    model = MockModel(responses=["intent: chat"], loop=True)
    planner = Planner()
    orch = make_orchestrator(planner=planner, model=model)

    # 45 distinct representative requests — mỗi cái resolves deterministically qua Rule Engine.
    # (request, expected_intent, expected_agent, expected_resolved_by)
    deterministic = [
        # coding (generate api / create api)
        ("generate api for the user service", "coding", "coder", "rule"),
        ("create api endpoint for orders", "coding", "coder", "rule"),
        ("generate api docs from the schema", "coding", "coder", "rule"),
        ("generate api client in typescript", "coding", "coder", "rule"),
        ("create api for the auth module", "coding", "coder", "rule"),
        ("generate api wrapper around the db", "coding", "coder", "rule"),
        ("create api stub for payments", "coding", "coder", "rule"),
        ("generate api sdk for the mobile app", "coding", "coder", "rule"),
        ("create api route for health checks", "coding", "coder", "rule"),
        ("generate api mock for integration tests", "coding", "coder", "rule"),
        # medical / doctor
        ("I have a medical question about my prescription", "medical", "doctor", "rule"),
        ("please doctor help me with this symptom", "medical", "doctor", "rule"),
        ("khám bệnh tại nhà vào thứ bảy", "medical", "doctor", "rule"),
        ("triệu chứng đau đầu và sốt nhẹ", "medical", "doctor", "rule"),
        ("medical advice for a persistent cough", "medical", "doctor", "rule"),
        ("see a doctor about my knee pain", "medical", "doctor", "rule"),
        ("doctor consultation for skin rash", "medical", "doctor", "rule"),
        ("medical second opinion needed", "medical", "doctor", "rule"),
        ("book a doctor appointment", "medical", "doctor", "rule"),
        ("medical symptom checker online", "medical", "doctor", "rule"),
        # system status / health
        ("show system status now", "system", "system_doctor", "rule"),
        ("run a system health check", "system", "system_doctor", "rule"),
        ("what is the current system status", "system", "system_doctor", "rule"),
        ("system health report please", "system", "system_doctor", "rule"),
        ("check the system status of the cluster", "system", "system_doctor", "rule"),
        ("system health diagnostics", "system", "system_doctor", "rule"),
        ("get system status summary", "system", "system_doctor", "rule"),
        ("system status after the deploy", "system", "system_doctor", "rule"),
        ("full system health scan", "system", "system_doctor", "rule"),
        ("system status endpoint response", "system", "system_doctor", "rule"),
        # skill install
        ("install skill markdown linter", "skill", None, "rule"),
        ("install skill code formatter", "skill", None, "rule"),
        ("install skill graph visualizer", "skill", None, "rule"),
        ("install skill pdf exporter", "skill", None, "rule"),
        ("install skill git helper", "skill", None, "rule"),
        ("install skill db profiler", "skill", None, "rule"),
        ("install skill api tester", "skill", None, "rule"),
        ("install skill log viewer", "skill", None, "rule"),
        ("install skill cache warmer", "skill", None, "rule"),
        ("install skill schema validator", "skill", None, "rule"),
        # upgrade / update system
        ("upgrade the runtime to latest", "upgrade", None, "rule"),
        ("upgrade now to version 2", "upgrade", None, "rule"),
        ("update system packages safely", "upgrade", None, "rule"),
        ("update system configuration", "upgrade", None, "rule"),
        ("upgrade the model provider", "upgrade", None, "rule"),
        ("update system before maintenance", "upgrade", None, "rule"),
        ("upgrade kernel modules", "upgrade", None, "rule"),
        ("update system locale settings", "upgrade", None, "rule"),
        ("upgrade database engine", "upgrade", None, "rule"),
        ("update system certificates", "upgrade", None, "rule"),
        # diagnose / phân tích lỗi
        ("diagnose the failing build", "diagnose", None, "rule"),
        ("diagnose why tests are red", "diagnose", None, "rule"),
        ("phân tích lỗi deployment hôm qua", "diagnose", None, "rule"),
        ("diagnose the network timeout", "diagnose", None, "rule"),
        ("diagnose memory leak in worker", "diagnose", None, "rule"),
        ("phân tích lỗi khi chạy migration", "diagnose", None, "rule"),
        ("diagnose slow query performance", "diagnose", None, "rule"),
        ("diagnose crash on startup", "diagnose", None, "rule"),
        ("phân tích lỗi lint trong CI", "diagnose", None, "rule"),
        ("diagnose deadlock between services", "diagnose", None, "rule"),
        # chat / hello
        ("hello there assistant", "chat", None, "rule"),
        ("hi how are you", "chat", None, "rule"),
        ("xin chào bạn có khỏe không", "chat", None, "rule"),
        ("just chat about the weather", "chat", None, "rule"),
        ("chat with me for a bit", "chat", None, "rule"),
        ("hello world from the test", "chat", None, "rule"),
        ("hi i am new here", "chat", None, "rule"),
        ("xin chào tôi cần hỗ trợ", "chat", None, "rule"),
        ("hello can you hear me", "chat", None, "rule"),
        ("chat casually about music", "chat", None, "rule"),
    ]

    # 15 distinct OPEN-ENDED requests — không khớp rule nào → bắt buộc gọi Planner.
    open_ended = [
        "refactor the entire monorepo to a hexagonal architecture",
        "explain the theory of relativity in simple terms",
        "write a haiku about the quiet ocean at dawn",
        "summarize this quarter's sales report into three bullets",
        "design a go-to-market plan for a new developer SaaS",
        "translate the following paragraph into French",
        "what is the philosophical meaning of life",
        "propose a new brand logo concept for a fintech startup",
        "analyze the competitor landscape for vector databases",
        "draft a polite follow-up email to the client",
        "plan a two-day team offsite in the mountains",
        "create a retrospective document for the last sprint",
        "recommend three books on distributed systems",
        "estimate the timeline for the migration project",
        "brainstorm five feature ideas for the Q3 roadmap",
    ]

    total = len(deterministic) + len(open_ended)
    assert total >= 50, f"corpus phải >= 50 requests, có {total}"

    # Per-request route assertion (deterministic bucket must NEVER call Planner).
    for text, exp_intent, exp_agent, exp_by in deterministic:
        resp = orch.handle(text)
        assert resp.resolved_by == exp_by, f"{text!r}: resolved_by={resp.resolved_by} != {exp_by}"
        assert resp.intent == exp_intent, f"{text!r}: intent={resp.intent} != {exp_intent}"
        if exp_agent is not None:
            assert resp.agent == exp_agent, f"{text!r}: agent={resp.agent} != {exp_agent}"

    # Open-ended bucket — each forces a Planner call (mock model, 0 real network).
    for text in open_ended:
        orch.handle(text)

    stats = orch.stats()
    assert stats["total_requests"] == total

    planner_calls = stats["llm_calls"]
    planner_call_rate = planner_calls / total
    deterministic_route_rate = 1.0 - planner_call_rate

    # Acceptance (brief mục 20): measured, not inferred.
    assert deterministic_route_rate >= 0.70, f"deterministic_route_rate={deterministic_route_rate:.2%} < 70%"
    assert planner_call_rate <= 0.30, f"planner_call_rate={planner_call_rate:.2%} > 30%"
    assert planner_calls == len(open_ended), (
        f"planner called {planner_calls} times, expected {len(open_ended)} (open-ended only)"
    )


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
