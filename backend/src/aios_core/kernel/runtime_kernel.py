"""RuntimeKernel: wires all kernel services into the DI container."""

from __future__ import annotations

from ..config import ResourcesSettings, Settings
from ..container import Container
from ..models import MockModel, ModelRegistry
from .events import Event, EventBus, EventType
from .services import (
    ArtifactService,
    ContextService,
    EventService,
    ExecutionService,
    PermissionService,
    PolicyService,
    ResourceService,
    SchedulerService,
    StateService,
)


class RuntimeKernel:
    """Assemble and manage the full runtime service graph."""

    def __init__(self, container: Container, bus: EventBus) -> None:
        self._container = container
        self._bus = bus

    @property
    def container(self) -> Container:
        return self._container

    @property
    def bus(self) -> EventBus:
        return self._bus

    def start(self) -> None:
        self._container.start()

    def stop(self) -> None:
        self._container.stop()

    @classmethod
    def create(cls, settings: Settings | None = None) -> "RuntimeKernel":
        settings = settings or Settings()
        container = Container()
        bus = EventBus()

        # Instances constructed manually (Union/non-type constructor hints are
        # not DI-resolvable) — register_instance.
        event_service = EventService(bus, settings.audit.db_path)
        artifact_service = ArtifactService(settings.artifacts.dir, bus)
        context_service = ContextService()
        resources_settings = ResourcesSettings(
            max_tokens=settings.resources.max_tokens,
            max_concurrent=settings.resources.max_concurrent,
        )
        container.register_instance(EventBus, bus)
        container.register_instance(EventService, event_service)
        container.register_instance(ArtifactService, artifact_service)
        container.register_instance(ContextService, context_service)
        container.register_instance(ResourcesSettings, resources_settings)

        # Model registry (pre-register the offline mock).
        model_registry = ModelRegistry(default_name=settings.models.default)
        model_registry.register("mock", MockModel())
        container.register_instance(ModelRegistry, model_registry)

        # Model router (TASK-025): policy-driven selection + fallback.
        # Note: register("mock", MockModel()) already attached a default
        # capability (availability=True — no is_available() call).
        from ..models.router import ModelRouter, RoutingPolicy

        model_router = ModelRouter(
            registry=model_registry,
            policy=RoutingPolicy.from_settings(
                settings.models.routing.model_dump()
            ),
        )
        container.register_instance(ModelRouter, model_router)

        # Memory coordinator (TASK-023): the only gateway to memory stores.
        # Lazy imports avoid the aios_core/__init__ → knowledge → memory cycle.
        from ..knowledge.knowledge import KnowledgeMemory
        from ..memory import ConversationMemory
        from ..memory.contracts import MemoryBudget
        from ..memory.coordinator import MemoryCoordinator, MemoryCoordinatorConfig
        from ..memory.sources import (
            ArtifactSource,
            ConversationSource,
            KnowledgeSource,
            SessionSource,
        )

        conversation_memory = ConversationMemory(settings.memory.conversation_db_path)
        knowledge_memory = KnowledgeMemory(settings.memory.knowledge_db_path)
        memory_coordinator = MemoryCoordinator(
            sources=[
                ConversationSource(conversation_memory),
                SessionSource(context_service),
                KnowledgeSource(knowledge_memory),  # embedder=None (offline)
                ArtifactSource(artifact_service),
            ],
            context=context_service,
            config=MemoryCoordinatorConfig(
                budget=MemoryBudget(**settings.memory.budget.model_dump())
            ),
        )
        container.register_instance(MemoryCoordinator, memory_coordinator)

        # Context optimizer (TASK-024): priority-ordered budgeted context.
        from ..context.optimizer import ContextOptimizer, ContextOptimizerConfig

        context_optimizer = ContextOptimizer(
            context=context_service,
            config=ContextOptimizerConfig(
                budget=MemoryBudget(**settings.memory.budget.model_dump())
            ),
        )
        container.register_instance(ContextOptimizer, context_optimizer)

        # Planning engine (TASK-026): offline-first pipeline
        # (workflow → template → rule → LLM) with INV-014 plan validation.
        from ..capabilities.registry import CapabilityRegistry
        from ..orchestrator.planner import Planner
        from ..orchestrator.planning import PlanningEngine
        from ..workflow.library import WorkflowLibrary

        planning_engine = PlanningEngine(
            library=WorkflowLibrary(),
            capabilities=CapabilityRegistry(),
            policy=PolicyService(bus),
            resources=resources_settings,
            planner=Planner(),
            router=model_router,  # untyped inject (INV-005 rule A)
            model=None,  # None → router decides on LLM path
            registry=model_registry,  # LLM path: model = registry.get(...)
            settings=settings.planning,
        )
        container.register_instance(PlanningEngine, planning_engine)

        # Remaining services are constructed via the container (type-only hints).
        container.register(PermissionService, PermissionService)
        container.register(PolicyService, PolicyService)
        container.register(SchedulerService, SchedulerService)
        container.register(StateService, StateService)
        container.register(ResourceService, ResourceService)
        container.register(ExecutionService, ExecutionService)

        # Execution graph (TASK-027): DAG execution + graph state (INV-015).
        # MUST come after StateService registration so resolve() returns the
        # same singleton instance that ExecutionService will use.
        from ..kernel.graph import GraphExecutor

        graph_executor = GraphExecutor(
            state_service=container.resolve(StateService),  # shared instance
            settings=settings.graph,
        )
        container.register_instance(GraphExecutor, graph_executor)

        # Graph scheduler (TASK-028): resource-aware scheduling via
        # ResourceService public API (INV-016 — không sở hữu implementation).
        from ..kernel.scheduler import GraphScheduler

        graph_scheduler = GraphScheduler(
            resource_service=container.resolve(ResourceService),  # shared
            state_service=container.resolve(StateService),  # shared
            executor=container.resolve(GraphExecutor),  # shared (027)
            settings=settings.scheduler,
            graph_settings=settings.graph,  # schedule_plan consumes default_failure_policy
        )
        container.register_instance(GraphScheduler, graph_scheduler)

        # Harness kernel (TASK-029, M6-H1): registry + runner (INV-017/018).
        from ..harness import HarnessRegistry, HarnessRunner

        harness_registry = HarnessRegistry()
        harness_runner = HarnessRunner(
            state_service=container.resolve(StateService),  # shared
            artifact_service=container.resolve(ArtifactService),  # shared (M1)
            diagnose_on_failure=settings.harness.diagnose_on_failure,
        )
        container.register_instance(HarnessRegistry, harness_registry)
        container.register_instance(HarnessRunner, harness_runner)

        # Execution verification (TASK-030, M6-H2): VerificationHarness over
        # H1 runner; EvidenceServices duck-typed (P1-02 v2 — KHÔNG import
        # kernel.services.events trong harness/execution).
        from types import SimpleNamespace

        from ..harness.execution import (
            EvidenceServices, VerificationHarness,
        )

        execution_services = EvidenceServices(
            state=container.resolve(StateService),  # shared
            events=container.resolve(EventService),  # top-level import (M1)
            artifacts=container.resolve(ArtifactService),  # shared (M1)
        )
        verification_harness = VerificationHarness(
            execution_services,
            state_service=container.resolve(StateService),
            artifact_service=container.resolve(ArtifactService),
        )
        harness_registry.register(verification_harness)  # id="verification"
        container.register_instance(VerificationHarness, verification_harness)

        # Test & Simulation (TASK-031, M6-H3): TestHarness qua H1 runner —
        # Fake Runtime/Tool, deterministic, không side effect (INV-020).
        from ..harness.testing import FakeRuntime, SimulationRunner, TestHarness

        test_harness = TestHarness(
            SimulationRunner(FakeRuntime()),
            state_service=container.resolve(StateService),  # shared
        )
        harness_registry.register(test_harness)  # id="test"
        container.register_instance(TestHarness, test_harness)

        # Evaluation (TASK-032, M6-H4): EvaluationHarness qua H1 runner —
        # deterministic evaluators, LLM judge stub offline (INV-020).
        from ..harness.evaluation import Engine, EvaluationHarness

        evaluation_harness = EvaluationHarness(
            Engine(default_threshold=settings.evaluation.default_threshold),
            state_service=container.resolve(StateService),  # shared
            max_items=settings.evaluation.max_items,
        )
        harness_registry.register(evaluation_harness)  # id="evaluation"
        container.register_instance(EvaluationHarness, evaluation_harness)

        # Benchmark + Regression Gate (TASK-033, M6-H4): run_fn placeholder
        # deterministic — real runner inject qua config (INV-021).
        from ..harness.benchmark import (
            BenchmarkHarness, BenchmarkRunner, RegressionGate, default_rules,
        )
        from ..harness.benchmark.contracts import RunResult

        def _placeholder_run(scenario_id: str) -> RunResult:
            return RunResult(scenario_id=scenario_id)

        benchmark_harness = BenchmarkHarness(
            BenchmarkRunner(_placeholder_run,
                            max_scenarios=settings.benchmark.max_scenarios),
            RegressionGate(default_rules(
                quality_max_delta=settings.benchmark.quality_max_delta,
                failure_rate_max_delta=settings.benchmark.failure_rate_max_delta,
            )),
            state_service=container.resolve(StateService),  # shared
        )
        harness_registry.register(benchmark_harness)  # id="benchmark"
        container.register_instance(BenchmarkHarness, benchmark_harness)

        # Behavioral Conformance (M13-P0, TASK-089): N lần + repeat + fault +
        # evidence compare + gate (chỉ expose). Engine tạo SimulationRunner
        # riêng (default FakeRuntime) — độc lập TestHarness (P3-8 v1).
        from ..harness.behavioral import (
            BehavioralConformanceEngine, BehavioralConformanceHarness,
        )

        behavioral_harness = BehavioralConformanceHarness(
            BehavioralConformanceEngine(),
            state_service=container.resolve(StateService),  # shared
        )
        harness_registry.register(behavioral_harness)  # id="behavioral"
        container.register_instance(BehavioralConformanceHarness, behavioral_harness)

        # Doctor & Readiness (TASK-034, M6-H5): shared DoctorChecks — checks
        # injectable qua register (placeholder deterministic v1, INV-022).
        from ..harness.doctor import (
            DoctorChecks, DoctorHarness, ReadinessHarness, ReadinessScorer,
        )

        doctor_checks = DoctorChecks()
        doctor_harness = DoctorHarness(
            doctor_checks,
            state_service=container.resolve(StateService),  # shared
        )
        readiness_harness = ReadinessHarness(
            doctor_checks,  # P1-01: dùng chung instance
            ReadinessScorer(min_overall=settings.doctor.min_overall,
                            policy_gate=settings.doctor.policy_gate),
            state_service=container.resolve(StateService),  # shared
        )
        harness_registry.register(doctor_harness)  # id="doctor"
        harness_registry.register(readiness_harness)  # id="readiness"
        container.register_instance(DoctorHarness, doctor_harness)
        container.register_instance(ReadinessHarness, readiness_harness)

        # Enterprise (M7): Identity + Tenancy + Distributed Runtime + Governance
        # + Security + Operations behind a single facade (INV-022..INV-029).
        # Default wiring uses in-memory subsystems (offline-first); external
        # services (Vault, K8s) plug in via injected dependencies.
        from ..enterprise import EnterpriseManager

        enterprise = EnterpriseManager()
        container.register_instance(EnterpriseManager, enterprise)

        # Autonomous (M9): Autonomy Layer trên Orchestrator (INV-030..034).
        # Offline-first: goal/loop/governor/recovery/long-horizon/memory/stuck/
        # evaluation/multi-agent wired ngay; experimentation (cần evaluate_fn)
        # và scheduler (cần re-register fn) do wiring cấp cao cung cấp.
        from ..autonomous import (
            AutonomyBudget,
            AutonomyGovernor,
            AutonomousEvaluator,
            AutonomousGoalEngine,
            AutonomousLoop,
            AutonomousMemory,
            AutonomousPlanner,
            AutonomousRecovery,
            AutonomyManager,
            EvaluationConfig,
            LongHorizonManager,
            MultiAgentOrchestrator,
            RiskClass,
            StuckDetector,
            WorldModel,
        )

        risk_table = {
            RiskClass(key): value
            for key, value in settings.autonomous.risk_table.items()
        }

        autonomy_budget = AutonomyBudget(**settings.autonomous.budget.model_dump())
        autonomy_governor = AutonomyGovernor(
            budget=autonomy_budget,
            risk_table=risk_table,
        )
        autonomy_planner = AutonomousPlanner(risk_table=risk_table)
        autonomy_world = WorldModel()
        autonomy_goal_engine = AutonomousGoalEngine(
            event_service=container.resolve(EventService),
            db_path=settings.autonomous.db_path,
        )
        autonomy_loop = AutonomousLoop(
            governor=autonomy_governor,
            world=autonomy_world,
            planner=autonomy_planner,
            max_iterations=settings.autonomous.loop_max_iterations,
            event_service=container.resolve(EventService),
        )
        autonomy_memory = AutonomousMemory(
            event_service=container.resolve(EventService),
            db_path=settings.autonomous.db_path,
        )
        autonomy_manager = AutonomyManager(
            goal_engine=autonomy_goal_engine,
            governor=autonomy_governor,
            planner=autonomy_planner,
            world=autonomy_world,
            loop=autonomy_loop,
            recovery=AutonomousRecovery(
                event_service=container.resolve(EventService),
            ),
            long_horizon=LongHorizonManager(
                event_service=container.resolve(EventService),
                db_path=settings.autonomous.db_path,
            ),
            autonomous_memory=autonomy_memory,
            stuck_detector=StuckDetector(
                window_size=settings.autonomous.stuck_window
            ),
            db_path=settings.autonomous.db_path,
            event_service=container.resolve(EventService),
        )
        autonomy_manager.evaluator = AutonomousEvaluator(
            config=EvaluationConfig(
                correctness_min=settings.autonomous.correctness_min,
                risk_max=settings.autonomous.risk_max,
                cost_max=settings.autonomous.cost_max,
                stuck_iterations=settings.autonomous.stuck_iterations,
            ),
            event_service=container.resolve(EventService),
        )
        autonomy_manager.multi_agent = MultiAgentOrchestrator(
            event_service=container.resolve(EventService),
        )
        container.register_instance(AutonomyManager, autonomy_manager)

        # Kill Switch (TASK-068, M10-F3): emergency control plane — gate duy
        # nhất cho execution mới + tool calls (Gate E: bypass = 0).
        from ..kernel.kill_switch import KillSwitch
        from ..orchestrator.goals import GoalManager

        kill_switch = KillSwitch(
            # Lazy resolve — không bắt ExecutionService lúc create (test fake OK)
            cancel_execution=lambda eid: container.resolve(ExecutionService).cancel(eid),
            cancel_goal=(
                (lambda gid: container.resolve(GoalManager).cancel_goal(gid))
                if container.has(GoalManager) else None
            ),
            emit=lambda etype, payload: bus.publish(
                Event(type=EventType(etype), payload=payload, source="kill_switch")
            ),
        )
        container.register_instance(KillSwitch, kill_switch)

        return cls(container, bus)
