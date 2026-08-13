"""Tool contract (TASK-014) — Execution Plane, hard isolation.

tools/ imports ONLY aios_core.metadata + pydantic + stdlib (allow-list rule).
All runtime interactions go through ToolContext injectable callables
(permission_gate, event_sink) — never kernel services (INV-001/004/005).
Template method `run` owns: tool_id check -> gate check (fail-closed) ->
started event -> _run -> finished event (even on error).
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..metadata import AiOSMetadata, make_component_metadata

logger = logging.getLogger("aios.tools")

EVENT_TOOL_STARTED = "tool.started"  # == EventType.TOOL_STARTED.value
EVENT_TOOL_FINISHED = "tool.finished"  # == EventType.TOOL_FINISHED.value


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_id: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None


class ToolOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    result: Any = None
    error: str = ""
    duration_s: float = 0.0  # measured with time.perf_counter; error paths -> 0.0 (C1-12/R1)
    usage: dict[str, Any] = Field(default_factory=dict)


class ToolContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    permission_gate: Callable[[list[str]], bool] | None = None  # None = DENY (fail-closed)
    event_sink: Callable[[str, dict], None] | None = None  # (event_type, payload)
    extra: dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """Base tool. Subclasses declare class attrs + implement `_run` stub."""

    tool_type: Literal["python", "docker", "rest", "mcp", "shell", "git"]
    required_scopes: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()

    def __init__(
        self,
        event_sink: Callable[[str, dict], None] | None = None,
        available: bool = True,
        metadata: AiOSMetadata | None = None,
        **tool_specific: Any,
    ) -> None:
        if not self.required_scopes:  # C1-06: no carve-out — side effect <-> gate
            raise ValueError(f"{type(self).__name__} must declare required_scopes")
        if not isinstance(available, bool):
            raise TypeError("available must be bool")
        self._event_sink = event_sink
        self._available = available
        self.id = f"tool.{self.tool_type}"
        self.name = self.tool_type
        self.description = self._describe()
        self.metadata = metadata or make_component_metadata(
            id=self.id, name=self.name, version="1.0.0", tags=["tool", self.tool_type]
        )
        self._configure(**tool_specific)

    # -- subclass hooks -------------------------------------------------------

    @abstractmethod
    def _describe(self) -> str: ...

    def _configure(self, **kwargs: Any) -> None:
        """Subclass hook for tool-specific constructor params (C2-10)."""

    @abstractmethod
    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput: ...

    # -- public API -----------------------------------------------------------

    def available(self) -> bool:
        return self._available

    def run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        # 1) tool_id check (C2-02 — before gate so mismatch isn't masked by deny).
        if input.tool_id != self.id:
            return ToolOutput(
                ok=False,
                error=f"tool_id mismatch: expected {self.id}, got {input.tool_id}",
            )
        # 2) Gate check — fail-closed; gate raise is also DENY (C1-02/R2).
        gate = context.permission_gate
        if gate is not None:
            try:
                allowed = gate(list(self.required_scopes))
            except Exception as exc:  # noqa: BLE001 — fail-closed
                logger.warning("permission_gate raised for %s: %s", self.id, exc)
                return ToolOutput(
                    ok=False,
                    error=f"permission denied: {', '.join(self.required_scopes)} (gate error)",
                )
        else:
            allowed = False
        if not allowed:
            if gate is None:
                return ToolOutput(
                    ok=False,
                    error=f"permission denied: {', '.join(self.required_scopes)} (no gate)",
                )
            return ToolOutput(ok=False, error=f"permission denied: {', '.join(self.required_scopes)}")

        # 3) started event.
        self._emit(
            EVENT_TOOL_STARTED,
            {
                "tool_id": self.id,
                "tool_type": self.tool_type,
                "capabilities": list(self.capabilities),
                "session_id": input.session_id,
            },
        )
        # 4) _run — measure only on success (R1: error paths -> duration_s=0.0).
        t0 = time.perf_counter()
        try:
            output = self._run(input, context)
            output.duration_s = time.perf_counter() - t0
        except Exception as exc:  # noqa: BLE001 — BaseException propagates
            logger.exception("tool %s failed", self.id)
            output = ToolOutput(ok=False, error=f"{self.id} failed: {exc}")
        # 5) finished event — even on error (R4: output created before emit).
        self._emit(
            EVENT_TOOL_FINISHED,
            {
                "tool_id": self.id,
                "tool_type": self.tool_type,
                "capabilities": list(self.capabilities),
                "session_id": input.session_id,
                "ok": output.ok,
                "duration_s": output.duration_s,
            },
        )
        # 6) return.
        return output

    def _stub_usage(self) -> dict:
        return {"mode": "stub", "tool_type": self.tool_type, "capabilities": list(self.capabilities)}

    def _emit(self, event_type: str, payload: dict) -> None:
        sink = self._event_sink  # C2-09: constructor sink is the per-run default
        if sink is None:
            return
        try:
            sink(event_type, payload)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("event_sink failed for %s: %s", event_type, exc)
