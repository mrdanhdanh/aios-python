"""Assistant base contract (Worker Plane — TASK-013).

Hard isolation (INV-001/002, TASK-016): this package may ONLY import
aios_core.models.base / aios_core.models.errors (contracts), pydantic and
stdlib. Every runtime interaction goes through injectable callables
(event_sink, health_probe, pipeline steps) — never kernel services.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("aios.agents")


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str  # user content (empty/whitespace -> handle returns status="error")
    context: dict[str, Any] = Field(default_factory=dict)  # knowledge/rule/session data from caller
    session_id: str | None = None


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str  # reply (or error message when status="error")
    intent: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: Literal["ok", "error"] = "ok"


# event_type: str (e.g. "agent.started"), payload: dict — best-effort
EventSink = Callable[[str, dict], None]

EVENT_AGENT_STARTED = "agent.started"  # == EventType.AGENT_STARTED.value (kernel)
EVENT_AGENT_FINISHED = "agent.finished"  # == EventType.AGENT_FINISHED.value (kernel)


class Assistant(ABC):
    """Template-method assistant: handle() owns lifecycle/events/errors."""

    def __init__(self, event_sink: EventSink | None = None) -> None:
        self._event_sink = event_sink

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def intent(self) -> str: ...

    def handle(self, request: AssistantRequest) -> AssistantResponse:
        """Lifecycle: validate -> started -> _process -> finished. Not overridable."""
        if not request.text or not request.text.strip():
            return AssistantResponse(
                text="empty request text", intent=self.intent, status="error"
            )
        self._emit(EVENT_AGENT_STARTED, {"agent": self.name, "intent": self.intent,
                                         "session_id": request.session_id})
        try:
            response = self._process(request)
        except Exception as exc:  # noqa: BLE001 — never propagate; BaseException propagates
            logger.exception("assistant %s failed", self.name)
            response = AssistantResponse(
                text=f"{self.name} failed: {exc}",
                intent=self.intent,
                status="error",
                metadata={"error": str(exc)},
            )
        self._emit(EVENT_AGENT_FINISHED, {"agent": self.name, "intent": self.intent,
                                          "status": response.status,
                                          "session_id": request.session_id})
        return response

    @abstractmethod
    def _process(self, request: AssistantRequest) -> AssistantResponse: ...

    def _emit(self, event_type: str, payload: dict) -> None:
        if self._event_sink is None:
            return
        try:
            self._event_sink(event_type, payload)
        except Exception as exc:  # noqa: BLE001 — best-effort (pattern EventService._audit)
            logger.warning("event_sink failed for %s: %s", event_type, exc)
