"""Model router (TASK-025 §YC-9): policy-driven selection + policy-bounded fallback.

Pure orchestration — no filter/cost logic here (INV-013 no-God-object; the
six modules below own their responsibilities).
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Callable

from ..base import ChatMessage, ChatResponse
from ..capability import ModelCapability  # noqa: F401
from ..errors import ModelError, RouterError
from ..registry import ModelRegistry
from .availability import AvailabilityChecker
from .contracts import (
    HealthConfig,
    ModelRouterConfig,
    PolicyRule,
    RejectedCandidate,
    RouteDecision,
    RouteRequest,
    RoutingPolicy,
)
from .cost import estimate_cost, latency_ms, quality_score
from .fallback import FallbackResolver
from .health import ModelHealth
from .selector import ModelCandidate, ModelSelector, SelectorResult


class ModelRouter:
    """Routes a request to a model via policy; falls back within policy."""

    def __init__(
        self,
        registry: ModelRegistry,
        policy: RoutingPolicy,
        config: ModelRouterConfig | None = None,
        health: ModelHealth | None = None,
        availability: AvailabilityChecker | None = None,
        selector: ModelSelector | None = None,
        fallback: FallbackResolver | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._registry = registry
        self._policy = policy
        self._config = config or ModelRouterConfig()
        self._health = health or ModelHealth(HealthConfig())
        self._selector = selector or ModelSelector(availability)
        self._fallback = fallback or FallbackResolver(self._health, availability)
        self._now = now
        self._last_decision: RouteDecision | None = None
        self._lock = threading.RLock()

    @property
    def last_decision(self) -> RouteDecision | None:
        with self._lock:
            return self._last_decision

    # -- selection -----------------------------------------------------------

    def select(self, request: RouteRequest) -> RouteDecision:
        policy_name = (request.policy or self._policy.default) or "balanced"
        if policy_name != "balanced" and policy_name not in self._policy.policies:
            raise RouterError(f"unknown policy: {policy_name!r}")
        rule = self._policy.rule(policy_name)

        all_candidates = self._candidates()
        health_rejected = [
            RejectedCandidate(name=c.name, reason="health")
            for c in all_candidates
            if not self._health.can_use(c.name)
        ]
        considered = [c for c in all_candidates if self._health.can_use(c.name)]

        result: SelectorResult = self._selector.select(
            considered,
            rule,
            request,
            policy_name=policy_name,
            canonical_prompt=self._config.canonical_prompt_tokens,
            canonical_completion=self._config.canonical_completion_tokens,
        )
        decision = RouteDecision(
            model_name=result.model_name,
            policy_used=policy_name,
            rule_applied=rule is not None,
            candidates_considered=[c.name for c in considered],
            rejected=health_rejected + result.rejected,
            cost_estimate=(
                estimate_cost(
                    self._registry.capability(result.model_name),
                    request.prompt_tokens or self._config.canonical_prompt_tokens,
                    request.completion_tokens or self._config.canonical_completion_tokens,
                )
                if result.model_name
                else 0.0
            ),
            quality_score=(
                quality_score(self._registry.capability(result.model_name))
                if result.model_name
                else 0.0
            ),
            latency_class=(
                self._registry.capability(result.model_name).latency_class
                if result.model_name
                else "medium"
            ),
            health_snapshot={
                name: status.value
                for name, status in self._health.snapshot().items()
            },
            fallback_chain=[],
            created_at=self._now(),
        )
        with self._lock:
            self._last_decision = decision
        return decision

    def _candidates(self) -> list[ModelCandidate]:
        candidates: list[ModelCandidate] = []
        for name in self._registry.list():
            capability = self._registry.capability(name)
            candidates.append(
                ModelCandidate(
                    name=name,
                    capability=capability,
                    model=self._registry.get(name),
                )
            )
        return candidates

    # -- chat with fallback ----------------------------------------------------

    def chat(self, messages: list[ChatMessage], request: RouteRequest) -> ChatResponse:
        decision = self.select(request)
        if decision.model_name is None:
            reasons = ", ".join(
                f"{r.name}:{r.reason}" for r in decision.rejected
            ) or "no model"
            raise RouterError(f"no model available ({reasons})")

        policy_name = decision.policy_used
        rule = self._policy.rule(policy_name)
        all_candidates = self._candidates()
        excluded: set[str] = set()
        chain: list[str] = []
        attempts = 0
        name: str | None = decision.model_name
        last_error: ModelError | None = None
        while name is not None:
            if self._config.max_attempts is not None and attempts >= self._config.max_attempts:
                break
            attempts += 1
            chain.append(name)
            try:
                response = self._registry.get(name).chat(messages)
            except ModelError as exc:
                last_error = exc
                self._health.record_failure(name, exc)
                excluded.add(name)
                next_candidate = self._fallback.next(
                    all_candidates,
                    rule,
                    excluded,
                    request,
                    canonical_prompt=self._config.canonical_prompt_tokens,
                    canonical_completion=self._config.canonical_completion_tokens,
                )
                name = next_candidate.name if next_candidate is not None else None
                continue
            self._health.record_success(name)
            if not response.model:
                response.model = name
            final_decision = decision.model_copy(
                update={
                    "model_name": name,
                    "fallback_chain": chain,
                    "created_at": self._now(),
                }
            )
            with self._lock:
                self._last_decision = final_decision
            return response
        if last_error is not None:
            raise last_error
        raise ModelError(f"all models failed: {chain}")
