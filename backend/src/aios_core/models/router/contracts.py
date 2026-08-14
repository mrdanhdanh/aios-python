"""Model router contracts (TASK-025): policy, request, decision, health."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

_RESERVED_POLICY = "balanced"


class PolicyRule(BaseModel):
    """Deterministic filter constraints (PLAN §8). Unknown field -> error."""

    model_config = ConfigDict(extra="forbid")

    max_cost: float | None = None  # USD per request (canonical tokens when absent)
    max_latency_ms: int | None = None
    min_quality: float | None = None  # 0..1
    providers: list[str] | None = None

    @model_validator(mode="after")
    def _validate(self) -> "PolicyRule":
        if self.max_cost is not None and self.max_cost < 0:
            raise ValueError("max_cost must be >= 0")
        if self.max_latency_ms is not None and self.max_latency_ms <= 0:
            raise ValueError("max_latency_ms must be > 0")
        if self.min_quality is not None and not (0.0 <= self.min_quality <= 1.0):
            raise ValueError("min_quality must be in [0, 1]")
        if self.providers is not None:
            if not self.providers or any(p.strip() == "" for p in self.providers):
                raise ValueError("providers must be non-empty without blank entries")
        return self


class RoutingPolicy(BaseModel):
    """Named routing policies (PLAN §8). ``balanced`` is reserved."""

    model_config = ConfigDict(extra="forbid")

    default: str = _RESERVED_POLICY
    policies: dict[str, PolicyRule] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate(self) -> "RoutingPolicy":
        if self.default != _RESERVED_POLICY and self.default not in self.policies:
            raise ValueError(f"unknown default policy: {self.default!r}")  # C2-07 v1
        if _RESERVED_POLICY in self.policies:
            raise ValueError("'balanced' is a reserved policy name")
        return self

    @classmethod
    def from_settings(cls, data: dict[str, Any]) -> "RoutingPolicy":
        """Build from settings dict (``RoutingSettings.model_dump()``)."""
        return cls(
            default=data.get("default", _RESERVED_POLICY),
            policies={
                name: PolicyRule(**rule)
                for name, rule in (data.get("policies") or {}).items()
            },
        )

    def rule(self, name: str) -> PolicyRule | None:
        """Rule for a policy name; ``balanced`` and unknown -> None (no filter)."""
        return self.policies.get(name)


class RouteRequest(BaseModel):
    """Model routing request (tokens optional — canonical fallback)."""

    model_config = ConfigDict(extra="forbid")

    policy: str | None = None  # None -> policy.default
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    @model_validator(mode="after")
    def _validate(self) -> "RouteRequest":
        for field in ("prompt_tokens", "completion_tokens"):
            value = getattr(self, field)
            if value is not None and value < 0:
                raise ValueError(f"{field} must be >= 0")
        return self


class RejectedCandidate(BaseModel):
    """A candidate excluded from selection, with a deterministic reason."""

    model_config = ConfigDict(extra="forbid")

    name: str
    reason: str  # unavailable | cost | latency | quality | provider | health | no-capability


class RouteDecision(BaseModel):
    """Result of a routing decision (never calls the model)."""

    model_config = ConfigDict(extra="forbid")

    model_name: str | None
    policy_used: str
    rule_applied: bool
    candidates_considered: list[str]
    rejected: list[RejectedCandidate]
    cost_estimate: float
    quality_score: float
    latency_class: str
    health_snapshot: dict[str, str]  # model -> HealthStatus.value
    fallback_chain: list[str]
    created_at: datetime


class HealthStatus(str, Enum):
    """Dynamic model health (TASK-025 §YC-8)."""

    OK = "ok"
    DEGRADED = "degraded"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"


class HealthConfig(BaseModel):
    """ModelHealth tuning."""

    model_config = ConfigDict(extra="forbid")

    cooldown_seconds: float = 30.0
    max_failures_before_disable: int = 3

    @model_validator(mode="after")
    def _validate(self) -> "HealthConfig":
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        if self.max_failures_before_disable < 1:
            raise ValueError("max_failures_before_disable must be >= 1")
        return self


class ModelRouterConfig(BaseModel):
    """Router tuning. ``max_attempts=None`` -> try the whole chain (C2-06 v1)."""

    model_config = ConfigDict(extra="forbid")

    max_attempts: int | None = None
    canonical_prompt_tokens: int = 1000  # fallback when request omits tokens
    canonical_completion_tokens: int = 1000

    @model_validator(mode="after")
    def _validate(self) -> "ModelRouterConfig":
        if self.max_attempts is not None and self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1 (or None)")
        if self.canonical_prompt_tokens < 0 or self.canonical_completion_tokens < 0:
            raise ValueError("canonical tokens must be >= 0")
        return self
