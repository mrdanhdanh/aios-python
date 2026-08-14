"""Harness context (TASK-029, H1): run-scoped context with event sink."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, PrivateAttr

from aios_core.logging import get_logger
from .contracts import HarnessEvent, utcnow

logger = get_logger("aios.harness.context")


class HarnessContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    harness: str
    target: str
    version: str | None = None
    environment: str = "local"
    config: dict[str, Any] = {}
    started_at: datetime

    _sink: Callable[[HarnessEvent], None] | None = PrivateAttr(default=None)

    def attach_sink(self, sink: Callable[[HarnessEvent], None]) -> None:
        self._sink = sink

    def emit_event(
        self,
        phase: str,
        message: str,
        level: Literal["info", "warning", "error"] = "info",
    ) -> HarnessEvent:
        event = HarnessEvent(
            run_id=self.run_id, phase=phase, timestamp=utcnow(),
            level=level, message=message)
        if self._sink is not None:
            try:  # C2-05: sink failure must never break the run
                self._sink(event)
            except Exception as exc:  # noqa: BLE001
                logger.warning("harness event sink failed: %s", exc)
        return event
