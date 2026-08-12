"""Ollama provider: local LLM via HTTP (stdlib urllib only)."""

from __future__ import annotations

import json
import socket
import urllib.error
from urllib.request import Request, urlopen

from .. import __version__
from ..metadata import AiOSMetadata
from .base import ChatMessage, ChatResponse, ModelContract
from .errors import ModelError, ModelNotAvailableError, ModelTimeoutError


class OllamaModel(ModelContract):
    """Chat provider for a local Ollama server.

    ``urlopen`` is a module-level reference so tests can patch
    ``aios_core.models.ollama_provider.urlopen``.
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
        timeout: float = 30.0,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def name(self) -> str:
        return f"ollama:{self._model}"

    def is_available(self) -> bool:
        try:
            with urlopen(f"{self._base_url}/api/tags", timeout=self._timeout) as resp:
                return resp.status == 200
        except Exception:  # noqa: BLE001 — any failure means unavailable
            return False

    def metadata(self) -> AiOSMetadata:
        return AiOSMetadata(
            id="models.ollama",
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
        payload = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        req = Request(
            f"{self._base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise ModelError(f"ollama HTTP error {exc.code}: {exc.reason}") from exc
        except socket.timeout as exc:
            raise ModelTimeoutError("ollama request timed out") from exc
        except urllib.error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, socket.timeout):
                raise ModelTimeoutError("ollama request timed out") from exc
            if isinstance(reason, (ConnectionRefusedError, socket.gaierror)):
                raise ModelNotAvailableError(f"ollama not reachable: {reason}") from exc
            raise ModelError(f"ollama request failed: {reason}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ModelError("ollama returned invalid JSON") from exc
        if "message" not in data:
            raise ModelError("ollama response missing 'message'")

        return ChatResponse(
            content=data["message"].get("content", ""),
            model=data.get("model", self._model),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0) or 0,
                "completion_tokens": data.get("eval_count", 0) or 0,
            },
            finish_reason=data.get("done_reason", "stop") or "stop",
        )
