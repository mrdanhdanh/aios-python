"""Model health state machine (TASK-025 §YC-8): OK/DEGRADED/COOLDOWN/DISABLED.

In-memory, lock-protected, clock injectable. Failures accumulate across
cooldown cycles (cumulative — C2-03 v1): cooldown expiry lazily returns to OK
but does NOT reset failure counts.
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Callable

from .contracts import HealthConfig, HealthStatus


class ModelHealth:
    """Tracks dynamic per-model health for routing decisions."""

    def __init__(
        self,
        config: HealthConfig | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._config = config or HealthConfig()
        self._now = now
        self._failures: dict[str, int] = {}
        self._cooldown_until: dict[str, datetime] = {}
        self._lock = threading.RLock()

    def record_success(self, name: str) -> None:
        with self._lock:
            self._failures.pop(name, None)
            self._cooldown_until.pop(name, None)

    def record_failure(self, name: str, error: Exception) -> None:
        """Transition table (C2-03 v1): 1 -> DEGRADED, 2 -> COOLDOWN, >=3 -> DISABLED."""
        with self._lock:
            failures = self._failures.get(name, 0) + 1
            self._failures[name] = failures
            if failures >= self._config.max_failures_before_disable:
                self._cooldown_until.pop(name, None)
            else:
                self._cooldown_until[name] = self._now() + timedelta(
                    seconds=self._config.cooldown_seconds
                )

    def can_use(self, name: str, now: datetime | None = None) -> bool:
        with self._lock:
            return self.status(name, now=now) in (
                HealthStatus.OK,
                HealthStatus.DEGRADED,
            )

    def status(self, name: str, now: datetime | None = None) -> HealthStatus:
        with self._lock:
            current = now if now is not None else self._now()
            failures = self._failures.get(name, 0)
            if failures >= self._config.max_failures_before_disable:
                return HealthStatus.DISABLED
            if failures == 0:
                return HealthStatus.OK
            if failures == 1:
                return HealthStatus.DEGRADED
            # failures == 2: COOLDOWN with expiry (lazy -> OK, failures stay).
            cooldown_until = self._cooldown_until.get(name)
            if cooldown_until is not None:
                if current < cooldown_until:
                    return HealthStatus.COOLDOWN
                self._cooldown_until.pop(name, None)
            return HealthStatus.OK

    def snapshot(self) -> dict[str, HealthStatus]:
        with self._lock:
            return {name: self.status(name) for name in sorted(self._failures)}
