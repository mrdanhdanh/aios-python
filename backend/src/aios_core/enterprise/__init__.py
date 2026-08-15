"""AIOS Enterprise package (M7 — P12).

Bundles the 7 enterprise groups (E1–E7) behind a single facade
``EnterpriseManager`` that the Control Plane uses to enforce the 8 M7
architecture invariants (INV-022..INV-029). Each subsystem is independently
testable and composed via dependency injection — no god object.

Public API:
    from aios_core.enterprise import EnterpriseManager, IdentityEngine, ...
"""

from __future__ import annotations

from .contracts import (
    AuditEvent,
    CredentialRef,
    HealthStatus,
    IsolationTier,
    Lease,
    NetworkPolicy,
    Permission,
    Principal,
    PrincipalType,
    Quota,
    RuntimeNodeInfo,
    RoutingCriteria,
    SandboxProfile,
    Tenant,
    TenantScope,
)
from .dashboard import EnterpriseDashboard
from .governance import (
    BudgetExceeded,
    CostEstimate,
    CostGovernor,
    QuotaExceeded,
    QuotaManager,
    ResourceUsage,
)
from .identity import (
    ABACEngine,
    DelegationChain,
    IdentityEngine,
    NoPrincipalError,
    RBACEngine,
    agent_principal,
    service_principal,
    user_principal,
)
from .operations import (
    AuditError,
    CentralAuditStore,
    HealthMonitor,
    RecoveryManager,
)
from .runtime import (
    ControlPlaneIsolationError,
    NodeNotFoundError,
    NodeRegistry,
    RuntimeRouter,
)
from .scheduler import DistributedScheduler, LeaseError, LeaseManager
from .security import (
    CredentialBroker,
    CredentialError,
    NetworkPolicyEngine,
    SandboxBoundary,
    SandboxBypassError,
)
from .tenancy import (
    CrossTenantAccessDenied,
    MemoryNamespace,
    TenancyManager,
    TenantBoundary,
    TenantNotFoundError,
    TenantRegistry,
)


class EnterpriseManager:
    """Control-plane facade composing all M7 subsystems (INV-022..INV-029).

    Constructed with injected dependencies where the real runtime differs from
    offline defaults; the default constructor wires the in-memory subsystems so
    the package is usable and testable without external services (offline-first).
    """

    def __init__(
        self,
        identity: IdentityEngine | None = None,
        tenancy: TenancyManager | None = None,
        nodes: NodeRegistry | None = None,
        leases: LeaseManager | None = None,
        quotas: QuotaManager | None = None,
        costs: CostGovernor | None = None,
        credentials: CredentialBroker | None = None,
        network: NetworkPolicyEngine | None = None,
        sandbox: SandboxBoundary | None = None,
        audit: CentralAuditStore | None = None,
        health: HealthMonitor | None = None,
        recovery: RecoveryManager | None = None,
    ) -> None:
        self.identity = identity or IdentityEngine()
        self.tenancy = tenancy or TenancyManager()
        self.nodes = nodes or NodeRegistry()
        self.leases = leases or LeaseManager()
        self.quotas = quotas or QuotaManager()
        self.costs = costs or CostGovernor()
        self.credentials = credentials or CredentialBroker()
        self.network = network or NetworkPolicyEngine()
        self.sandbox = sandbox or SandboxBoundary()
        self.audit = audit or CentralAuditStore()
        self.health = health or HealthMonitor()
        self.recovery = recovery or RecoveryManager()
        self.router = RuntimeRouter(self.nodes)
        self.dashboard = EnterpriseDashboard(self.audit)

    # -- INV-022: identity first ------------------------------------------------
    def require_principal(self, principal: Principal | None) -> Principal:
        return self.identity.require(principal)

    # -- INV-023: tenant isolation ---------------------------------------------
    def enforce_tenant(self, owner: TenantScope, accessor_tenant_id: str) -> None:
        self.tenancy.enforce_isolation(owner, accessor_tenant_id)

    # -- INV-024: credential isolation -----------------------------------------
    def resolve_credential(
        self,
        credential_id: str,
        tenant_id: str,
        capability: str,
        project_id: str | None = None,
    ) -> str:
        token = self.credentials.resolve(credential_id, tenant_id, capability, project_id)
        self.audit.record(
            actor_id=tenant_id,
            action="credential.resolved",
            result="success",
            tenant_id=tenant_id,
            credential_scope=capability,
            evidence={"credential_id": credential_id},
        )
        return token

    # -- INV-025: resource fairness --------------------------------------------
    def begin_execution(self, tenant_id: str, override: bool = False) -> None:
        self.quotas.begin(tenant_id, override=override)
        self.audit.record(
            actor_id=tenant_id,
            action="execution.started",
            result="success",
            tenant_id=tenant_id,
        )

    # -- INV-026: distributed execution safety --------------------------------
    def acquire_lease(self, execution_id: str, node_id: str, ttl_s: float = 60.0) -> Lease:
        lease = self.leases.acquire(execution_id, node_id, ttl_s=ttl_s)
        self.audit.record(
            actor_id=node_id,
            action="lease.acquired",
            result="success",
            evidence={"execution_id": execution_id, "node_id": node_id},
        )
        return lease

    # -- INV-027: audit completeness -------------------------------------------
    def deny(self, actor_id: str, reason: str, tenant_id: str | None = None) -> None:
        self.audit.record(
            actor_id=actor_id,
            action="authz.denied",
            result="denied",
            tenant_id=tenant_id,
            policy_decision=reason,
            evidence={"reason": reason},
        )

    # -- INV-028: sandbox boundary ---------------------------------------------
    def require_sandbox(self, profile_name: str | None, untrusted: bool) -> SandboxProfile:
        try:
            return self.sandbox.require_sandbox(profile_name, untrusted)
        except SandboxBypassError:
            self.audit.record(
                actor_id="system",
                action="sandbox.bypassed",
                result="denied",
                evidence={"profile": profile_name},
            )
            raise

    # -- INV-029: control plane isolation --------------------------------------
    def route(self, tenant_id: str, tenant_class: str | None = None,
              region: str | None = None, capability: str | None = None):
        from .contracts import RoutingCriteria

        return self.router.select(
            RoutingCriteria(
                tenant_id=tenant_id,
                tenant_class=tenant_class,
                region=region,
                capability=capability,
            )
        )


__all__ = [
    "EnterpriseManager",
    "IdentityEngine",
    "RBACEngine",
    "ABACEngine",
    "DelegationChain",
    "NoPrincipalError",
    "TenancyManager",
    "TenantRegistry",
    "TenantBoundary",
    "MemoryNamespace",
    "CrossTenantAccessDenied",
    "TenantNotFoundError",
    "NodeRegistry",
    "RuntimeRouter",
    "NodeNotFoundError",
    "ControlPlaneIsolationError",
    "LeaseManager",
    "DistributedScheduler",
    "LeaseError",
    "QuotaManager",
    "CostGovernor",
    "QuotaExceeded",
    "BudgetExceeded",
    "CredentialBroker",
    "CredentialError",
    "NetworkPolicyEngine",
    "SandboxBoundary",
    "SandboxBypassError",
    "CentralAuditStore",
    "AuditError",
    "HealthMonitor",
    "RecoveryManager",
    "EnterpriseDashboard",
    "Principal",
    "PrincipalType",
    "Tenant",
    "TenantScope",
    "IsolationTier",
    "RuntimeNodeInfo",
    "RoutingCriteria",
    "Lease",
    "Quota",
    "ResourceUsage",
    "CostEstimate",
    "CredentialRef",
    "NetworkPolicy",
    "SandboxProfile",
    "AuditEvent",
    "Permission",
    "HealthStatus",
]
