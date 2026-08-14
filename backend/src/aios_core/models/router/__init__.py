"""Model router (TASK-025): policy-driven selection + fallback."""

from .availability import AvailabilityChecker
from .contracts import (
    HealthConfig,
    HealthStatus,
    ModelRouterConfig,
    PolicyRule,
    RejectedCandidate,
    RouteDecision,
    RouteRequest,
    RoutingPolicy,
)
from .cost import (
    balanced_score,
    cost_rate,
    cost_score,
    estimate_cost,
    latency_ms,
    latency_score,
    quality_score,
)
from .fallback import FallbackResolver
from .health import ModelHealth
from .router import ModelRouter
from .selector import ModelCandidate, ModelSelector, SelectorResult

__all__ = [
    "AvailabilityChecker",
    "FallbackResolver",
    "HealthConfig",
    "HealthStatus",
    "ModelCandidate",
    "ModelHealth",
    "ModelRouter",
    "ModelRouterConfig",
    "ModelSelector",
    "PolicyRule",
    "RejectedCandidate",
    "RouteDecision",
    "RouteRequest",
    "RoutingPolicy",
    "SelectorResult",
    "balanced_score",
    "cost_rate",
    "cost_score",
    "estimate_cost",
    "latency_ms",
    "latency_score",
    "quality_score",
]
