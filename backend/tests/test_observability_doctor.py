"""HealthDoctor tests (TASK-021)."""

from aios_core.healthcheck import HealthCheck, HealthRegistry, HealthReport, HealthStatus
from aios_core.observability.doctor import HealthDoctor


class FakeCheck(HealthCheck):
    def __init__(self, name: str, status: HealthStatus) -> None:
        self._name = name
        self._status = status

    @property
    def name(self) -> str:
        return self._name

    def check(self) -> HealthReport:
        return HealthReport(name=self._name, status=self._status)


def test_worst_wins_aggregation():
    reg = HealthRegistry()
    reg.register(FakeCheck("healthy", HealthStatus.HEALTHY))
    reg.register(FakeCheck("bad", HealthStatus.UNHEALTHY))
    doctor = HealthDoctor(reg, diagnostics=[])
    report = doctor.report()
    assert report.status == HealthStatus.UNHEALTHY


def test_degraded_beats_healthy():
    reg = HealthRegistry()
    reg.register(FakeCheck("ok", HealthStatus.HEALTHY))
    reg.register(FakeCheck("meh", HealthStatus.DEGRADED))
    assert HealthDoctor(reg).report().status == HealthStatus.DEGRADED


def test_diagnostics_hooks_merged():
    reg = HealthRegistry()
    doctor = HealthDoctor(
        reg,
        diagnostics=[lambda: {"skills": 3}, lambda: {"catalog": 5}],
        metrics_summary=lambda: {"total": 7},
    )
    report = doctor.report()
    assert report.diagnostics["skills"] == 3
    assert report.diagnostics["catalog"] == 5
    assert report.diagnostics["metrics"] == {"total": 7}


def test_diagnostic_failure_never_crashes():
    reg = HealthRegistry()

    def broken():
        raise RuntimeError("boom")

    doctor = HealthDoctor(reg, diagnostics=[broken])
    report = doctor.report()
    assert report.status == HealthStatus.HEALTHY
    assert "error" in report.diagnostics


def test_empty_registry_healthy():
    reg = HealthRegistry()
    report = HealthDoctor(reg).report()
    assert report.status == HealthStatus.HEALTHY
    assert report.checks == ()
