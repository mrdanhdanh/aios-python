"""Enterprise shared contracts (M7 — Identity, Tenancy, Distributed, Governance,
Security, Operations).

All contracts use ``extra="forbid"`` (PLAN §Contracts) so unknown fields fail
fast. These are pure data models: no kernel/runtime services imported here —
the enterprise submodules compose them with injected dependencies.

M7 invariants covered (see ``backend/tests/test_architecture.py``):
    INV-022 Identity First        — ``Principal`` required on every execution
    INV-023 Tenant Isolation      — ``TenantScope`` + boundary deny-by-default
    INV-024 Credential Isolation  — ``CredentialRef`` scoped resolution
    INV-025 Resource Fairness     — ``Quota`` + usage accounting
    INV-026 Distributed Safety    — ``Lease`` single-active per execution
    INV-027 Audit Completeness    — ``AuditEvent`` structured evidence
    INV-028 Sandbox Boundary      — ``SandboxProfile`` + untrusted flag
    INV-029 Control Plane Isolation — ``RuntimeNodeInfo.tenant_classes``
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# --------------------------------------------------------------------------- #
# E1 — Identity                                                                #
# --------------------------------------------------------------------------- #

class PrincipalType(str, Enum):
    """Who is acting (PLAN §3 E1)."""

    USER = "user"
    SERVICE = "service"
    AGENT = "agent"
    WORKFLOW = "workflow"
    SYSTEM = "system"


class Principal(BaseModel):
    """Identity attached to every request (INV-022).

    A composite principal carries ``delegated_from`` to express a delegation
    chain (e.g. user → agent → workflow) with capability attenuation.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    type: PrincipalType
    tenant_id: str
    roles: list[str] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    # Delegation chain: the principal this identity acts on behalf of (if any).
    delegated_from: str | None = None
    # Attenuated scopes granted by the delegating principal (capability attenuation).
    scopes: list[str] = Field(default_factory=list)


def user_principal(
    user_id: str,
    tenant_id: str,
    roles: list[str] | None = None,
    attributes: dict[str, Any] | None = None,
) -> Principal:
    return Principal(
        id=user_id,
        type=PrincipalType.USER,
        tenant_id=tenant_id,
        roles=roles or [],
        attributes=attributes or {},
    )


def agent_principal(agent_id: str, tenant_id: str, delegated_from: str | None = None) -> Principal:
    return Principal(
        id=agent_id,
        type=PrincipalType.AGENT,
        tenant_id=tenant_id,
        delegated_from=delegated_from,
    )


def service_principal(service_id: str, tenant_id: str) -> Principal:
    return Principal(id=service_id, type=PrincipalType.SERVICE, tenant_id=tenant_id)


class Permission(BaseModel):
    """A single capability grant: ``action`` on ``resource`` (RBAC/ABAC)."""

    model_config = ConfigDict(extra="forbid")

    action: str
    resource: str
    effect: str = "allow"  # allow | deny


# --------------------------------------------------------------------------- #
# E2 — Tenancy                                                                 #
# --------------------------------------------------------------------------- #

class IsolationTier(str, Enum):
    """Tenant isolation spectrum (PLAN §4 E2)."""

    DEVELOPMENT = "development"  # shared
    STANDARD = "standard"  # logical isolation
    SECURE = "secure"  # sandbox
    ENTERPRISE = "enterprise"  # dedicated runtime


class TenantScope(BaseModel):
    """Ownership boundary for any enterprise object (INV-023)."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    project_id: str | None = None
    workspace_id: str | None = None


class Tenant(BaseModel):
    """A tenant (organization / team) within AIOS (PLAN §4 E2)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    tier: IsolationTier = IsolationTier.STANDARD


# --------------------------------------------------------------------------- #
# E3 — Distributed Runtime                                                     #
# --------------------------------------------------------------------------- #

class RuntimeNodeInfo(BaseModel):
    """Contract for a runtime node (INV-029 — tenant_classes gate access)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    region: str = "default"
    capacity: dict[str, float] = Field(default_factory=dict)  # cpu, memory(GB)
    capabilities: list[str] = Field(default_factory=list)
    health: str = "healthy"  # healthy | degraded | unhealthy
    version: str = "1.0.0"
    # Which tenant classes this node may serve (control-plane isolation).
    tenant_classes: list[str] = Field(default_factory=list)


class RoutingCriteria(BaseModel):
    """Inputs to the runtime router (PLAN §5 E3)."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    region: str | None = None
    capability: str | None = None
    tenant_class: str | None = None


# --------------------------------------------------------------------------- #
# E4 — Distributed Scheduler / Lease                                           #
# --------------------------------------------------------------------------- #

class Lease(BaseModel):
    """Single active lease per execution (INV-026)."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str
    node_id: str
    acquired_at: float
    expires_at: float
    heartbeat_at: float


# --------------------------------------------------------------------------- #
# E5 — Governance                                                              #
# --------------------------------------------------------------------------- #

class Quota(BaseModel):
    """Per-tenant resource quota (PLAN §7 E5)."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    concurrent_executions: int = 20
    cpu: float = 8.0
    memory_gb: float = 16.0
    llm_tokens_per_day: int = 5_000_000
    storage_gb: int = 100
    # Tool / sandbox limits (AI-specific quota).
    tool_calls_per_day: int = 100_000
    sandbox_seconds_per_day: int = 10_000


class CostEstimate(BaseModel):
    """Estimated cost of an execution (PLAN §7 E5)."""

    model_config = ConfigDict(extra="forbid")

    amount: float
    currency: str = "USD"
    model: str | None = None
    breakdown: dict[str, float] = Field(default_factory=dict)


class ResourceUsage(BaseModel):
    """Live accounting for fairness (INV-025)."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str
    active_executions: int = 0
    tokens_today: int = 0
    tool_calls_today: int = 0
    sandbox_seconds_today: int = 0


# --------------------------------------------------------------------------- #
# E6 — Security & Data Isolation                                               #
# --------------------------------------------------------------------------- #

class CredentialRef(BaseModel):
    """Scoped credential reference (INV-024).

    A credential is NEVER materialized outside its authorized scope. The broker
    resolves ``CredentialRef`` → short-lived token only inside the scope.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    project_id: str | None = None
    capability: str  # e.g. "github", "aws", "oracle"
    scopes: list[str] = Field(default_factory=list)
    expires_at: float | None = None
    # Secret material is resolved lazily by the broker; never stored here.
    secret_ref: str | None = None


class NetworkPolicy(BaseModel):
    """Default-deny network policy (PLAN §8 E6)."""

    model_config = ConfigDict(extra="forbid")

    deny: list[str] = Field(default_factory=list)
    allow: list[str] = Field(default_factory=list)


class SandboxProfile(BaseModel):
    """Sandbox boundary for untrusted execution (INV-028)."""

    model_config = ConfigDict(extra="forbid")

    filesystem_read: list[str] = Field(default_factory=list)
    filesystem_write: list[str] = Field(default_factory=list)
    network: bool = False
    cpu: float = 1.0
    memory_mb: int = 512
    timeout_s: float = 60.0
    # Untrusted tools MUST run under a sandbox profile.
    required: bool = False


# --------------------------------------------------------------------------- #
# E7 — Operations / Audit                                                      #
# --------------------------------------------------------------------------- #

class AuditEvent(BaseModel):
    """Structured, tamper-evident audit record (INV-027).

    ``previous_hash`` chains events for immutability; ``evidence`` carries the
    security-sensitive action details required for completeness.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float
    actor_id: str  # principal id (INV-022)
    action: str
    result: str  # success | denied | error
    tenant_id: str | None = None
    project_id: str | None = None
    agent_id: str | None = None
    workflow_id: str | None = None
    tool_id: str | None = None
    credential_scope: str | None = None
    policy_decision: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str | None = None
    hash: str | None = None


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DRAINING = "draining"
