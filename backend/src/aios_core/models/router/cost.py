"""Cost/quality/latency metrics (TASK-025) — pure deterministic functions."""

from __future__ import annotations

from ..capability import ModelCapability  # noqa: F401 (re-export convenience)

#: Latency representative per class (ms) — PLAN-free constant, documented.
LATENCY_MS = {"fast": 1000, "medium": 5000, "slow": 15000}
LATENCY_SCORE = {"fast": 1.0, "medium": 0.6, "slow": 0.3}

#: USD per 1M tokens at which cost_score reaches 0.
COST_SCALE = 0.1

#: Fixed quality weights (sum = 1.0).
QUALITY_WEIGHTS = {
    "reasoning": 0.30,
    "coding": 0.30,
    "vision": 0.15,
    "tool_calling": 0.15,
    "structured_output": 0.10,
}


def cost_rate(cap: ModelCapability) -> float:
    """USD per 1M tokens (input + output)."""
    return cap.input_cost + cap.output_cost


def estimate_cost(cap: ModelCapability, prompt_tokens: int, completion_tokens: int) -> float:
    """USD per request: (input*pt + output*ct) / 1e6."""
    return (cap.input_cost * prompt_tokens + cap.output_cost * completion_tokens) / 1_000_000


def quality_score(cap: ModelCapability) -> float:
    """0..1 — fixed weights over capability flags (rounded: FP-safety)."""
    return round(
        sum(
            QUALITY_WEIGHTS[key] * float(bool(getattr(cap, key)))
            for key in QUALITY_WEIGHTS
        ),
        6,
    )


def latency_ms(cap: ModelCapability) -> int:
    return LATENCY_MS[cap.latency_class]


def latency_score(cap: ModelCapability) -> float:
    return LATENCY_SCORE[cap.latency_class]


def cost_score(cap: ModelCapability) -> float:
    """1 - min(cost_rate / COST_SCALE, 1) — cheaper models score higher."""
    return 1.0 - min(cost_rate(cap) / COST_SCALE, 1.0)


def balanced_score(cap: ModelCapability) -> float:
    """0.5*quality + 0.3*latency + 0.2*cost (PLAN §8 default 'balanced')."""
    return (
        0.5 * quality_score(cap)
        + 0.3 * latency_score(cap)
        + 0.2 * cost_score(cap)
    )
