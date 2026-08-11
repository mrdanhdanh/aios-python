"""Policy service: pre-execution policy evaluation (deny > approval > allow)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

from ...metadata import SEMVER_RE
from ...logging import get_logger
from ..events import Event, EventBus, EventType
from .permissions import PermissionScope

logger = get_logger("aios.kernel.services.policy")

DEFAULT_POLICY_VERSION = "0.1.0"


class Policy(BaseModel):
    """Policy rules. ``max_concurrent``/``sandbox_required`` are carried for
    TASK-005 (Resource/Execution services) — NOT evaluated here."""

    allow_scopes: list[str] = Field(default_factory=lambda: [PermissionScope.FILESYSTEM.value])
    deny_scopes: list[str] = Field(default_factory=list)
    require_approval: bool = False
    sandbox_required: bool = False
    allow_internet: bool = False
    max_tokens: int | None = None
    max_concurrent: int | None = None
    version: str = DEFAULT_POLICY_VERSION

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        if not SEMVER_RE.match(value):
            raise ValueError(f"Invalid semver: {value!r}")
        return value


@dataclass
class PolicyRequest:
    scopes: list[PermissionScope]
    tokens: int | None = None
    internet: bool = False
    sandbox: bool = False


@dataclass
class PolicyDecision:
    approved: bool
    requires_approval: bool = False
    sandbox_required: bool = False
    allow_internet: bool = False
    policy_version: str = DEFAULT_POLICY_VERSION
    reason: str = ""


class PolicyService:
    """Evaluate a request against the policy before execution.

    Precedence: deny > approval > allow. Scopes not listed in allow_scopes
    are treated as ASK (default-deny).
    """

    def __init__(self, bus: EventBus, policy: Policy | None = None) -> None:
        self._bus = bus
        self._policy = policy or Policy()

    @property
    def policy(self) -> Policy:
        return self._policy

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        p = self._policy

        # Deny wins: any denied scope → rejected (list all).
        denied = [s.value for s in request.scopes if s.value in p.deny_scopes]
        if denied:
            return PolicyDecision(
                approved=False,
                policy_version=p.version,
                reason=f"denied scopes: {denied}",
            )

        # Token budget.
        if p.max_tokens is not None and request.tokens is not None and request.tokens > p.max_tokens:
            return PolicyDecision(
                approved=False,
                policy_version=p.version,
                reason=f"token budget exceeded: {request.tokens} > {p.max_tokens}",
            )

        # Internet gate.
        if request.internet and not p.allow_internet:
            return PolicyDecision(
                approved=False,
                policy_version=p.version,
                reason="internet access not allowed by policy",
            )

        # Approval: require_approval or any scope not in allow (default-deny → ASK).
        ask_scopes = [s.value for s in request.scopes if s.value not in p.allow_scopes]
        needs_approval = p.require_approval or bool(ask_scopes)
        if needs_approval:
            request_id = str(uuid.uuid4())
            self._bus.publish(
                Event(
                    type=EventType.PERMISSION_REQUESTED,
                    payload={
                        "service": "policy",
                        "request_id": request_id,
                        "scopes": [s.value for s in request.scopes],
                        "ask_scopes": ask_scopes,
                    },
                    source="policy_service",
                )
            )
            return PolicyDecision(
                approved=True,
                requires_approval=True,
                sandbox_required=p.sandbox_required,
                allow_internet=p.allow_internet,
                policy_version=p.version,
                reason=f"approval required for scopes: {ask_scopes or 'policy rule'}",
            )

        return PolicyDecision(
            approved=True,
            sandbox_required=p.sandbox_required,
            allow_internet=p.allow_internet,
            policy_version=p.version,
            reason="policy allows",
        )
