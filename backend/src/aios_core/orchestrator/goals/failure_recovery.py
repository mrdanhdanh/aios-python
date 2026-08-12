"""Failure Recovery: agent failed -> retry -> fallback agent -> fallback
workflow -> report (PLAN.md). Deterministic, offline-first; sleeps are injected
so tests never wait (lesson: fake clock trap).

Retry applies ONLY to the original attempt; each fallback runs exactly once
(C1-10). Every executor failure emits ERROR_OCCURRED (C2-07).
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field

from ...kernel.events import EventType
from ...kernel.services.events import EventService


class RecoveryStatus(str, Enum):
    RECOVERED = "recovered"
    FAILED = "failed"


class RecoveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RecoveryStatus
    attempts: int = 0
    error: str = ""
    fallback_used: Literal["", "agent", "workflow"] = ""
    final_result: Any = None
    history: list[str] = Field(default_factory=list)


class FailureRecovery:
    """Retry/fallback orchestration for a failing agent+workflow pair."""

    def __init__(
        self,
        event_service: EventService,
        max_retries: int = 2,
        backoff_base_s: float = 0.1,
        backoff_max_s: float = 2.0,
        fallback_agents: dict[str, str] | None = None,
        fallback_workflows: dict[str, str] | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if backoff_base_s < 0:
            raise ValueError("backoff_base_s must be >= 0")
        if backoff_max_s < 0:
            raise ValueError("backoff_max_s must be >= 0")
        self._events = event_service
        self._max_retries = max_retries
        self._backoff_base = backoff_base_s
        self._backoff_max = backoff_max_s
        self._fallback_agents = fallback_agents or {}
        self._fallback_workflows = fallback_workflows or {}
        self._sleeper = sleeper

    def run(
        self,
        agent: str,
        workflow_name: str,
        executor: Callable[[str, str], Any],
    ) -> RecoveryResult:
        """Run the recovery chain. ``executor(agent, workflow) -> Any``; an
        exception (or a raised ``RuntimeError``) counts as failure."""
        history: list[str] = []
        attempts = 0
        error = ""

        def _try(target_agent: str, target_wf: str) -> Any:
            nonlocal attempts, error
            attempts += 1
            try:
                return executor(target_agent, target_wf)
            except Exception as exc:  # noqa: BLE001 — BaseException (KeyboardInterrupt) propagates
                error = str(exc)
                self._events.emit(
                    EventType.ERROR_OCCURRED,
                    {"agent": target_agent, "workflow_name": target_wf, "error": error},
                    source="failure_recovery",
                )
                return None

        # 1) Original attempt.
        history.append(f"agent:{agent}")
        result = _try(agent, workflow_name)
        if result is not None:
            return RecoveryResult(status=RecoveryStatus.RECOVERED, attempts=attempts,
                                  final_result=result, history=history)

        # 2) Retries with exponential backoff (sleep injected).
        for attempt_idx in range(self._max_retries):
            backoff = min(self._backoff_base * (2 ** attempt_idx), self._backoff_max)
            history.append(f"retry:{attempt_idx + 1}")
            self._sleeper(backoff)
            self._events.emit(
                EventType.RECOVERY_RETRY,
                {"agent": agent, "workflow_name": workflow_name,
                 "attempt": attempt_idx + 1, "backoff_s": backoff},
                source="failure_recovery",
            )
            result = _try(agent, workflow_name)
            if result is not None:
                return RecoveryResult(status=RecoveryStatus.RECOVERED, attempts=attempts,
                                      final_result=result, history=history)

        # 3) Fallback agent (exactly once — C1-10).
        fb_agent = self._fallback_agents.get(agent)
        if fb_agent:
            history.append(f"fallback_agent:{fb_agent}")
            self._events.emit(
                EventType.RECOVERY_FALLBACK,
                {"kind": "agent", "from": agent, "to": fb_agent, "workflow_name": workflow_name},
                source="failure_recovery",
            )
            result = _try(fb_agent, workflow_name)
            if result is not None:
                return RecoveryResult(status=RecoveryStatus.RECOVERED, attempts=attempts,
                                      fallback_used="agent", final_result=result, history=history)

        # 4) Fallback workflow (exactly once). Uses fallback agent if any.
        fb_wf = self._fallback_workflows.get(workflow_name)
        if fb_wf:
            history.append(f"fallback_workflow:{fb_wf}")
            self._events.emit(
                EventType.RECOVERY_FALLBACK,
                {"kind": "workflow", "from": workflow_name, "to": fb_wf, "agent": fb_agent or agent},
                source="failure_recovery",
            )
            result = _try(fb_agent or agent, fb_wf)
            if result is not None:
                return RecoveryResult(status=RecoveryStatus.RECOVERED, attempts=attempts,
                                      fallback_used="workflow", final_result=result, history=history)

        # 5) Report failure.
        return RecoveryResult(
            status=RecoveryStatus.FAILED,
            attempts=attempts,
            error=error,
            fallback_used="",
            history=history,
        )
