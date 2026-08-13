"""Execution Supervisor (TASK-022) — tracks running workflows from the bus.

In-memory (v1): no catch-up from the audit log (counters start at creation).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..kernel.events import Event, EventBus, EventType

_TERMINAL = {
    EventType.WORKFLOW_COMPLETED,
    EventType.WORKFLOW_FAILED,
    EventType.WORKFLOW_CANCELLED,
}


@dataclass(frozen=True)
class SupervisorSnapshot:
    running: tuple[dict[str, Any], ...]   # {execution_id, plan_id, started_at (ISO)}
    recent_completed: int
    recent_failed: int                    # FAILED + CANCELLED (R3-1)
    queue_size: int | None
    stuck: tuple[dict[str, Any], ...]     # subset of running (sorted)


class ExecutionSupervisor:
    def __init__(
        self,
        bus: EventBus,
        task_queue_count: Callable[[], int] | None = None,
        stuck_after_s: float = 60.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._queue_count = task_queue_count
        self._stuck_after_s = stuck_after_s
        self._clock = clock or time.monotonic
        self._active: dict[str, dict[str, Any]] = {}  # execution_id -> info
        self._completed = 0
        self._failed = 0
        self._subscription = bus.subscribe(None, self._on_event)

    def _on_event(self, event: Event) -> None:
        execution_id = str(event.payload.get("execution_id") or "")
        if not execution_id:
            return
        if event.type == EventType.WORKFLOW_STARTED:
            self._active[execution_id] = {
                "execution_id": execution_id,
                "plan_id": str(event.payload.get("plan_id") or ""),
                "started_ref": self._clock(),
                "started_at": event.timestamp.isoformat(),
            }
        elif event.type in _TERMINAL:
            self._active.pop(execution_id, None)
            if event.type == EventType.WORKFLOW_COMPLETED:
                self._completed += 1
            else:
                self._failed += 1  # FAILED + CANCELLED (R3-1)

    def snapshot(self) -> SupervisorSnapshot:
        running = sorted(
            (
                {
                    "execution_id": info["execution_id"],
                    "plan_id": info["plan_id"],
                    "started_at": info["started_at"],
                }
                for info in self._active.values()
            ),
            key=lambda r: r["execution_id"],
        )
        now = self._clock()
        stuck = tuple(
            r
            for r in running
            if self._active.get(r["execution_id"], {}).get("started_ref", now) + self._stuck_after_s < now
        )
        queue_size = self._queue_count() if self._queue_count else None
        return SupervisorSnapshot(
            running=tuple(running),
            recent_completed=self._completed,
            recent_failed=self._failed,
            queue_size=queue_size,
            stuck=stuck,
        )

    def close(self) -> None:
        self._subscription.unsubscribe()
