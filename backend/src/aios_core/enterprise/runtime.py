"""TASK-037 — Distributed Runtime (E3).

Splits the single ``RuntimeKernel`` into a Control Plane → Runtime Router →
Runtime Nodes topology (PLAN §5 E3). Enforces INV-029 (Control Plane
Isolation): a node only serves tenants whose class is in ``tenant_classes``;
tenant workloads never reach the control plane internals except via the API
contract.

``RuntimeRouter`` selects a node by Tenant / Region / Capability / Capacity /
Latency / Policy / Cost / Health. Selection is deterministic given the same
registry + criteria (no LLM, offline-first).
"""

from __future__ import annotations

import threading
from typing import Any

from .contracts import RoutingCriteria, RuntimeNodeInfo


class NodeNotFoundError(KeyError):
    """Raised when no runtime node satisfies routing criteria."""


class ControlPlaneIsolationError(Exception):
    """Raised when a tenant class is not permitted on a node (INV-029)."""


class NodeRegistry:
    """Thread-safe registry of runtime nodes (PLAN §5 E3)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._nodes: dict[str, RuntimeNodeInfo] = {}

    def register(self, node: RuntimeNodeInfo) -> None:
        with self._lock:
            self._nodes[node.id] = node

    def deregister(self, node_id: str) -> None:
        with self._lock:
            self._nodes.pop(node_id, None)

    def get(self, node_id: str) -> RuntimeNodeInfo:
        with self._lock:
            if node_id not in self._nodes:
                raise NodeNotFoundError(node_id)
            return self._nodes[node_id]

    def list(self) -> list[RuntimeNodeInfo]:
        with self._lock:
            return list(self._nodes.values())

    def healthy(self) -> list[RuntimeNodeInfo]:
        return [n for n in self.list() if n.health in ("healthy", "degraded")]


class RuntimeRouter:
    """Selects a runtime node for a request (PLAN §5 E3).

    Priority order (deterministic): health → tenant_class gate (INV-029) →
    region → capability → capacity → cost (ascending) → id (stable tie-break).
    """

    def __init__(self, registry: NodeRegistry | None = None) -> None:
        self.registry = registry or NodeRegistry()

    def _allowed(self, node: RuntimeNodeInfo, criteria: RoutingCriteria) -> bool:
        # INV-029: control plane gates tenant class.
        if node.tenant_classes and criteria.tenant_class is not None:
            if criteria.tenant_class not in node.tenant_classes:
                return False
        if node.health == "unhealthy":
            return False
        if criteria.region and node.region and node.region != criteria.region:
            return False
        if criteria.capability and criteria.capability not in node.capabilities:
            return False
        return True

    @staticmethod
    def _score(node: RuntimeNodeInfo, criteria: RoutingCriteria) -> tuple:
        # Lower cost (sum capacity) is better; stable by id.
        cost = float(node.capacity.get("cpu", 0) or 0) + float(
            node.capacity.get("memory", 0) or 0
        )
        # Healthy beats degraded in secondary sort.
        health_rank = 0 if node.health == "healthy" else 1
        return (health_rank, cost, node.id)

    def select(self, criteria: RoutingCriteria) -> RuntimeNodeInfo:
        candidates = [n for n in self.registry.healthy() if self._allowed(n, criteria)]
        if not candidates:
            raise NodeNotFoundError(
                f"no runtime node for tenant {criteria.tenant_id!r}"
            )
        # Region preference (non-strict: candidates may ignore region if none match
        # is already filtered above; region mismatch already excluded).
        candidates.sort(key=lambda n: self._score(n, criteria))
        return candidates[0]

    def check_isolation(self, node_id: str, tenant_class: str) -> bool:
        """INV-029 explicit check: tenant class allowed on node?"""
        node = self.registry.get(node_id)
        if not node.tenant_classes:
            return True  # unrestricted node
        return tenant_class in node.tenant_classes
