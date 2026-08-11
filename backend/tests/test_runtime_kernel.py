"""RuntimeKernel tests: wiring, lifecycle, end-to-end."""

from aios_core.config import AuditSettings, ArtifactsSettings, ResourcesSettings, Settings
from aios_core.kernel import RuntimeKernel
from aios_core.kernel.events import EventBus
from aios_core.kernel.execution_plan import ExecutionPlanBuilder
from aios_core.kernel.services import (
    ArtifactService,
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


def make_settings(tmp_path):
    return Settings(
        audit=AuditSettings(db_path=str(tmp_path / "audit.db")),
        artifacts=ArtifactsSettings(dir=str(tmp_path / "artifacts")),
        resources=ResourcesSettings(max_tokens=1000, max_concurrent=2),
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
    ):
        assert c.resolve(interface) is not None


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
