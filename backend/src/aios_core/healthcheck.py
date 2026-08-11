"""Health check primitives: status, report, check interface, registry.

Worst-wins aggregation: unhealthy > degraded > healthy.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


#: Order used for worst-wins aggregation (higher = worse).
_STATUS_WEIGHT = {
    HealthStatus.HEALTHY: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.UNHEALTHY: 2,
}


@dataclass
class HealthReport:
    name: str
    status: HealthStatus
    message: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )  # NOT `now` directly — that would be evaluated at import time.


class HealthCheck(ABC):
    """Base class for health checks (e.g. model, docker, disk)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of this check."""

    @abstractmethod
    def check(self) -> HealthReport:
        """Run the check and return a report."""


class HealthRegistry:
    """Register health checks and produce aggregated reports."""

    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register(self, check: HealthCheck) -> None:
        if check.name in self._checks:
            raise ValueError(f"Health check already registered: {check.name}")
        self._checks[check.name] = check

    def get_all(self) -> list[HealthReport]:
        reports: list[HealthReport] = []
        for name, check in self._checks.items():
            try:
                reports.append(check.check())
            except Exception as exc:  # noqa: BLE001 — a broken check must not crash the report
                logger.exception("Health check %s failed", name)
                reports.append(
                    HealthReport(name=name, status=HealthStatus.DEGRADED, message=f"check raised: {exc}")
                )
        return reports

    def report(self) -> HealthReport:
        """Aggregate all checks, worst-wins. Empty registry → degraded."""
        reports = self.get_all()
        if not reports:
            return HealthReport(
                name="aios",
                status=HealthStatus.DEGRADED,
                message="no checks registered",
            )
        worst = max(reports, key=lambda r: _STATUS_WEIGHT[r.status])
        return HealthReport(
            name="aios",
            status=worst.status,
            message="; ".join(f"{r.name}={r.status.value}" for r in reports),
        )
