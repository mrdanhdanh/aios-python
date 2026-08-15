"""TASK-035 — Identity & Access (E1).

Implements the Principal model, RBAC + ABAC, and delegation with capability
attenuation (PLAN §3 E1). Enforces INV-022 (Identity First): every execution
must carry a ``Principal``; anonymous execution is rejected at the boundary.

Design:
- ``RBACEngine`` resolves role → permission set (static, deterministic).
- ``ABACEngine`` evaluates attribute/resource/environment conditions.
- ``IdentityEngine`` composes both and validates principals (INV-022).
- ``DelegationChain`` supports composite principals + capability attenuation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import (
    Permission,
    Principal,
    PrincipalType,
    agent_principal,
    service_principal,
    user_principal,
)


# Re-export factories for convenience.
__all__ = [
    "Permission",
    "Principal",
    "PrincipalType",
    "RBACEngine",
    "ABACEngine",
    "IdentityEngine",
    "DelegationChain",
    "user_principal",
    "agent_principal",
    "service_principal",
    "NoPrincipalError",
]


class NoPrincipalError(Exception):
    """Raised when an execution lacks a required principal (INV-022)."""


# --------------------------------------------------------------------------- #
# RBAC                                                                         #
# --------------------------------------------------------------------------- #

class RBACEngine:
    """Role → permission set resolver (deterministic, no LLM)."""

    def __init__(self) -> None:
        # role -> set of "action:resource"
        self._roles: dict[str, set[str]] = {}
        self._static: set[str] = set()

    def define_role(self, role: str, permissions: list[Permission]) -> None:
        self._roles[role] = {
            f"{p.action}:{p.resource}" for p in permissions if p.effect == "allow"
        }

    def add_static_permission(self, action: str, resource: str) -> None:
        self._static.add(f"{action}:{resource}")

    def resolve(self, principal: Principal) -> set[str]:
        """All allowed ``action:resource`` strings for a principal."""
        granted: set[str] = set(self._static)
        for role in principal.roles:
            granted |= self._roles.get(role, set())
        # Apply attenuated scopes from delegation (capability attenuation).
        if principal.scopes:
            scoped = {s for s in principal.scopes if ":" in s or "*" in s}
            granted &= scoped if scoped else granted
        return granted

    def has_permission(self, principal: Principal, action: str, resource: str) -> bool:
        target = f"{action}:{resource}"
        allowed = self.resolve(principal)
        if target in allowed:
            return True
        # Wildcard support: "action:*" or "*:*"
        if f"{action}:*" in allowed:
            return True
        if "*:*" in allowed:
            return True
        return False


# --------------------------------------------------------------------------- #
# ABAC                                                                         #
# --------------------------------------------------------------------------- #

@dataclass
class ABACRule:
    """Attribute-based rule: allow/deny when ``condition`` holds."""

    effect: str  # allow | deny
    action: str
    condition: Callable[[Principal, str, dict[str, Any]], bool]


class ABACEngine:
    """Attribute/resource/environment based policy evaluation (PLAN §3 E1)."""

    def __init__(self) -> None:
        self._rules: list[ABACRule] = []

    def add_rule(
        self,
        effect: str,
        action: str,
        condition: Callable[[Principal, str, dict[str, Any]], bool],
    ) -> None:
        self._rules.append(ABACRule(effect=effect, action=action, condition=condition))

    def evaluate(
        self,
        principal: Principal,
        action: str,
        resource: dict[str, Any] | None = None,
    ) -> str:
        """Return 'allow' or 'deny'. Deny rules win (fail-closed)."""
        resource = resource or {}
        decision = "allow"
        for rule in self._rules:
            if rule.action not in (action, "*"):
                continue
            if rule.condition(principal, action, resource):
                if rule.effect == "deny":
                    return "deny"
                decision = "allow"
        return decision


# --------------------------------------------------------------------------- #
# Delegation                                                                   #
# --------------------------------------------------------------------------- #

@dataclass
class DelegationChain:
    """Composite principal with capability attenuation (PLAN §3 E1).

    A user delegates to an agent; the agent may only act within the scopes the
    user granted (attenuation). The chain is validated to be non-empty and the
    leaf must reference the delegating principal.
    """

    principal: Principal
    children: list["DelegationChain"] = field(default_factory=list)

    def all_principals(self) -> list[Principal]:
        out = [self.principal]
        for child in self.children:
            out.extend(child.all_principals())
        return out

    def validate(self) -> None:
        """Ensure delegation references are coherent (no orphan delegation)."""
        principals = {p.id: p for p in self.all_principals()}
        for p in self.all_principals():
            if p.delegated_from is not None:
                if p.delegated_from not in principals:
                    raise ValueError(
                        f"delegated_from {p.delegated_from!r} not in chain"
                    )


# --------------------------------------------------------------------------- #
# Identity Engine (INV-022)                                                    #
# --------------------------------------------------------------------------- #

class IdentityEngine:
    """Enforces Identity First (INV-022) and composes RBAC + ABAC."""

    def __init__(self, rbac: RBACEngine | None = None, abac: ABACEngine | None = None) -> None:
        self.rbac = rbac or RBACEngine()
        self.abac = abac or ABACEngine()

    @staticmethod
    def require(principal: Principal | None) -> Principal:
        """Enforce INV-022: a principal is mandatory for execution."""
        if principal is None:
            raise NoPrincipalError("INV-022: execution requires a Principal")
        if not principal.id or not principal.tenant_id:
            raise NoPrincipalError("INV-022: principal must have id + tenant_id")
        return principal

    def authorize(
        self,
        principal: Principal | None,
        action: str,
        resource: dict[str, Any] | None = None,
    ) -> bool:
        """Full authorization: identity present + RBAC + ABAC (fail-closed)."""
        self.require(principal)
        assert principal is not None
        # RBAC gate.
        if not self.rbac.has_permission(principal, action, resource.get("type", "*") if resource else "*"):
            return False
        # ABAC gate (resource dict must carry 'type' for resource matching).
        resource = resource or {}
        abac_decision = self.abac.evaluate(principal, action, resource)
        return abac_decision == "allow"
