"""RuntimeKernel: wires all kernel services into the DI container."""

from __future__ import annotations

from ..config import ResourcesSettings, Settings
from ..container import Container
from ..models import MockModel, ModelRegistry
from .events import EventBus
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

        return cls(container, bus)
