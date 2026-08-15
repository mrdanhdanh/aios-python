"""TASK-038 — Distributed Scheduler + Execution Lease (E4).

Extends the M5 Graph Scheduler with a distributed layer (PLAN §6 E4):
queue → assign to node → lease → heartbeat → stale detection → failover →
resume snapshot. Enforces INV-026 (Distributed Execution Safety): an execution
has at most ONE active lease at any time. A second lease for the same execution
is rejected.

``LeaseManager`` is the source of truth for active leases; ``DistributedScheduler``
orchestrates assignment and failover using only public interfaces (INV-016 style
— no ownership of the underlying execution implementation).
"""

from __future__ import annotations

import threading
import time
from typing import Callable

from .contracts import Lease, RuntimeNodeInfo


class LeaseError(Exception):
    """Raised on lease violations (INV-026)."""


class LeaseManager:
    """Single-active-lease-per-execution manager (INV-026)."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._lock = threading.RLock()
        # execution_id -> Lease
        self._leases: dict[str, Lease] = {}

    def acquire(self, execution_id: str, node_id: str, ttl_s: float = 60.0) -> Lease:
        now = self._clock()
        with self._lock:
            existing = self._leases.get(execution_id)
            if existing is not None and existing.expires_at > now:
                raise LeaseError(
                    f"INV-026: execution {execution_id!r} already has active lease "
                    f"on {existing.node_id!r}"
                )
            lease = Lease(
                execution_id=execution_id,
                node_id=node_id,
                acquired_at=now,
                expires_at=now + ttl_s,
                heartbeat_at=now,
            )
            self._leases[execution_id] = lease
            return lease

    def renew(self, execution_id: str, node_id: str, ttl_s: float = 60.0) -> Lease:
        now = self._clock()
        with self._lock:
            lease = self._leases.get(execution_id)
            if lease is None:
                raise LeaseError(f"no lease for execution {execution_id!r}")
            if lease.node_id != node_id:
                raise LeaseError(
                    f"INV-026: node {node_id!r} cannot renew lease held by "
                    f"{lease.node_id!r}"
                )
            lease.heartbeat_at = now
            lease.expires_at = now + ttl_s
            return lease

    def release(self, execution_id: str) -> None:
        with self._lock:
            self._leases.pop(execution_id, None)

    def is_expired(self, execution_id: str, now: float | None = None) -> bool:
        now = now if now is not None else self._clock()
        lease = self._leases.get(execution_id)
        return lease is None or lease.expires_at <= now

    def active_node(self, execution_id: str) -> str | None:
        lease = self._leases.get(execution_id)
        if lease is None or lease.expires_at <= self._clock():
            return None
        return lease.node_id

    def list(self) -> list[Lease]:
        with self._lock:
            return list(self._leases.values())


class DistributedScheduler:
    """Assigns queued executions to healthy nodes with lease + failover.

    The scheduler does NOT execute work itself; it calls ``run_on_node``
    (injectable) and ``resume_snapshot`` (injectable) so the actual runtime
    remains behind a public interface (no god object).
    """

    def __init__(
        self,
        lease_manager: LeaseManager,
        node_selector: Callable[[str], RuntimeNodeInfo],
        run_on_node: Callable[[str, str], None] | None = None,
        resume_snapshot: Callable[[str, str], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.leases = lease_manager
        self._select = node_selector
        self._run = run_on_node or (lambda eid, nid: None)
        self._resume = resume_snapshot or (lambda eid, nid: None)
        self._clock = clock or time.monotonic
        self._queue: list[str] = []
        self._lock = threading.RLock()

    def enqueue(self, execution_id: str) -> None:
        with self._lock:
            if execution_id not in self._queue:
                self._queue.append(execution_id)

    def schedule(self, ttl_s: float = 60.0) -> list[str]:
        """Assign queued executions to nodes; return those scheduled."""
        scheduled: list[str] = []
        with self._lock:
            pending = list(self._queue)
        for execution_id in pending:
            node = self._select(execution_id)
            try:
                self.leases.acquire(execution_id, node.id, ttl_s=ttl_s)
            except LeaseError:
                continue  # INV-026: already leased elsewhere
            self._run(execution_id, node.id)
            with self._lock:
                if execution_id in self._queue:
                    self._queue.remove(execution_id)
            scheduled.append(execution_id)
        return scheduled

    def failover(self, execution_id: str, ttl_s: float = 60.0) -> str | None:
        """On lease expiry, reschedule to another node + resume snapshot.

        Returns the new node id, or None if no node available.
        """
        if not self.leases.is_expired(execution_id):
            return self.leases.active_node(execution_id)
        node = self._select(execution_id)
        lease = self.leases.acquire(execution_id, node.id, ttl_s=ttl_s)  # INV-026
        self._resume(execution_id, node.id)
        return lease.node_id
