"""TASK-075 — Performance & Cost (M10-F4)."""

from __future__ import annotations

import pytest

from aios_core.models.capability import ModelCapability
from aios_core.observability.performance import (
    CostAggregator,
    CostEstimator,
    PerformanceMetrics,
    TokenEstimate,
)


# ---------------------------------------------------------------------------
# AC2: cost công thức chuẩn
# ---------------------------------------------------------------------------

def test_model_cost_formula():
    cap = ModelCapability(model_id="gpt", provider="openai",
                          input_cost=1.0, output_cost=2.0)
    estimator = CostEstimator(capabilities=lambda m: cap)
    cost = estimator.model_cost(TokenEstimate(model_id="gpt", tokens_in=1_000_000,
                                              tokens_out=500_000))
    assert cost == pytest.approx(1.0 + 1.0)  # 1M in × 1.0 + 0.5M out × 2.0


def test_model_cost_unknown_capability_zero():
    estimator = CostEstimator(capabilities=lambda m: None)
    assert estimator.model_cost(TokenEstimate(model_id="x", tokens_in=1000)) == 0.0


def test_tool_cost():
    estimator = CostEstimator(tool_cost_per_call=0.001)
    assert estimator.tool_cost(10) == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# AC3/AC4: aggregate + cost per success
# ---------------------------------------------------------------------------

def test_aggregate_empty_no_crash():
    dash = CostAggregator(CostEstimator()).build()
    assert dash.total_cost == 0.0
    assert dash.cost_per_success is None  # 0 success → SKIPPED


def test_aggregate_full():
    cap = ModelCapability(model_id="m1", provider="mock", input_cost=1.0, output_cost=1.0)
    dash = CostAggregator(
        CostEstimator(capabilities=lambda m: cap),
        token_estimates=[TokenEstimate(model_id="m1", tokens_in=1_000_000, tokens_out=0)],
        tool_calls_by_tool={"python": 5},
        workflow_success={"wf-a": (2, 3), "wf-b": (1, 1)},
        goal_workflows={"goal-1": ["wf-a", "wf-b"]},
    ).build()
    assert dash.total_cost == pytest.approx(1.0 + 0.005)
    assert dash.cost_per_tool["python"] == pytest.approx(0.005)
    assert dash.cost_per_success == pytest.approx((1.0 + 0.005) / 3)
    assert dash.cost_per_goal["goal-1"] > 0


# ---------------------------------------------------------------------------
# AC1: performance metrics
# ---------------------------------------------------------------------------

def test_performance_empty_metrics():
    snap = PerformanceMetrics(metrics_svc=None, artifact_dir="__nonexistent__").snapshot()
    assert snap.workflow_count == 0
    assert snap.storage_bytes == 0
    assert snap.avg_workflow_latency_ms == 0.0


def test_performance_storage_size(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.bin").write_bytes(b"x" * 10)
    snap = PerformanceMetrics(metrics_svc=None, artifact_dir=str(tmp_path)).snapshot()
    assert snap.storage_bytes == 15


def test_performance_with_metrics(tmp_path):
    from aios_core.kernel.events import Event, EventType
    from aios_core.observability.metrics import MetricsService

    svc = MetricsService(__import__("aios_core.kernel.events", fromlist=["EventBus"]).EventBus(),
                         tmp_path / "m.db")
    for i in range(2):
        svc._on_event(Event(type=EventType.WORKFLOW_STARTED,
                            payload={"execution_id": f"e{i}", "plan_id": "p"}, source="t"))
        svc._on_event(Event(type=EventType.WORKFLOW_COMPLETED,
                            payload={"execution_id": f"e{i}", "plan_id": "p"}, source="t"))
    snap = PerformanceMetrics(svc, str(tmp_path)).snapshot()
    assert snap.workflow_count == 2
    assert snap.avg_workflow_latency_ms >= 0


# ---------------------------------------------------------------------------
# AC7: model independence — 3 provider đều ModelContract
# ---------------------------------------------------------------------------

def test_model_provider_contract_uniform():
    from aios_core.models import MockModel
    from aios_core.models.base import ModelContract
    from aios_core.models.ollama_provider import OllamaModel
    from aios_core.models.openai_provider import OpenAIModel

    providers = [MockModel(echo=True), OllamaModel(), OpenAIModel()]
    for p in providers:
        assert isinstance(p, ModelContract)
        assert p.name
        assert p.metadata() is not None
        assert p.is_available() in (True, False)


def test_registry_swap_keeps_api():
    from aios_core.models import ModelRegistry

    registry = ModelRegistry(default_name="mock")
    registry.register("mock", __import__("aios_core.models", fromlist=["MockModel"]).MockModel(echo=True))
    # swap provider — API dùng không đổi
    for name in registry.list():
        model = registry.get(name)
        assert hasattr(model, "chat") and hasattr(model, "metadata")


# ---------------------------------------------------------------------------
# AC5/AC6: CLI
# ---------------------------------------------------------------------------

def test_cli_cost_and_performance(capsys):
    from aios_core.workflow.cli import main

    assert main(["cost"]) == 0
    assert main(["performance"]) == 0
    out = capsys.readouterr().out
    assert "total_cost" in out
    assert "storage_bytes" in out
