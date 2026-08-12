"""Workflow compilers: declarative definition → engine ExecutionPlan."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from ..kernel.execution_plan import (
    ExecutionPlan,
    ExecutionPlanStatus,
    PlanNode,
)
from .definition import WorkflowDefinition
from .errors import WorkflowError


class WorkflowCompiler(ABC):
    """Compile a WorkflowDefinition into an engine ExecutionPlan."""

    @abstractmethod
    def compile(self, definition: WorkflowDefinition) -> ExecutionPlan: ...

    def is_available(self) -> bool:
        return True


class MockCompiler(WorkflowCompiler):
    """Offline compiler (default) — used by simulation and tests."""

    def compile(self, definition: WorkflowDefinition) -> ExecutionPlan:
        nodes = []
        for wnode in definition.nodes:
            nodes.append(
                PlanNode(
                    id=wnode.id,
                    type=wnode.type,
                    name=wnode.name,
                    agent=wnode.agent,
                    capabilities=list(wnode.capabilities),
                    depends_on=list(wnode.depends_on),
                    # Merge: node override > definition default > PlanNode default.
                    timeout_s=wnode.timeout_s if wnode.timeout_s is not None else definition.timeout_s,
                    retries=wnode.retries if wnode.retries is not None else definition.retries,
                )
            )
        return ExecutionPlan(
            id=f"wf:{definition.name}",
            request_ref=definition.name,
            nodes=nodes,
            required_permissions=list(definition.permissions),
            required_resources=dict(definition.resources),
            status=ExecutionPlanStatus.READY,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class LangGraphCompiler(WorkflowCompiler):
    """Stub — real LangGraph integration lands in M2 (workflow engine swap)."""

    def compile(self, definition: WorkflowDefinition) -> ExecutionPlan:
        raise NotImplementedError("LangGraphCompiler is not implemented in v1 (M2)")

    def is_available(self) -> bool:
        return False


def get_compiler(name: str = "mock") -> WorkflowCompiler:
    if name == "mock":
        return MockCompiler()
    if name == "langgraph":
        return LangGraphCompiler()
    raise WorkflowError(f"unknown compiler: {name!r}")
