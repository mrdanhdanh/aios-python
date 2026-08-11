"""Permission service: scope-based allow/deny/ask with pending requests."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from ...logging import get_logger
from ..events import Event, EventBus, EventType

logger = get_logger("aios.kernel.services.permissions")


class PermissionScope(str, Enum):
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    DOCKER = "docker"
    SHELL = "shell"
    CLIPBOARD = "clipboard"
    GIT = "git"
    BROWSER = "browser"
    CAMERA = "camera"


class PermissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class PermissionRequest:
    scope: PermissionScope
    resource: str
    reason: str = ""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PermissionService:
    """Decide/ask permission for scopes.

    Defaults: filesystem=ALLOW, everything else=ASK.
    ``on_ask`` is a sync callback that must return quickly (M2 Permission
    Broker moves this to async). If it raises, we fall back to ASK.
    """

    def __init__(
        self,
        bus: EventBus,
        on_ask: Callable[[PermissionRequest], PermissionDecision] | None = None,
    ) -> None:
        self._bus = bus
        self._on_ask = on_ask
        self._policies: dict[PermissionScope, PermissionDecision] = {
            PermissionScope.FILESYSTEM: PermissionDecision.ALLOW,
        }
        self._pending: dict[str, PermissionRequest] = {}

    def set_policy(self, scope: PermissionScope, decision: PermissionDecision) -> None:
        if not isinstance(scope, PermissionScope):
            raise ValueError(f"invalid scope: {scope!r}")
        if not isinstance(decision, PermissionDecision):
            raise ValueError(f"invalid decision: {decision!r}")
        self._policies[scope] = decision

    def request(self, scope: PermissionScope, resource: str, reason: str = "") -> PermissionDecision:
        req = PermissionRequest(scope=scope, resource=resource, reason=reason)
        decision = self._policies.get(scope, PermissionDecision.ASK)

        if decision != PermissionDecision.ASK:
            self._emit_result(req, decision)
            return decision

        # ASK path: consult callback if provided.
        if self._on_ask is not None:
            try:
                decision = self._on_ask(req)
            except Exception as exc:  # noqa: BLE001
                logger.warning("on_ask callback failed, falling back to ASK: %s", exc)
                decision = PermissionDecision.ASK

        if decision == PermissionDecision.ASK:
            self._pending[req.request_id] = req
            self._bus.publish(
                Event(
                    type=EventType.PERMISSION_REQUESTED,
                    payload={
                        "service": "permission",
                        "request_id": req.request_id,
                        "scope": scope.value,
                        "resource": resource,
                    },
                    source="permission_service",
                )
            )
            return decision

        self._emit_result(req, decision)
        return decision

    def grant(self, request_id: str) -> bool:
        req = self._pending.pop(request_id, None)
        if req is None:
            logger.warning("grant: unknown request id %s (no-op)", request_id)
            return False
        self._emit_result(req, PermissionDecision.ALLOW)
        return True

    def deny(self, request_id: str) -> bool:
        req = self._pending.pop(request_id, None)
        if req is None:
            logger.warning("deny: unknown request id %s (no-op)", request_id)
            return False
        self._emit_result(req, PermissionDecision.DENY)
        return True

    def pending_count(self) -> int:
        return len(self._pending)

    def _emit_result(self, req: PermissionRequest, decision: PermissionDecision) -> None:
        event_type = (
            EventType.PERMISSION_GRANTED if decision == PermissionDecision.ALLOW else EventType.PERMISSION_DENIED
        )
        self._bus.publish(
            Event(
                type=event_type,
                payload={"request_id": req.request_id, "scope": req.scope.value, "resource": req.resource},
                source="permission_service",
            )
        )
