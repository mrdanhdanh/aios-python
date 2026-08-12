"""OpenAI-compatible provider (lazy import; client injectable for tests)."""

from __future__ import annotations

import importlib.util
import os
from typing import Any

from .. import __version__
from ..metadata import AiOSMetadata
from .base import ChatMessage, ChatResponse, ModelContract
from .errors import ModelNotAvailableError


def _is_openai_installed() -> bool:
    return importlib.util.find_spec("openai") is not None


class OpenAIModel(ModelContract):
    """Chat provider via the official ``openai`` SDK.

    ``client`` is an injection seam: tests pass a fake; when ``None`` the
    client is built lazily after availability is confirmed.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._model = model
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
        self._base_url = base_url if base_url is not None else os.environ.get("OPENAI_BASE_URL")
        self._client = client
        self._timeout = timeout

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def is_available(self) -> bool:
        return _is_openai_installed() and (self._api_key is not None or self._base_url is not None)

    def metadata(self) -> AiOSMetadata:
        return AiOSMetadata(
            id="models.openai",
            name=self._model,
            version=__version__,
            author="AIOS",
            license="MIT",
        )

    def _chat(
        self,
        messages: list[ChatMessage],
        temperature: float,
        max_tokens: int | None,
    ) -> ChatResponse:
        if self._client is None:
            if not self.is_available():
                raise ModelNotAvailableError("openai not installed or missing api_key/base_url")
            self._client = self._build_client()

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        completion = self._client.chat.completions.create(**kwargs)

        choice = completion.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=completion.model or self._model,
            usage={
                "prompt_tokens": getattr(completion.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(completion.usage, "completion_tokens", 0) or 0,
            },
            finish_reason=getattr(choice, "finish_reason", "stop") or "stop",
        )

    def _build_client(self) -> Any:
        from openai import OpenAI

        kwargs: dict[str, Any] = {"timeout": self._timeout}
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAI(**kwargs)
