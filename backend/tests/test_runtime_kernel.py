"""RuntimeKernel tests: wiring, lifecycle, end-to-end."""

from aios_core.config import (
    AuditSettings,
    ArtifactsSettings,
    MemorySettings,
    ResourcesSettings,
    Settings,
)
from aios_core.kernel import RuntimeKernel
from aios_core.kernel.events import EventBus
from aios_core.kernel.execution_plan import ExecutionPlanBuilder
from aios_core.kernel.services import (
    ArtifactService,
    ContextScope,
    ContextService,
    EventService,
    ExecutionService,
    ExecutionStatus,
    PermissionService,
    PolicyService,
    ResourceService,
    SchedulerService,
    StateService,
)
from aios_core.memory import MemoryCoordinator, MemoryKind, MemoryQuery


def make_settings(tmp_path):
    return Settings(
        audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
        artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        resources=ResourcesSettings(max_tokens=1000, max_concurrent=2),
        memory=MemorySettings(
            conversation_db_path=str(tmp_path / "conv.db"),
            knowledge_db_path=str(tmp_path / "knowledge.db"),
        ),
    )


def test_create_has_all_services(tmp_path):
    kernel = RuntimeKernel.create(make_settings(tmp_path))
    c = kernel.container
    for interface in (
        EventBus,
        EventService,
        ArtifactService,
        ContextService,
        PermissionService,
        PolicyService,
        SchedulerService,
        StateService,
        ResourceService,
        ExecutionService,
    ):
        assert c.has(interface), f"missing {interface}"
    assert kernel.bus is not None


def test_resolve_all_no_raise(tmp_path):
    kernel = RuntimeKernel.create(make_settings(tmp_path))
    c = kernel.container
    for interface in (
        EventBus,
        EventService,
        ArtifactService,
        ContextService,
        PermissionService,
        PolicyService,
        SchedulerService,
        StateService,
        ResourceService,
        ExecutionService,
        MemoryCoordinator,
    ):
        assert c.resolve(interface) is not None


def test_memory_coordinator_wired(tmp_path):
    """TASK-023: coordinator resolvable; empty query returns empty selection
    and injection writes into EXECUTION scope (no store data needed)."""
    kernel = RuntimeKernel.create(make_settings(tmp_path))
    coordinator = kernel.container.resolve(MemoryCoordinator)
    query = MemoryQuery(text="", session_id="s1")
    selection = coordinator.retrieve(query)
    assert selection.items == []
    assert selection.total_tokens == 0
    ctx = coordinator.inject(query)
    assert ctx.session_id == "s1"
    context_service = kernel.container.resolve(ContextService)
    stored = context_service.get(ContextScope.EXECUTION, "memory.context", inherit=False)
    assert stored is not None and stored.session_id == "s1"


def test_context_optimizer_wired(tmp_path):
    """TASK-024: optimizer resolvable + optimize runs end-to-end (tmp settings)."""
    from aios_core.context import ContextOptimizer

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    optimizer = kernel.container.resolve(ContextOptimizer)
    final = optimizer.optimize("hello")
    assert final.total_tokens >= 1
    assert final.usable_budget == 19000  # default budget: 20000 - reserve 1000
    assert "[User Request]" in final.render()


def test_planning_engine_wired(tmp_path):
    """TASK-026: planning engine resolvable + offline plan (tmp settings)."""
    from aios_core.orchestrator.planning import PlanningEngine

    class Req:
        def __init__(self, text):
            self.text = text
            self.policy = None
            self.source = "test"

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    engine = kernel.container.resolve(PlanningEngine)
    result = engine.plan(Req("check status"))
    assert result.llm_calls == 0  # offline-first
    assert result.plan.status.value == "ready"


def test_graph_executor_wired(tmp_path):
    """TASK-027: graph executor resolvable + shares StateService instance."""
    from aios_core.kernel.execution_plan import PlanNode, PlanNodeType
    from aios_core.kernel.graph import ExecutionGraph, GraphExecutor, GraphNode

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    executor = kernel.container.resolve(GraphExecutor)
    assert executor._state is kernel.container.resolve(StateService)  # shared
    graph = ExecutionGraph(id="g", nodes=[
        GraphNode(id="A", type=PlanNodeType.TASK, name="a"),
        GraphNode(id="B", type=PlanNodeType.TASK, name="b",
                  depends_on=[{"node_id": "A"}]),
    ])
    result = executor.execute(graph, lambda n, ctx: n.id)
    assert result.status.value == "succeeded"
    assert result.execution_order == ["A", "B"]


def test_graph_scheduler_wired(tmp_path):
    """TASK-028: scheduler resolvable + shared instances + graph_settings."""
    from aios_core.kernel.graph import GraphExecutor
    from aios_core.kernel.scheduler import GraphScheduler

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    scheduler = kernel.container.resolve(GraphScheduler)
    assert scheduler._resources is kernel.container.resolve(ResourceService)
    assert scheduler._state is kernel.container.resolve(StateService)
    assert scheduler._graph_settings is kernel.container.resolve(GraphExecutor)._settings
    plan = ExecutionPlanBuilder.from_dict({
        "id": "p", "request_ref": "r",
        "nodes": [
            {"id": "A", "type": "task", "name": "a"},
            {"id": "B", "type": "task", "name": "b", "depends_on": ["A"]},
        ],
    })
    result = scheduler.schedule_plan(plan, lambda n, ctx: n.id)
    assert result.graph.status.value == "succeeded"
    assert result.graph.execution_order == ["A", "B"]


def test_harness_wired(tmp_path):
    """TASK-029 (M6-H1): registry/runner resolvable + shared services."""
    from aios_core.harness import Harness, HarnessRegistry, HarnessRunner

    class H(Harness):
        id = "h1"
        name = "H1"
        version = "1.0.0"

        def run(self, ctx):
            return "ok"

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    registry = kernel.container.resolve(HarnessRegistry)
    runner = kernel.container.resolve(HarnessRunner)
    assert runner._state is kernel.container.resolve(StateService)
    assert runner._artifacts is kernel.container.resolve(ArtifactService)
    registry.register(H())
    ctx = runner.create_context(registry.get("h1"), target="t")
    report = runner.execute(registry.get("h1"), ctx)
    assert report.result.status.value == "completed"
    assert len(report.artifacts) == 2  # INV-018 evidence


def test_model_router_wired(tmp_path):
    """TASK-025: router resolvable; offline select works (no chat calls)."""
    from aios_core.models import ModelRouter, RouteRequest

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    router = kernel.container.resolve(ModelRouter)
    decision = router.select(RouteRequest())
    assert decision.model_name == "mock"
    assert decision.policy_used == "balanced"


def test_start_stop_idempotent(tmp_path):
    kernel = RuntimeKernel.create(make_settings(tmp_path))
    kernel.start()
    kernel.start()  # idempotent
    kernel.stop()
    kernel.stop()  # idempotent


def test_end_to_end_execution(tmp_path):
    kernel = RuntimeKernel.create(make_settings(tmp_path))
    execution = kernel.container.resolve(ExecutionService)
    plan = ExecutionPlanBuilder.from_dict(
        {
            "id": "plan-e2e",
            "nodes": [
                {"id": "a", "type": "task", "name": "A"},
                {"id": "b", "type": "task", "name": "B", "depends_on": ["a"]},
            ],
            "required_permissions": ["filesystem"],
            "estimated_tokens": 10,
        }
    )
    result = execution.execute(
        plan,
        {"a": lambda n, r: "ra", "b": lambda n, r: "rb"},
    )
    assert result.status == ExecutionStatus.COMPLETED
    assert result.node_results == {"a": "ra", "b": "rb"}
    # resources released
    resources = kernel.container.resolve(ResourceService)
    assert resources.stats()["used_tokens"] == 0
    assert resources.stats()["running"] == 0


def test_settings_resources_wired(tmp_path):
    kernel = RuntimeKernel.create(make_settings(tmp_path))
    resources = kernel.container.resolve(ResourceService)
    assert resources.limits.max_tokens == 1000
    assert resources.limits.max_concurrent == 2


def test_model_registry_wired(tmp_path):
    from aios_core.models import ModelRegistry

    kernel = RuntimeKernel.create(make_settings(tmp_path))
    registry = kernel.container.resolve(ModelRegistry)
    assert "mock" in registry.list()
    assert registry.default().name == "mock"
