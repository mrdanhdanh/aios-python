"""Developer-facing component contracts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import AgentRequest, AgentResponse, ToolInput, ToolOutput
from .errors import ContractError


def _id(value: str, label: str) -> str:
    if not value or not value.strip() or any(ch.isspace() for ch in value):
        raise ContractError(f"{label} must be a non-empty identifier")
    return value


@dataclass(frozen=True)
class Capability:
    id: str
    version: str = "1.0.0"
    description: str = ""

    def __post_init__(self) -> None:
        _id(self.id, "capability id")


class Agent:
    id = ""
    version = "1.0.0"
    capabilities: tuple[str, ...] = ()

    def __init__(self, *, id: str | None = None, capabilities: tuple[str, ...] | list[str] | None = None) -> None:
        self.id = _id(id or self.id, "agent id")
        self.capabilities = tuple(capabilities if capabilities is not None else self.capabilities)

    def handle(self, request: AgentRequest) -> AgentResponse:
        raise NotImplementedError


class Tool:
    id = ""
    version = "1.0.0"
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

    def __init__(self, *, id: str | None = None, capabilities: tuple[str, ...] | list[str] | None = None, permissions: tuple[str, ...] | list[str] | None = None) -> None:
        self.id = _id(id or self.id, "tool id")
        self.capabilities = tuple(capabilities if capabilities is not None else self.capabilities)
        self.permissions = tuple(permissions if permissions is not None else self.permissions)
        if not self.capabilities:
            raise ContractError("tool must declare at least one capability")

    def run(self, input: ToolInput) -> ToolOutput:
        raise NotImplementedError


class Workflow:
    id = ""
    version = "1.0.0"

    def __init__(self, *, id: str | None = None, nodes: list[str] | tuple[str, ...] = (), edges: list[tuple[str, str]] | tuple[tuple[str, str], ...] = ()) -> None:
        self.id = _id(id or self.id, "workflow id")
        self.nodes = tuple(nodes)
        self.edges = tuple(edges)
        self.validate()

    def validate(self) -> None:
        if not self.nodes or len(set(self.nodes)) != len(self.nodes):
            raise ContractError("workflow must contain unique nodes")
        node_set = set(self.nodes)
        indegree = {node: 0 for node in self.nodes}
        outgoing = {node: [] for node in self.nodes}
        for source, target in self.edges:
            if source not in node_set or target not in node_set:
                raise ContractError("workflow edge references an unknown node")
            outgoing[source].append(target)
            indegree[target] += 1
        queue = [node for node, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            node = queue.pop(0)
            visited += 1
            for target in outgoing[node]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    queue.append(target)
        if visited != len(self.nodes):
            raise ContractError("workflow graph must be acyclic")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "version": self.version, "nodes": list(self.nodes), "edges": [list(edge) for edge in self.edges]}
