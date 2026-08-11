"""Health check tests: registry, worst-wins, edge cases."""

import pytest

from aios_core.healthcheck import (
    HealthCheck,
    HealthRegistry,
    HealthReport,
    HealthStatus,
)


class FakeCheck(HealthCheck):
    def __init__(self, name: str, status: HealthStatus, message: str = ""):
        self._name = name
        self._status = status
        self._message = message

    @property
    def name(self) -> str:
        return self._name

    def check(self) -> HealthReport:
        return HealthReport(name=self._name, status=self._status, message=self._message)


class BrokenCheck(HealthCheck):
    @property
    def name(self) -> str:
        return "broken"

    def check(self) -> HealthReport:
        raise RuntimeError("boom")


def test_empty_registry_degraded():
    registry = HealthRegistry()
    report = registry.report()
    assert report.status == HealthStatus.DEGRADED
    assert "no checks registered" in report.message


def test_worst_wins_healthy_plus_degraded():
    registry = HealthRegistry()
    registry.register(FakeCheck("a", HealthStatus.HEALTHY))
    registry.register(FakeCheck("b", HealthStatus.DEGRADED))
    assert registry.report().status == HealthStatus.DEGRADED


def test_worst_wins_healthy_plus_unhealthy():
    registry = HealthRegistry()
    registry.register(FakeCheck("a", HealthStatus.HEALTHY))
    registry.register(FakeCheck("b", HealthStatus.UNHEALTHY))
    assert registry.report().status == HealthStatus.UNHEALTHY


def test_register_duplicate_raises():
    registry = HealthRegistry()
    registry.register(FakeCheck("a", HealthStatus.HEALTHY))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(FakeCheck("a", HealthStatus.HEALTHY))


def test_broken_check_degrades_not_crash():
    registry = HealthRegistry()
    registry.register(FakeCheck("ok", HealthStatus.HEALTHY))
    registry.register(BrokenCheck())
    report = registry.report()
    assert report.status == HealthStatus.DEGRADED
    assert "broken" in report.message


def test_get_all_returns_reports():
    registry = HealthRegistry()
    registry.register(FakeCheck("a", HealthStatus.HEALTHY))
    registry.register(FakeCheck("b", HealthStatus.UNHEALTHY))
    reports = registry.get_all()
    assert len(reports) == 2
    assert {r.name for r in reports} == {"a", "b"}


def test_timestamps_differ_between_reports():
    registry = HealthRegistry()
    registry.register(FakeCheck("a", HealthStatus.HEALTHY))
    registry.register(FakeCheck("b", HealthStatus.UNHEALTHY))
    reports = registry.get_all()
    assert reports[0].timestamp != reports[1].timestamp
    assert reports[0].timestamp.tzinfo is not None
