"""Model capability metadata (PLAN §8.1) — static routing facts.

Stored on the registry (TASK-025), NOT on ModelContract: providers stay
unchanged (additive only). ``availability`` is a STATIC flag — routing never
calls ``model.is_available()`` (Ollama = HTTP call, breaks offline determinism).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ModelCapability(BaseModel):
    """Routing-relevant model metadata (PLAN §8.1)."""

    model_config = ConfigDict(extra="forbid")

    model_id: str
    provider: str
    context_window: int = 0  # 0 = unknown
    input_cost: float = 0.0  # USD per 1M tokens
    output_cost: float = 0.0  # USD per 1M tokens
    latency_class: Literal["fast", "medium", "slow"] = "medium"
    reasoning: bool = False
    coding: bool = False
    vision: bool = False
    tool_calling: bool = False
    structured_output: bool = False
    availability: bool = True  # STATIC flag (C2-05 v1: no is_available call)

    @field_validator("input_cost", "output_cost")
    @classmethod
    def _validate_cost(cls, value: float) -> float:
        if value < 0:
            raise ValueError("cost must be >= 0")
        return value

    @field_validator("context_window")
    @classmethod
    def _validate_window(cls, value: int) -> int:
        if value < 0:
            raise ValueError("context_window must be >= 0")
        return value

    @classmethod
    def default(cls, model_id: str, availability: bool = True) -> "ModelCapability":
        """Deterministic defaults for providers without declared capability."""
        provider = model_id.split(":", 1)[0] if ":" in model_id else model_id
        return cls(
            model_id=model_id,
            provider=provider,
            availability=availability,
        )