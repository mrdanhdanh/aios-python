"""Import smoke tests: package imports, version, exports."""

import re

import pytest

import aios_core
from aios_core import (
    Container,
    ContainerError,
    EventBus,
    ExecutionPlan,
    ExecutionPlanBuilder,
    contracts,
)
from aios_core.contracts import (
    ArtifactContract,
    CompatibilityChecker,
    ContractMetadata,
    ContractVersion,
)


def test_version_is_semver():
    assert re.match(r"^\d+\.\d+\.\d+", aios_core.__version__)


def test_exports_present():
    for name in (
        "get_logger",
        "setup_logging",
        "AiOSMetadata",
        "make_component_metadata",
        "HealthStatus",
        "HealthReport",
        "HealthCheck",
        "HealthRegistry",
        "Settings",
        "load_settings",
        "Container",
        "ContainerError",
        "EventBus",
        "ExecutionPlan",
        "ExecutionPlanBuilder",
        "contracts",
        "__version__",
    ):
        assert hasattr(aios_core, name), f"missing export: {name}"


def test_kernel_submodule_exports():
    from aios_core.kernel import Event, EventType, Subscription

    assert Event and EventType and Subscription


def test_services_imports():
    from aios_core.kernel.services import (
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

    assert all(
        x is not None
        for x in (
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
    )


def test_runtime_kernel_import():
    from aios_core.kernel import RuntimeKernel

    assert RuntimeKernel is not None


def test_models_imports():
    from aios_core.models import (
        MockModel,
        ModelContract,
        ModelError,
        ModelNotAvailableError,
        ModelRegistry,
        ModelTimeoutError,
    )

    assert all(
        x is not None
        for x in (
            MockModel,
            ModelContract,
            ModelError,
            ModelNotAvailableError,
            ModelRegistry,
            ModelTimeoutError,
        )
    )


def test_memory_knowledge_imports():
    from aios_core.knowledge import ChunkResult, KnowledgeMemory, MockEmbedder
    from aios_core.memory import ConversationMemory, SessionMemory, SQLiteVectorStore, VectorStore

    assert all(
        x is not None
        for x in (
            ChunkResult,
            KnowledgeMemory,
            MockEmbedder,
            ConversationMemory,
            SessionMemory,
            SQLiteVectorStore,
            VectorStore,
        )
    )


def test_workflow_imports():
    from aios_core.workflow import (
        LangGraphCompiler,
        MockCompiler,
        WorkflowCompiler,
        WorkflowDefinition,
        WorkflowError,
        WorkflowLibrary,
        WorkflowNode,
    )

    assert all(
        x is not None
        for x in (
            LangGraphCompiler,
            MockCompiler,
            WorkflowCompiler,
            WorkflowDefinition,
            WorkflowError,
            WorkflowLibrary,
            WorkflowNode,
        )
    )


def test_m1_final_imports():
    from aios_core.capabilities import Capability, CapabilityError, CapabilityRegistry
    from aios_core.catalog import CatalogError, CatalogEntry, SystemCatalog
    from aios_core.knowledge_graph import GraphError, KnowledgeGraph
    from aios_core.prompts import PromptError, PromptEvaluation, PromptRegistry, PromptTemplate

    assert all(
        x is not None
        for x in (
            Capability,
            CapabilityError,
            CapabilityRegistry,
            CatalogError,
            CatalogEntry,
            SystemCatalog,
            GraphError,
            KnowledgeGraph,
            PromptError,
            PromptEvaluation,
            PromptRegistry,
            PromptTemplate,
        )
    )


def test_orchestrator_imports():
    from aios_core.orchestrator import (
        AgentSelector,
        Normalizer,
        Orchestrator,
        Planner,
        RuleEngine,
        SystemKnowledge,
        WorkflowMatcher,
    )

    assert all(
        x is not None
        for x in (
            AgentSelector,
            Normalizer,
            Orchestrator,
            Planner,
            RuleEngine,
            SystemKnowledge,
            WorkflowMatcher,
        )
    )


def test_goals_imports():
    # TASK-012: goal plane exports (AC12).
    from aios_core.orchestrator.goals import (
        FailureRecovery,
        GoalError,
        GoalManager,
        PermissionBroker,
        QueueError,
        TaskQueue,
        build_goal_modules,
    )

    assert all(
        x is not None
        for x in (
            FailureRecovery,
            GoalError,
            GoalManager,
            PermissionBroker,
            QueueError,
            TaskQueue,
            build_goal_modules,
        )
    )


def test_build_goal_modules_factory(tmp_path):
    # AC12 + C2-03/C2-14: factory wires all 4 modules on Settings().goals.db_path.
    from aios_core.config import Settings
    from aios_core.kernel import EventBus
    from aios_core.kernel.services import EventService, PolicyService
    from aios_core.orchestrator.goals import build_goal_modules

    settings = Settings()
    settings.goals.db_path = str(tmp_path / "goals.db")  # avoid polluting the repo
    bus = EventBus()
    event_service = EventService(bus, tmp_path / "audit.db")
    gm, tq, broker, recovery = build_goal_modules(
        settings, event_service, PolicyService(bus)
    )
    assert gm._db_path == tq._db_path  # noqa: SLF001 — shared db (C2-14)
    assert str(tq._db_path) == settings.goals.db_path  # noqa: SLF001 — config alive (C1-13)
    assert broker is not None and recovery is not None


def test_contracts_imports():
    assert ArtifactContract and CompatibilityChecker and ContractMetadata and ContractVersion
    assert Container and ContainerError
    assert ExecutionPlan and ExecutionPlanBuilder
    assert EventBus

