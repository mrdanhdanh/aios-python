"""Mock model: deterministic, offline — for tests and simulation mode."""

from __future__ import annotations

from .. import __version__
from ..metadata import AiOSMetadata
from .base import ChatMessage, ChatResponse, ModelContract
from .errors import ModelError


class MockModel(ModelContract):
    """Offline provider.

    - ``echo``: returns the last message content.
    - ``responses``: fixed (1 item) or sequential (N items); exhausted raises
      ``ModelError`` unless ``loop=True``.
    - ``raise_error``: raises the given exception on each call.
    - ``responses=None`` → always exhausted (raises).
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        echo: bool = False,
        raise_error: Exception | None = None,
        loop: bool = False,
    ) -> None:
        self.responses = responses
        self.echo = echo
        self.raise_error = raise_error
        self.loop = loop
        self.calls = 0
        self._index = 0

    @property
    def name(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        return True

    def metadata(self) -> AiOSMetadata:
        return AiOSMetadata(
            id="models.mock",
            name="mock",
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
        self.calls += 1
        if self.raise_error is not None:
            raise self.raise_error

        if self.echo:
            content = messages[-1].content
        else:
            if self.responses is None:
                raise ModelError("MockModel responses exhausted")
            if len(self.responses) == 1:
                # Fixed: always returns the single response.
                content = self.responses[0]
            else:
                if self._index >= len(self.responses):
                    if self.loop:
                        self._index = 0
                    else:
                        raise ModelError("MockModel responses exhausted")
                content = self.responses[self._index]
                self._index += 1

        tokens = max(1, len(content) // 4)
        return ChatResponse(
            content=content,
            model="mock",
            usage={"prompt_tokens": tokens, "completion_tokens": tokens},
        )
