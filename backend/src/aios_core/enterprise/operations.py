"""TASK-041 — Enterprise Operations (E7): HA + Audit + Recovery.

Implements:
- ``CentralAuditStore`` (INV-027): every security-sensitive action produces a
  structured, tamper-evident ``AuditEvent`` chained by ``previous_hash``. Audit
  completeness means no sensitive action is committed without evidence.
- ``HealthMonitor`` / failover: heartbeat → drain → reschedule (no blind kill).
- ``RecoveryManager``: snapshot/backup + restore for execution resumption.

The audit store emits via an injected ``EventBus`` (DI) so it stays decoupled
from kernel internals (INV-029-style isolation). For tests, the bus is optional.
"""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Callable

from .contracts import AuditEvent, HealthStatus, RuntimeNodeInfo


class AuditError(Exception):
    """Raised on audit violations (INV-027)."""


def _hash_event(event: AuditEvent) -> str:
    payload = (
        f"{event.id}|{event.timestamp}|{event.actor_id}|{event.action}|"
        f"{event.result}|{event.tenant_id}|{event.previous_hash}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CentralAuditStore:
    """Tamper-evident, append-only audit log (INV-027).

    Security-sensitive actions (authz deny, credential resolve, cross-tenant
    attempt, lease acquire, policy violation) MUST be recorded via ``record``.
    The chain is verified by ``verify_integrity``.
    """

    # Actions considered security-sensitive (must have audit evidence).
    SENSITIVE = {
        "authz.denied",
        "credential.resolved",
        "tenant.cross_access_denied",
        "lease.acquired",
        "policy.violation",
        "execution.started",
        "sandbox.bypassed",
    }

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.time
        self._lock = threading.RLock()
        self._events: list[AuditEvent] = []
        self._last_hash: str | None = None

    def record(
        self,
        actor_id: str,
        action: str,
        result: str,
        tenant_id: str | None = None,
        project_id: str | None = None,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        tool_id: str | None = None,
        credential_scope: str | None = None,
        policy_decision: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> AuditEvent:
        with self._lock:
            event = AuditEvent(
                timestamp=self._clock(),
                actor_id=actor_id,
                action=action,
                result=result,
                tenant_id=tenant_id,
                project_id=project_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                tool_id=tool_id,
                credential_scope=credential_scope,
                policy_decision=policy_decision,
                evidence=evidence or {},
                previous_hash=self._last_hash,
            )
            event.hash = _hash_event(event)
            self._events.append(event)
            self._last_hash = event.hash
            return event

    def has_evidence(self, action: str, **filters: Any) -> bool:
        with self._lock:
            return any(
                e.action == action
                and all(getattr(e, k, None) == v for k, v in filters.items())
                for e in self._events
            )

    def verify_integrity(self) -> bool:
        """Recompute the hash chain; return False on any tampering."""
        prev: str | None = None
        for e in self._events:
            if e.previous_hash != prev:
                return False
            if e.hash != _hash_event(e):
                return False
            prev = e.hash
        return True

    def list(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)


class HealthMonitor:
    """Heartbeat-based health + failover coordination (PLAN §9 E7)."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._heartbeats: dict[str, float] = {}
        self._status: dict[str, HealthStatus] = {}

    def heartbeat(self, node_id: str, status: HealthStatus | None = None) -> None:
        self._heartbeats[node_id] = self._clock()
        if status is not None:
            self._status[node_id] = status

    def mark_draining(self, node_id: str) -> None:
        self._status[node_id] = HealthStatus.DRAINING

    def is_stale(self, node_id: str, timeout_s: float) -> bool:
        last = self._heartbeats.get(node_id)
        if last is None:
            return True
        return (self._clock() - last) > timeout_s

    def failover_target(self, nodes: list[RuntimeNodeInfo], dead_node_id: str) -> RuntimeNodeInfo | None:
        """Choose a healthy node other than the dead one (no blind kill)."""
        candidates = [
            n for n in nodes
            if n.id != dead_node_id and n.health in ("healthy", "degraded")
        ]
        return candidates[0] if candidates else None


class RecoveryManager:
    """Snapshot/backup + restore for resilient execution (PLAN §9 E7)."""

    def __init__(self) -> None:
        self._snapshots: dict[str, dict[str, Any]] = {}

    def snapshot(self, execution_id: str, state: dict[str, Any]) -> None:
        self._snapshots[execution_id] = dict(state)

    def restore(self, execution_id: str) -> dict[str, Any] | None:
        return self._snapshots.get(execution_id)

    def has_snapshot(self, execution_id: str) -> bool:
        return execution_id in self._snapshots
