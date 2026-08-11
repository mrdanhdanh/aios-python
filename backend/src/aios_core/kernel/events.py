"""In-process publish/subscribe event bus."""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..logging import get_logger

logger = get_logger("aios.kernel.events")


class EventType(str, Enum):
    AGENT_STARTED = "agent.started"
    AGENT_FINISHED = "agent.finished"
    TOOL_STARTED = "tool.started"
    TOOL_FINISHED = "tool.finished"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_CANCELLED = "workflow.cancelled"
    SKILL_INSTALLED = "skill.installed"
    SKILL_UPDATED = "skill.updated"
    SKILL_REMOVED = "skill.removed"
    UPGRADE_COMPLETED = "upgrade.completed"
    PERMISSION_REQUESTED = "permission.requested"
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_DENIED = "permission.denied"
    ARTIFACT_CREATED = "artifact.created"
    MODEL_CALL_STARTED = "model.call.started"
    MODEL_CALL_FINISHED = "model.call.finished"
    ERROR_OCCURRED = "error.occurred"


@dataclass
class Event:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "source": self.source,
        }


Handler = Callable[[Event], Any] | Callable[[Event], Awaitable[Any]]


class Subscription:
    def __init__(self, bus: "EventBus", event_type: EventType | None, handler: Handler) -> None:
        self._bus = bus
        self.event_type = event_type
        self.handler = handler
        self._cancelled = False

    def unsubscribe(self) -> None:
        if not self._cancelled:
            self._bus._unsubscribe(self)  # noqa: SLF001
            self._cancelled = True


class EventBus:
    """Thread-safe pub/sub bus.

    Async handlers:
    - inside a running loop: scheduled as a task, tracked in ``_pending``,
      exceptions logged by the done callback (never re-raised by ``flush``);
    - outside a loop (sync thread): run via ``asyncio.run`` in a daemon thread
      (stateless handlers only; Event Service marshals into the main loop).
    """

    def __init__(self) -> None:
        self._subscribers: list[Subscription] = []
        self._lock = threading.RLock()
        self._pending: set[asyncio.Task] = set()

    def subscribe(self, event_type: EventType | None, handler: Handler) -> Subscription:
        sub = Subscription(self, event_type, handler)
        with self._lock:
            self._subscribers.append(sub)
        return sub

    def _unsubscribe(self, sub: Subscription) -> None:
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)

    def publish(self, event: Event) -> None:
        # Snapshot under lock, iterate outside the lock.
        with self._lock:
            handlers = [
                s.handler
                for s in self._subscribers
                if s.event_type is None or s.event_type == event.type
            ]
        for handler in handlers:
            try:
                result = handler(event)
            except Exception as exc:  # noqa: BLE001 — a broken handler must not crash the bus
                logger.warning("Sync handler failed for %s: %s", event.type, exc)
                continue
            if isinstance(result, Awaitable):
                self._schedule_async(event, result)

    def _schedule_async(self, event: Event, coro: Awaitable[Any]) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop → run in a daemon thread with its own loop.
            def _run() -> None:
                try:
                    asyncio.run(coro)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Async handler failed for %s: %s", event.type, exc)

            threading.Thread(target=_run, daemon=True).start()
            return

        # Inside a running loop → schedule a tracked task.
        task = asyncio.create_task(coro)

        def _done(t: asyncio.Task) -> None:
            if t.cancelled():
                self._pending.discard(t)
                return
            exc = t.exception()
            if exc is not None:
                logger.warning("Async handler failed for %s: %s", event.type, exc)
            self._pending.discard(t)

        task.add_done_callback(_done)
        with self._lock:
            self._pending.add(task)

    async def flush(self) -> None:
        """Wait for all tracked async handlers; never re-raises their errors."""
        with self._lock:
            pending = list(self._pending)
        if not pending:
            return
        await asyncio.gather(*pending, return_exceptions=True)
