"""General chat assistant — deterministic template, model optional (TASK-013)."""

from __future__ import annotations

from collections.abc import Callable

from ..models.base import ChatMessage, ModelContract
from ..models.errors import ModelError
from .base import Assistant, AssistantRequest, AssistantResponse, EventSink


class GeneralAssistant(Assistant):
    name = "general"
    intent = "chat"
    description = "General chat assistant (deterministic template, model optional)"

    def __init__(self, model: ModelContract | None = None, event_sink: EventSink | None = None) -> None:
        super().__init__(event_sink=event_sink)
        self._model = model

    def _process(self, request: AssistantRequest) -> AssistantResponse:
        if self._model is not None:
            try:
                response = self._model.chat(
                    [ChatMessage(role="user", content=request.text)], temperature=0.7
                )
                return AssistantResponse(
                    text=response.content,
                    intent=self.intent,
                    metadata={"model": self._model.name, "model_called": True},
                )
            except ModelError as exc:
                return self._template(request, model_error=str(exc))
            except Exception as exc:  # noqa: BLE001 — offline-first fallback (C1-08)
                return self._template(request, model_error=str(exc))
        return self._template(request)

    def _template(self, request: AssistantRequest, model_error: str | None = None) -> AssistantResponse:
        text = f"Bạn nói: {request.text}"
        knowledge = request.context.get("knowledge")
        if isinstance(knowledge, list):
            for item in knowledge[:5]:
                text += f"\n- {item}"
        metadata: dict = {"model_called": False}
        if model_error is not None:
            metadata["model_error"] = model_error
        return AssistantResponse(text=text, intent=self.intent, metadata=metadata)
