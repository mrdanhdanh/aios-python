"""Model selector (TASK-025 §YC-6): deterministic filter -> rank -> pick.

Pure orchestration over cost/availability helpers; never calls the model,
never does network I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..base import ModelContract
from ..capability import ModelCapability
from .availability import AvailabilityChecker
from .contracts import PolicyRule, RejectedCandidate, RouteRequest
from .cost import (
    balanced_score,
    cost_rate,
    estimate_cost,
    latency_ms,
    quality_score,
)

# Rank keys per policy name (deterministic; None = balanced behavior).
_RANK_KEY = {
    "cheap": lambda cap: cost_rate(cap),
    "fast": lambda cap: latency_ms(cap),
    "quality": lambda cap: -quality_score(cap),  # desc via negation
    "local": lambda cap: -balanced_score(cap),
    "balanced": lambda cap: -balanced_score(cap),
    None: lambda cap: -balanced_score(cap),
}


@dataclass(frozen=True)
class ModelCandidate:
    """A routable model: registry name + capability + provider instance."""

    name: str
    capability: ModelCapability
    model: ModelContract


@dataclass(frozen=True)
class SelectorResult:
    model_name: str | None
    rejected: list[RejectedCandidate]
    ranking: list[tuple[str, float]]


class ModelSelector:
    """Filter candidates by rule, rank by policy, pick the best."""

    def __init__(self, availability: AvailabilityChecker | None = None) -> None:
        self._availability = availability or AvailabilityChecker()

    def select(
        self,
        candidates: list[ModelCandidate],
        rule: PolicyRule | None,
        request: RouteRequest,
        policy_name: str = "balanced",
        canonical_prompt: int = 1000,
        canonical_completion: int = 1000,
    ) -> SelectorResult:
        prompt = request.prompt_tokens if request.prompt_tokens is not None else canonical_prompt
        completion = request.completion_tokens if request.completion_tokens is not None else canonical_completion
        rejected: list[RejectedCandidate] = []
        kept: list[ModelCandidate] = []
        for candidate in candidates:
            cap = candidate.capability
            if not self._availability.is_available(cap):
                rejected.append(RejectedCandidate(name=candidate.name, reason="unavailable"))
                continue
            if rule is None:
                kept.append(candidate)
                continue
            if rule.max_cost is not None:
                cost = estimate_cost(cap, prompt, completion)
                if cost > rule.max_cost:
                    rejected.append(RejectedCandidate(name=candidate.name, reason="cost"))
                    continue
            if rule.max_latency_ms is not None and latency_ms(cap) > rule.max_latency_ms:
                rejected.append(RejectedCandidate(name=candidate.name, reason="latency"))
                continue
            if rule.min_quality is not None and quality_score(cap) < rule.min_quality:
                rejected.append(RejectedCandidate(name=candidate.name, reason="quality"))
                continue
            if rule.providers is not None and cap.provider not in rule.providers:
                rejected.append(RejectedCandidate(name=candidate.name, reason="provider"))
                continue
            kept.append(candidate)

        rank_key = _RANK_KEY.get(policy_name, _RANK_KEY[None])
        ranked = sorted(
            ((c, rank_key(c.capability)) for c in kept),
            key=lambda pair: (pair[1], pair[0].name),
        )
        ranking = [(c.name, round(v, 6)) for c, v in ranked]
        model_name = ranked[0][0].name if ranked else None
        return SelectorResult(model_name=model_name, rejected=rejected, ranking=ranking)
