"""System doctor (TASK-021) — aggregates health checks + diagnostics.

Named HealthDoctor to avoid clashing with agents.SystemDoctor (TASK-013).
Diagnostics arrive as hooks from wiring — this module does NOT import
skills/catalog/prompts.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..healthcheck import HealthReport, HealthRegistry, HealthStatus, _STATUS_WEIGHT

Diagnostic = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class DoctorReport:
    status: HealthStatus
    checks: tuple[HealthReport, ...]
    diagnostics: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HealthDoctor:
    """Worst-wins aggregation of health checks plus diagnostics snapshots."""

    def __init__(
        self,
        health_registry: HealthRegistry,
        diagnostics: list[Diagnostic] | None = None,
        metrics_summary: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self._registry = health_registry
        self._diagnostics = diagnostics or []
        self._metrics_summary = metrics_summary

    def report(self) -> DoctorReport:
        checks = tuple(self._registry.get_all())
        worst = HealthStatus.HEALTHY
        for check in checks:
            if _STATUS_WEIGHT[check.status] > _STATUS_WEIGHT[worst]:
                worst = check.status
        diagnostics: dict[str, Any] = {}
        for hook in self._diagnostics:
            try:
                diagnostics.update(hook())
            except Exception as exc:  # noqa: BLE001 — diagnostic failure never crashes doctor
                diagnostics["error"] = str(exc)
        if self._metrics_summary is not None:
            diagnostics["metrics"] = self._metrics_summary()
        return DoctorReport(status=worst, checks=checks, diagnostics=diagnostics)
