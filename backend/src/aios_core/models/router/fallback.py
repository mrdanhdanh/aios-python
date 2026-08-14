"""Fallback resolver (TASK-025 §YC-7): next candidate respecting policy.

Receives RAW candidates (unfiltered registry list) and re-applies the rule
each hop (defense-in-depth, C3-02 v1) + health block + excluded set. Never
returns a model outside the policy.
"""

from __future__ import annotations

from datetime import datetime

from ..capability import ModelCapability  # noqa: F401
from .availability import AvailabilityChecker
from .contracts import PolicyRule, RouteRequest
from .cost import estimate_cost, latency_ms, quality_score
from .health import ModelHealth
from .selector import ModelCandidate


class FallbackResolver:
    """Picks the next usable candidate under the same routing rule."""

    def __init__(
        self,
        health: ModelHealth,
        availability: AvailabilityChecker | None = None,
    ) -> None:
        self._health = health
        self._availability = availability or AvailabilityChecker()

    def next(
        self,
        all_candidates: list[ModelCandidate],
        rule: PolicyRule | None,
        excluded: set[str],
        request: RouteRequest,
        canonical_prompt: int = 1000,
        canonical_completion: int = 1000,
    ) -> ModelCandidate | None:
        prompt = request.prompt_tokens if request.prompt_tokens is not None else canonical_prompt
        completion = request.completion_tokens if request.completion_tokens is not None else canonical_completion
        for candidate in all_candidates:  # deterministic registry order
            if candidate.name in excluded:
                continue
            if not self._availability.is_available(candidate.capability):
                continue
            if not self._health.can_use(candidate.name):
                continue
            if rule is not None:
                if rule.max_cost is not None and estimate_cost(
                    candidate.capability, prompt, completion
                ) > rule.max_cost:
                    continue
                if rule.max_latency_ms is not None and latency_ms(
                    candidate.capability
                ) > rule.max_latency_ms:
                    continue
                if rule.min_quality is not None and quality_score(
                    candidate.capability
                ) < rule.min_quality:
                    continue
                if rule.providers is not None and (
                    candidate.capability.provider not in rule.providers
                ):
                    continue
            return candidate
        return None
