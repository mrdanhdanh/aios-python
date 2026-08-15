"""TASK-036 — Multi-Tenancy (E2).

Enforces INV-023 (Tenant Isolation): cross-tenant access is denied by default
at every boundary (API, context, memory, registry, runtime, storage, tool,
audit). Implements the ownership model ``Organization → Tenant → Project →
Workspace → Execution`` and memory-namespace isolation so Tenant A memory is
never retrievable by Tenant B (PLAN §4 E2).

The boundary is fail-closed: missing or mismatched scope → deny/raise.
"""

from __future__ import annotations

import threading
from typing import Any

from .contracts import IsolationTier, Tenant, TenantScope


class TenantNotFoundError(KeyError):
    """Raised when a tenant id is unknown."""


class CrossTenantAccessDenied(Exception):
    """Raised when a cross-tenant access is attempted (INV-023)."""


class TenantRegistry:
    """Thread-safe registry of tenants (PLAN §4 E2)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tenants: dict[str, Tenant] = {}

    def register(self, tenant: Tenant) -> None:
        with self._lock:
            self._tenants[tenant.id] = tenant

    def get(self, tenant_id: str) -> Tenant:
        with self._lock:
            if tenant_id not in self._tenants:
                raise TenantNotFoundError(tenant_id)
            return self._tenants[tenant_id]

    def exists(self, tenant_id: str) -> bool:
        with self._lock:
            return tenant_id in self._tenants

    def list(self) -> list[Tenant]:
        with self._lock:
            return list(self._tenants.values())

    def isolation_tier(self, tenant_id: str) -> IsolationTier:
        return self.get(tenant_id).tier


class TenantBoundary:
    """Enforces cross-tenant denial at every boundary (INV-023).

    ``enforce`` raises ``CrossTenantAccessDenied`` when ``accessor`` tries to
    touch an object owned by a different tenant. ``may_access`` is the Boolean
    variant for callers that prefer to branch instead of raise.
    """

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict

    def enforce(self, owner: TenantScope, accessor_tenant_id: str) -> None:
        if owner.tenant_id != accessor_tenant_id:
            raise CrossTenantAccessDenied(
                f"INV-023: tenant {accessor_tenant_id!r} cannot access "
                f"tenant {owner.tenant_id!r} object"
            )

    def may_access(self, owner: TenantScope, accessor_tenant_id: str) -> bool:
        try:
            self.enforce(owner, accessor_tenant_id)
            return True
        except CrossTenantAccessDenied:
            return False


class MemoryNamespace:
    """Per-tenant memory namespace (INV-023 memory isolation, PLAN §4 E2).

    A tenant's retriever only sees its own namespace. Cross-namespace retrieval
    is blocked by the boundary.
    """

    def __init__(self, tenant_id: str, boundary: TenantBoundary | None = None) -> None:
        self.tenant_id = tenant_id
        self._boundary = boundary or TenantBoundary()
        self._store: dict[str, Any] = {}
        self._namespace_id = f"memory:{tenant_id}"

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, accessor_tenant_id: str) -> Any:
        # INV-023: even the owner can only read within their own namespace.
        self._boundary.enforce(
            TenantScope(tenant_id=self.tenant_id), accessor_tenant_id
        )
        return self._store.get(key)

    @property
    def namespace_id(self) -> str:
        return self._namespace_id


class TenancyManager:
    """Composes registry + boundary + memory namespaces (TASK-036 facade)."""

    def __init__(self, registry: TenantRegistry | None = None) -> None:
        self.registry = registry or TenantRegistry()
        self.boundary = TenantBoundary()
        self._namespaces: dict[str, MemoryNamespace] = {}

    def namespace(self, tenant_id: str) -> MemoryNamespace:
        if tenant_id not in self._namespaces:
            self._namespaces[tenant_id] = MemoryNamespace(tenant_id, self.boundary)
        return self._namespaces[tenant_id]

    def enforce_isolation(self, owner: TenantScope, accessor_tenant_id: str) -> None:
        self.boundary.enforce(owner, accessor_tenant_id)
