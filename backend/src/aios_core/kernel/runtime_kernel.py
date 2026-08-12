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

        # Remaining services are constructed via the container (type-only hints).
        container.register(PermissionService, PermissionService)
        container.register(PolicyService, PolicyService)
        container.register(SchedulerService, SchedulerService)
        container.register(StateService, StateService)
        container.register(ResourceService, ResourceService)
        container.register(ExecutionService, ExecutionService)

        return cls(container, bus)
