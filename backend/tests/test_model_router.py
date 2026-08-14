"""TASK-025 — Model Router tests (M5-P9): capability, registry API, policy,
cost, health, selector, fallback, router, INV-013, integration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from aios_core.models import (
    ChatMessage,
    ChatResponse,
    ModelCapability,
    ModelContract,
    ModelError,
    ModelNotAvailableError,
    ModelRateLimitError,
    ModelRegistry,
    ModelTimeoutError,
    RouterError,
)
from aios_core.models.router import (
    AvailabilityChecker,
    FallbackResolver,
    HealthConfig,
    HealthStatus,
    ModelHealth,
    ModelRouter,
    ModelRouterConfig,
    ModelSelector,
    PolicyRule,
    RouteDecision,
    RouteRequest,
    RoutingPolicy,
    SelectorResult,
    cost_rate,
    estimate_cost,
    latency_ms,
    quality_score,
)
from aios_core.models.router.selector import ModelCandidate

FIXED_NOW = datetime(2026, 8, 14, tzinfo=timezone.utc)


def make_cap(model_id: str, **kw) -> ModelCapability:
    return ModelCapability(model_id=model_id, provider=kw.pop("provider", model_id.split(":")[0] if ":" in model_id else model_id), **kw)


class FakeProvider(ModelContract):
    """Deterministic fake provider for router tests."""

    def __init__(self, name: str, error: Exception | None = None, text: str = "ok") -> None:
        self._name = name
        self._error = error
        self._text = text
        self.calls = 0

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return True

    def metadata(self):
        from aios_core.metadata import make_component_metadata
        return make_component_metadata(id=f"models.{self._name}", name=self._name, version="1.0.0")

    def _chat(self, messages, temperature, max_tokens) -> ChatResponse:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return ChatResponse(content=self._text, model=self._name)


def make_registry(entries: dict[str, tuple[ModelContract, ModelCapability]]) -> ModelRegistry:
    reg = ModelRegistry(default_name="mock")
    for name, (model, capability) in entries.items():
        reg.register(name, model, capability=capability)
    return reg


def make_router(entries, policy_data=None, **router_kw) -> tuple[ModelRouter, ModelRegistry]:
    reg = make_registry(entries)
    policy = RoutingPolicy.from_settings(policy_data or {"default": "balanced", "policies": {}})
    router = ModelRouter(registry=reg, policy=policy, now=lambda: FIXED_NOW, **router_kw)
    return router, reg


# ---------------------------------------------------------------------------
# YC-1 — ModelCapability
# ---------------------------------------------------------------------------

class TestCapability:
    def test_fields_and_forbid(self):
        with pytest.raises(ValidationError):
            make_cap("x", bogus=1)
        with pytest.raises(ValidationError):
            make_cap("x", latency_class="turbo")
        with pytest.raises(ValidationError):
            make_cap("x", input_cost=-1)

    def test_default_provider_parsing(self):
        c = ModelCapability.default("ollama:llama3.2")
        assert c.provider == "ollama"
        assert c.input_cost == 0.0
        assert c.reasoning is False
        assert c.availability is True
        c2 = ModelCapability.default("mock")
        assert c2.provider == "mock"


# ---------------------------------------------------------------------------
# YC-2 — Registry capability API
# ---------------------------------------------------------------------------

class TestRegistryCapability:
    def test_roundtrip(self):
        reg = ModelRegistry()
        reg.register_capability("m", make_cap("m", coding=True))
        assert reg.capability("m").coding is True
        assert list(reg.capabilities().keys()) == ["m"]

    def test_unknown_raises(self):
        reg = ModelRegistry()
        with pytest.raises(ModelError):
            reg.capability("nope")

    def test_register_with_capability(self):
        reg = ModelRegistry()
        reg.register("m", FakeProvider("m"), capability=make_cap("m", coding=True))
        assert reg.capability("m").coding is True

    def test_register_default_no_is_available(self):
        reg = ModelRegistry()
        provider = FakeProvider("m")
        reg.register("m", provider)  # no capability kwarg
        c = reg.capability("m")
        assert c.availability is True
        assert c.provider == "m"

    def test_duck_typed_capability_called_once(self):
        class CapProvider(FakeProvider):
            def capability(self) -> ModelCapability:
                return make_cap("m", vision=True)

        reg = ModelRegistry()
        provider = CapProvider("m")
        reg.register("m", provider)
        assert reg.capability("m").vision is True

    def test_overwrite_warns_not_crash(self):
        reg = ModelRegistry()
        reg.register_capability("m", make_cap("m"))
        reg.register_capability("m", make_cap("m", coding=True))  # warn, no crash
        assert reg.capability("m").coding is True


# ---------------------------------------------------------------------------
# YC-3 — Routing Policy
# ---------------------------------------------------------------------------

class TestPolicy:
    PLAN_POLICY = {
        "default": "balanced",
        "policies": {
            "cheap": {"max_cost": 0.01},
            "fast": {"max_latency_ms": 2000},
            "quality": {"min_quality": 0.9},
            "local": {"providers": ["ollama"]},
        },
    }

    def test_parse_plan_policies(self):
        p = RoutingPolicy.from_settings(self.PLAN_POLICY)
        assert p.rule("cheap").max_cost == 0.01
        assert p.rule("fast").max_latency_ms == 2000
        assert p.rule("local").providers == ["ollama"]

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            PolicyRule(max_budget=1)

    def test_min_quality_range(self):
        with pytest.raises(ValidationError):
            PolicyRule(min_quality=1.5)

    def test_balanced_reserved(self):
        with pytest.raises(ValidationError):
            RoutingPolicy(default="balanced", policies={"balanced": PolicyRule()})

    def test_default_must_exist(self):
        with pytest.raises(ValidationError):
            RoutingPolicy(default="nope", policies={})

    def test_empty_rule_accepted(self):
        p = RoutingPolicy.from_settings({"default": "balanced", "policies": {"x": {}}})
        assert p.rule("x") is not None

    def test_rule_balanced_none(self):
        p = RoutingPolicy.from_settings(self.PLAN_POLICY)
        assert p.rule("balanced") is None
        assert p.rule("nope") is None


# ---------------------------------------------------------------------------
# YC-4 — CostEstimator
# ---------------------------------------------------------------------------

class TestCost:
    def test_estimate(self):
        c = make_cap("m", input_cost=0.15, output_cost=0.60)
        assert cost_rate(c) == 0.75
        assert estimate_cost(c, 1000, 1000) == 0.00075

    def test_quality_score(self):
        c = make_cap("m", reasoning=True, coding=True, tool_calling=True,
                     structured_output=True)
        assert quality_score(c) == 0.85  # 0.3+0.3+0+0.15+0.1

    def test_latency_mapping(self):
        assert latency_ms(make_cap("m", latency_class="fast")) == 1000
        assert latency_ms(make_cap("m", latency_class="medium")) == 5000
        assert latency_ms(make_cap("m", latency_class="slow")) == 15000


# ---------------------------------------------------------------------------
# YC-5 — AvailabilityChecker
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_static_flag(self):
        checker = AvailabilityChecker()
        assert checker.is_available(make_cap("m", availability=True)) is True
        assert checker.is_available(make_cap("m", availability=False)) is False


# ---------------------------------------------------------------------------
# YC-6 — ModelSelector (PLAN §23 numbers per C1-01)
# ---------------------------------------------------------------------------

class TestSelector:
    def _selector(self):
        return ModelSelector()

    def _candidates(self, specs: dict[str, ModelCapability]):
        return [
            ModelCandidate(name=n, capability=c, model=FakeProvider(n))
            for n, c in specs.items()
        ]

    def test_cheap_policy(self):
        """C1-01: cost_rate 0.005/5.0/20.0 -> estimate 1e-5/0.01/0.04 vs max 0.01."""
        candidates = self._candidates({
            "cheap-m": make_cap("cheap-m", input_cost=0.0025, output_cost=0.0025),
            "mid-m": make_cap("mid-m", input_cost=2.5, output_cost=2.5),
            "exp-m": make_cap("exp-m", input_cost=10.0, output_cost=10.0),
        })
        result = self._selector().select(
            candidates, PolicyRule(max_cost=0.01), RouteRequest(), policy_name="cheap")
        assert result.model_name == "cheap-m"
        reasons = {r.name: r.reason for r in result.rejected}
        assert reasons["exp-m"] == "cost"
        assert "mid-m" not in reasons  # == max_cost passes (<=)

    def test_fast_policy(self):
        candidates = self._candidates({
            "fast-m": make_cap("fast-m", latency_class="fast"),
            "medium-m": make_cap("medium-m", latency_class="medium"),
        })
        result = self._selector().select(
            candidates, PolicyRule(max_latency_ms=2000), RouteRequest(), policy_name="fast")
        assert result.model_name == "fast-m"

    def test_quality_policy(self):
        candidates = self._candidates({
            "q-0.9": make_cap("q-0.9", reasoning=True, coding=True, vision=True, tool_calling=True),
            "q-0.85": make_cap("q-0.85", reasoning=True, coding=True, vision=True),
        })
        result = self._selector().select(
            candidates, PolicyRule(min_quality=0.9), RouteRequest(), policy_name="quality")
        assert result.model_name == "q-0.9"

    def test_local_policy(self):
        candidates = self._candidates({
            "ollama:x": make_cap("ollama:x", provider="ollama"),
            "openai:y": make_cap("openai:y", provider="openai"),
        })
        result = self._selector().select(
            candidates, PolicyRule(providers=["ollama"]), RouteRequest(), policy_name="local")
        assert result.model_name == "ollama:x"

    def test_balanced_no_filter(self):
        candidates = self._candidates({
            "a": make_cap("a", reasoning=True),
            "b": make_cap("b"),
        })
        result = self._selector().select(candidates, None, RouteRequest(), policy_name="balanced")
        assert result.model_name == "a"  # higher quality -> higher balanced

    def test_tie_break_name_asc(self):
        candidates = self._candidates({
            "b-model": make_cap("b-model"),
            "a-model": make_cap("a-model"),
        })
        result = self._selector().select(candidates, None, RouteRequest(), policy_name="balanced")
        assert result.model_name == "a-model"

    def test_unavailable_rejected(self):
        candidates = self._candidates({
            "off": make_cap("off", availability=False),
            "on": make_cap("on"),
        })
        result = self._selector().select(candidates, None, RouteRequest(), policy_name="balanced")
        assert result.model_name == "on"
        assert result.rejected[0].reason == "unavailable"

    def test_deterministic(self):
        candidates = self._candidates({"a": make_cap("a"), "b": make_cap("b", coding=True)})
        r1 = self._selector().select(candidates, None, RouteRequest(), policy_name="balanced")
        r2 = self._selector().select(candidates, None, RouteRequest(), policy_name="balanced")
        assert r1.model_name == r2.model_name


# ---------------------------------------------------------------------------
# YC-7 — FallbackResolver
# ---------------------------------------------------------------------------

class TestFallback:
    def test_excluded_skipped(self):
        health = ModelHealth(now=lambda: FIXED_NOW)
        fb = FallbackResolver(health)
        cands = [
            ModelCandidate("a", make_cap("a"), FakeProvider("a")),
            ModelCandidate("b", make_cap("b"), FakeProvider("b")),
            ModelCandidate("c", make_cap("c"), FakeProvider("c")),
        ]
        assert fb.next(cands, None, {"a"}, RouteRequest()).name == "b"
        assert fb.next(cands, None, {"a", "b"}, RouteRequest()).name == "c"

    def test_health_blocked(self):
        health = ModelHealth(now=lambda: FIXED_NOW)
        health.record_failure("b", ModelTimeoutError("t"))
        fb = FallbackResolver(health)
        cands = [
            ModelCandidate("a", make_cap("a"), FakeProvider("a")),
            ModelCandidate("b", make_cap("b"), FakeProvider("b")),
            ModelCandidate("c", make_cap("c"), FakeProvider("c")),
        ]
        # b in cooldown -> skipped
        assert fb.next(cands, None, set(), RouteRequest()).name == "a"

    def test_rule_rejected(self):
        health = ModelHealth(now=lambda: FIXED_NOW)
        fb = FallbackResolver(health)
        cands = [
            ModelCandidate("cheap", make_cap("cheap", input_cost=0.0025, output_cost=0.0025), FakeProvider("cheap")),
            ModelCandidate("exp", make_cap("exp", input_cost=10.0, output_cost=10.0), FakeProvider("exp")),
        ]
        result = fb.next(cands, PolicyRule(max_cost=0.01), set(), RouteRequest())
        assert result.name == "cheap"

    def test_all_excluded_none(self):
        health = ModelHealth(now=lambda: FIXED_NOW)
        fb = FallbackResolver(health)
        cands = [ModelCandidate("a", make_cap("a"), FakeProvider("a"))]
        assert fb.next(cands, None, {"a"}, RouteRequest()) is None


# ---------------------------------------------------------------------------
# YC-8 — ModelHealth
# ---------------------------------------------------------------------------

class TestHealth:
    def _health(self):
        return ModelHealth(
            config=HealthConfig(cooldown_seconds=30, max_failures_before_disable=3),
            now=lambda: FIXED_NOW,
        )

    def test_transition_table(self):
        h = self._health()
        h.record_failure("m", ModelTimeoutError("t"))
        assert h.status("m") is HealthStatus.DEGRADED
        assert h.can_use("m") is True
        h.record_failure("m", ModelTimeoutError("t"))
        assert h.status("m") is HealthStatus.COOLDOWN
        assert h.can_use("m") is False
        # after cooldown -> OK (failures stay)
        h._now = lambda: FIXED_NOW + timedelta(seconds=31)
        assert h.status("m") is HealthStatus.OK
        assert h.can_use("m") is True
        # 3rd failure -> DISABLED
        h.record_failure("m", ModelTimeoutError("t"))
        assert h.status("m") is HealthStatus.DISABLED
        assert h.can_use("m") is False

    def test_success_resets(self):
        h = self._health()
        h.record_failure("m", ModelTimeoutError("t"))
        h.record_failure("m", ModelTimeoutError("t"))
        h.record_success("m")
        assert h.status("m") is HealthStatus.OK
        assert h.can_use("m") is True

    def test_snapshot_sorted(self):
        h = self._health()
        h.record_failure("b", ModelTimeoutError("t"))
        h.record_failure("a", ModelTimeoutError("t"))
        assert list(h.snapshot().keys()) == ["a", "b"]

    def test_unknown_ok(self):
        h = self._health()
        assert h.status("nope") is HealthStatus.OK


# ---------------------------------------------------------------------------
# YC-9 — ModelRouter
# ---------------------------------------------------------------------------

class TestRouter:
    def _router(self, entries, policy_data=None, **kw):
        return make_router(entries, policy_data, **kw)[0]

    def test_select_balanced(self):
        router = self._router({"mock": (FakeProvider("mock"), make_cap("mock"))})
        d = router.select(RouteRequest())
        assert d.model_name == "mock"
        assert d.policy_used == "balanced"
        assert d.cost_estimate >= 0

    def test_select_unknown_policy_raises(self):
        router = self._router({"mock": (FakeProvider("mock"), make_cap("mock"))})
        with pytest.raises(RouterError):
            router.select(RouteRequest(policy="nope"))

    def test_select_no_model(self):
        router = self._router({"off": (FakeProvider("off"), make_cap("off", availability=False))})
        d = router.select(RouteRequest())
        assert d.model_name is None
        assert any(r.reason == "unavailable" for r in d.rejected)

    def test_select_no_chat_calls(self):
        provider = FakeProvider("mock")
        router = self._router({"mock": (provider, make_cap("mock"))})
        router.select(RouteRequest())
        assert provider.calls == 0  # offline determinism

    def test_chat_fallback_chain(self):
        a = FakeProvider("a", error=ModelTimeoutError("t"))
        b = FakeProvider("b")
        router = self._router({"a": (a, make_cap("a")), "b": (b, make_cap("b"))})
        response = router.chat([ChatMessage(role="user", content="hi")], RouteRequest())
        assert response.content == "ok"
        assert response.model == "b"
        assert router.last_decision.fallback_chain == ["a", "b"]

    def test_chat_rate_limit_fallback(self):
        a = FakeProvider("a", error=ModelRateLimitError("rl"))
        b = FakeProvider("b")
        router = self._router({"a": (a, make_cap("a")), "b": (b, make_cap("b"))})
        response = router.chat([ChatMessage(role="user", content="hi")], RouteRequest())
        assert response.model == "b"

    def test_chat_all_fail(self):
        a = FakeProvider("a", error=ModelTimeoutError("t"))
        b = FakeProvider("b", error=ModelNotAvailableError("na"))
        router = self._router({"a": (a, make_cap("a")), "b": (b, make_cap("b"))})
        with pytest.raises(ModelError):
            router.chat([ChatMessage(role="user", content="hi")], RouteRequest())

    def test_chat_max_attempts_1(self):
        a = FakeProvider("a", error=ModelTimeoutError("t"))
        b = FakeProvider("b")
        router, _ = make_router(
            {"a": (a, make_cap("a")), "b": (b, make_cap("b"))},
        )
        router._config = ModelRouterConfig(max_attempts=1)
        with pytest.raises(ModelTimeoutError):
            router.chat([ChatMessage(role="user", content="hi")], RouteRequest())
        assert b.calls == 0  # cap: only 1 attempt


# ---------------------------------------------------------------------------
# YC-10/11 — config + integration (wiring-level)
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_routing_from_config_yaml(self, tmp_path, monkeypatch):
        from pathlib import Path
        from aios_core.config import load_settings
        # Point at the repo config.yaml (real file) via AIOS_CONFIG_PATH.
        repo_config = Path(__file__).resolve().parents[1] / "config.yaml"
        monkeypatch.setenv("AIOS_CONFIG_PATH", str(repo_config))
        monkeypatch.chdir(tmp_path)  # no CWD config interference
        settings = load_settings()
        assert settings.models.routing.default == "balanced"
        assert settings.models.routing.policies["cheap"].max_cost == 0.01

    def test_env_override_scalar(self, tmp_path, monkeypatch):
        from aios_core.config import load_settings
        monkeypatch.delenv("AIOS_CONFIG_PATH", raising=False)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("AIOS_MODELS__ROUTING__DEFAULT", "cheap")
        settings = load_settings()
        assert settings.models.routing.default == "cheap"

    def test_env_override_dict_nested(self, tmp_path, monkeypatch):
        from aios_core.config import load_settings
        monkeypatch.delenv("AIOS_CONFIG_PATH", raising=False)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("AIOS_MODELS__ROUTING__POLICIES__CHEAP__MAX_COST", "0.05")
        settings = load_settings()
        assert settings.models.routing.policies["cheap"].max_cost == 0.05

    def test_models_typo_rejected(self, tmp_path, monkeypatch):
        from aios_core.config import Settings
        with pytest.raises(ValidationError):
            Settings(_env_file=None, models={"routingg": {"default": "x"}})

    def test_router_wired_in_kernel(self, tmp_path):
        from aios_core.config import Settings
        from aios_core.kernel import RuntimeKernel
        settings = Settings()
        settings.audit.db_path = str(tmp_path / "a.db")
        settings.artifacts.dir = str(tmp_path / "art")
        settings.memory.conversation_db_path = str(tmp_path / "c.db")
        settings.memory.knowledge_db_path = str(tmp_path / "k.db")
        settings.goals.db_path = str(tmp_path / "g.db")
        settings.skills.db_path = str(tmp_path / "s.db")
        settings.observability.db_path = str(tmp_path / "o.db")
        kernel = RuntimeKernel.create(settings)
        router = kernel.container.resolve(ModelRouter)
        d = router.select(RouteRequest())
        assert d.model_name == "mock"


# ---------------------------------------------------------------------------
# INV-013 behavioral
# ---------------------------------------------------------------------------

def test_inv013_policy_followed():
    """PLAN §23: cheap -> cheapest; timeout -> fallback order; offline calls==0."""
    entries = {
        "cheap-m": (FakeProvider("cheap-m"), make_cap("cheap-m", input_cost=0.0025, output_cost=0.0025)),
        "exp-m": (FakeProvider("exp-m"), make_cap("exp-m", input_cost=10.0, output_cost=10.0)),
    }
    policy_data = {"default": "cheap", "policies": {"cheap": {"max_cost": 0.01}}}
    router, reg = make_router(entries, policy_data)
    d = router.select(RouteRequest())
    assert d.model_name == "cheap-m"
    # exp-m must NEVER be chosen even as fallback (INV-013)
    fb = FallbackResolver(router._health)
    result = fb.next(
        [ModelCandidate(n, c, m) for n, (m, c) in entries.items()],
        PolicyRule(max_cost=0.01), set(), RouteRequest())
    assert result.name == "cheap-m"
    # offline: mock with 0 LLM calls
    provider = FakeProvider("offline")
    router2, _ = make_router({"offline": (provider, make_cap("offline"))})
    router2.select(RouteRequest())
    assert provider.calls == 0
