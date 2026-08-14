"""AIOS model layer: contract, providers, registry, capability, router.

Import order (TASK-025 C3-04): base → errors → capability → registry →
router (avoids cycles; router imports registry + capability).
"""

from .base import ChatMessage, ChatResponse, ModelContract
from .capability import ModelCapability
from .errors import (
    ModelError,
    ModelNotAvailableError,
    ModelRateLimitError,
    ModelTimeoutError,
    RouterError,
)
from .mock import MockModel
from .ollama_provider import OllamaModel
from .openai_provider import OpenAIModel
from .registry import ModelRegistry
from .router import (
    AvailabilityChecker,
    FallbackResolver,
    HealthConfig,
    HealthStatus,
    ModelCandidate,
    ModelHealth,
    ModelRouter,
    ModelRouterConfig,
    ModelSelector,
    PolicyRule,
    RejectedCandidate,
    RouteDecision,
    RouteRequest,
    RoutingPolicy,
)

__all__ = [
    "AvailabilityChecker",
    "ChatMessage",
    "ChatResponse",
    "FallbackResolver",
    "HealthConfig",
    "HealthStatus",
    "ModelCandidate",
    "ModelCapability",
    "ModelContract",
    "ModelError",
    "ModelHealth",
    "ModelNotAvailableError",
    "ModelRateLimitError",
    "ModelRouter",
    "ModelRouterConfig",
    "ModelSelector",
    "ModelTimeoutError",
    "MockModel",
    "OllamaModel",
    "OpenAIModel",
    "PolicyRule",
    "RejectedCandidate",
    "RouteDecision",
    "RouteRequest",
    "RouterError",
    "RoutingPolicy",
    "ModelRegistry",
]
