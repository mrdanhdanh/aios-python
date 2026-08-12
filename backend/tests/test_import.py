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


def test_contracts_imports():
    assert ArtifactContract and CompatibilityChecker and ContractMetadata and ContractVersion
    assert Container and ContainerError
    assert ExecutionPlan and ExecutionPlanBuilder
    assert EventBus

