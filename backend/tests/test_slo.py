"""TASK-069 — Reliability SLO: 7 ratio + 5 non-averaged gates (M10-F2)."""

from __future__ import annotations

import pytest

from aios_core.observability.slo import (
    SLO_DEFINITIONS,
    SloDefinition,
    SloEngine,
    SloKind,
    SloStatus,
    format_slo_report,
)


# ---------------------------------------------------------------------------
# AC1: 12 SLO — 7 ratio + 5 absolute-zero
# ---------------------------------------------------------------------------

def test_registry_has_12_slo():
    assert len(SLO_DEFINITIONS) == 12
    ratios = [s for s in SLO_DEFINITIONS if s.kind == SloKind.RATIO]
    zeros = [s for s in SLO_DEFINITIONS if s.kind == SloKind.ABSOLUTE_ZERO]
    assert len(ratios) == 7
    assert len(zeros) == 5
    assert {z.id for z in zeros} == {
        "policy_bypass", "lost_execution", "checkpoint_corruption",
        "unauthorized_tool", "contract_breaking",
    }


# ---------------------------------------------------------------------------
# AC2: RATIO biên
# ---------------------------------------------------------------------------

def test_ratio_pass_fail_boundary():
    engine = SloEngine()
    r = engine.check({"execution_success": 0.95})  # target 0.95
    res = {x.slo_id: x for x in r.results}["execution_success"]
    assert res.status == SloStatus.PASS
    r2 = engine.check({"execution_success": 0.949})
    assert {x.slo_id: x for x in r2.results}["execution_success"].status == SloStatus.FAIL


def test_ratio_out_of_range_fail():
    engine = SloEngine()
    r = engine.check({"execution_success": 1.5})
    assert {x.slo_id: x for x in r.results}["execution_success"].status == SloStatus.FAIL


# ---------------------------------------------------------------------------
# AC3: ABSOLUTE_ZERO — 1 lần cũng fail (không trung bình hóa)
# ---------------------------------------------------------------------------

def test_absolute_zero_single_violation_fails():
    engine = SloEngine()
    metrics = {s.id: 0.0 for s in SLO_DEFINITIONS}
    metrics["policy_bypass"] = 1.0  # chỉ 1 lần — vẫn FAIL
    r = engine.check(metrics)
    res = {x.slo_id: x for x in r.results}["policy_bypass"]
    assert res.status == SloStatus.FAIL
    assert "không trung bình hóa" in res.note


def test_absolute_zero_zero_passes():
    engine = SloEngine()
    metrics = {s.id: 0.0 for s in SLO_DEFINITIONS}
    r = engine.check(metrics)
    for x in r.results:
        if x.kind == "absolute_zero":
            assert x.status == SloStatus.PASS, x.slo_id


# ---------------------------------------------------------------------------
# AC4: release_ready — 1 gate fail chặn dù SLO khác đạt
# ---------------------------------------------------------------------------

def test_release_ready_false_on_single_fail():
    engine = SloEngine()
    metrics = {s.id: 1.0 for s in SLO_DEFINITIONS if s.kind == SloKind.RATIO}
    metrics.update({s.id: 0.0 for s in SLO_DEFINITIONS if s.kind == SloKind.ABSOLUTE_ZERO})
    assert engine.check(metrics).release_ready is True
    metrics["unauthorized_tool"] = 1.0
    report = engine.check(metrics)
    assert report.release_ready is False
    assert len(report.failures) == 1


def test_skipped_does_not_block():
    """SKIPPED (thiếu dữ liệu) không chặn release."""
    engine = SloEngine()
    report = engine.check({})  # không metrics nào
    assert all(x.status == SloStatus.SKIPPED for x in report.results)
    assert report.release_ready is True


# ---------------------------------------------------------------------------
# AC5: metrics_from_runtime không crash khi DB rỗng
# ---------------------------------------------------------------------------

def test_metrics_from_runtime_empty_db():
    from aios_core.kernel import RuntimeKernel

    kernel = RuntimeKernel.create()
    engine = SloEngine()
    metrics = engine.metrics_from_runtime(kernel)
    assert isinstance(metrics, dict)
    assert metrics["contract_breaking"] == 0.0
    report = engine.check(metrics)
    # DB rỗng → không crash; ratio thiếu dữ liệu → SKIPPED
    assert report.release_ready  # SKIPPED không chặn


def test_metrics_from_runtime_with_workflow(tmp_path):
    from aios_core.kernel import RuntimeKernel
    from aios_core.kernel.events import Event, EventBus, EventType
    from aios_core.observability.metrics import MetricsService

    kernel = RuntimeKernel.create()
    bus = kernel.bus
    metrics_svc = MetricsService(bus, tmp_path / "m.db")
    # start ×3 → finish: 2 completed + 1 failed (cùng execution_id — M1 pattern)
    for i in range(3):
        metrics_svc._on_event(Event(
            type=EventType.WORKFLOW_STARTED,
            payload={"execution_id": f"e{i}", "plan_id": "p"},
            source="t",
        ))
    for i in range(2):
        metrics_svc._on_event(Event(
            type=EventType.WORKFLOW_COMPLETED,
            payload={"execution_id": f"e{i}", "plan_id": "p"},
            source="t",
        ))
    metrics_svc._on_event(Event(
        type=EventType.WORKFLOW_FAILED,
        payload={"execution_id": "e2", "plan_id": "p", "reason": "x"},
        source="t",
    ))

    class _Kernel:
        container = type("C", (), {"resolve": lambda self, t: metrics_svc})()

    engine = SloEngine()
    metrics = engine.metrics_from_runtime(_Kernel())
    assert metrics["execution_success"] == pytest.approx(2 / 3)
    assert metrics["runtime_availability"] == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# AC6: CLI + AC7 validation
# ---------------------------------------------------------------------------

def test_cli_slo(tmp_path, capsys):
    from aios_core.workflow.cli import main

    assert main(["slo"]) == 0
    out = capsys.readouterr().out
    assert "execution_success" in out
    assert "RELEASE READY" in out or "NOT READY" in out


def test_slo_definition_extra_forbid_and_target():
    with pytest.raises(Exception):
        SloDefinition(id="x", name="x", kind=SloKind.RATIO, target=0.5, bogus=1)
    with pytest.raises(Exception):
        SloDefinition(id="x", name="x", kind=SloKind.RATIO, target=1.5)


def test_format_report_stable():
    engine = SloEngine()
    report = engine.check({"execution_success": 1.0})
    text = format_slo_report(report)
    assert "RELEASE READY" in text
    assert "✓" in text
