"""Model contract: ChatMessage, ChatResponse, ModelContract ABC.

Contract-first: providers implement ``_chat``; the base ``chat`` validates
inputs so every provider behaves consistently (important for simulation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from ..metadata import AiOSMetadata


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatResponse(BaseModel):
    content: str
    model: str = ""
    usage: dict[str, int] = Field(default_factory=dict)
    finish_reason: str = "stop"

    @field_validator("usage")
    @classmethod
    def _validate_usage(cls, value: dict[str, Any]) -> dict[str, Any]:
        result = dict(value)
        result.setdefault("prompt_tokens", 0)
        result.setdefault("completion_tokens", 0)
        for key in ("prompt_tokens", "completion_tokens"):
            if not isinstance(result[key], int) or result[key] < 0:
                raise ValueError(f"usage.{key} must be int >= 0")
        return result


class ModelContract(ABC):
    """Interface for chat providers (non-streaming in v1).

    Breaking-change policy: adding streaming/tool-calling in M2 bumps the
    contract version; keep ``chat()`` signature stable.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider/model name."""

    @abstractmethod
    def is_available(self) -> bool:
        """Static availability check (no network call)."""

    @abstractmethod
    def metadata(self) -> AiOSMetadata:
        """Component metadata (id=models.<name>, version=aios_core version)."""

    def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        """Validate inputs (template method) then delegate to ``_chat``."""
        if not messages:
            raise ValueError("messages must not be empty")
        if not (0.0 <= temperature <= 2.0):
            raise ValueError("temperature must be in [0.0, 2.0]")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("max_tokens must be > 0 (or None)")
        return self._chat(messages, temperature, max_tokens)

    @abstractmethod
    def _chat(
        self,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int | None,
    ) -> ChatResponse:
        """Provider implementation (inputs already validated)."""
