"""AIOS core package: config, logging, metadata, healthcheck, kernel foundations."""

__version__ = "0.1.0"

from . import agents, capabilities, catalog, contracts, knowledge, knowledge_graph, memory, models, orchestrator, prompts, sandbox, skills, tools, workflow
from .config import Settings, load_settings
from .container import Container, ContainerError, Scope
from .healthcheck import (
    HealthCheck,
    HealthRegistry,
    HealthReport,
    HealthStatus,
)
from .kernel import (
    Event,
    EventBus,
    EventType,
    ExecutionPlan,
    ExecutionPlanBuilder,
    Subscription,
)
from .logging import get_logger, set_correlation_id, setup_logging
from .metadata import AiOSMetadata, make_component_metadata

__all__ = [
    "__version__",
    "contracts",
    "models",
    "memory",
    "knowledge",
    "workflow",
    "capabilities",
    "prompts",
    "catalog",
    "knowledge_graph",
    "orchestrator",
    "Settings",
    "load_settings",
    "Container",
    "ContainerError",
    "Scope",
    "HealthCheck",
    "HealthRegistry",
    "HealthReport",
    "HealthStatus",
    "Event",
    "EventBus",
    "EventType",
    "Subscription",
    "ExecutionPlan",
    "ExecutionPlanBuilder",
    "get_logger",
    "set_correlation_id",
    "setup_logging",
    "AiOSMetadata",
    "make_component_metadata",
]
