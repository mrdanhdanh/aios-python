"""TASK-070 — Security Baseline 1.0: 11 checks (M10-F3)."""

from __future__ import annotations

import pytest

from aios_core.security import (
    SecurityChecker,
    SecurityChecks,
    SecurityItem,
    SecurityReport,
    SecuritySeverity,
    SecurityStatus,
    format_security_report,
)


# ---------------------------------------------------------------------------
# AC1: đủ 12 items (M11-P3c R8 thêm vendor_integrity)
# ---------------------------------------------------------------------------

def test_has_11_items():
    report = SecurityChecker().run()
    ids = {i.id for i in report.items}
    assert ids == {
        "identity", "authentication", "authorization", "secrets", "encryption",
        "audit", "plugin_signing", "supply_chain", "sandbox",
        "network_policy", "data_boundary",
        "vendor_integrity",  # M11-P3c/R8
    }
    assert len(report.items) == 12


# ---------------------------------------------------------------------------
# AC2/AC3: deterministic + evidence thật
# ---------------------------------------------------------------------------

def test_items_deterministic():
    r1 = SecurityChecker().run()
    r2 = SecurityChecker().run()
    assert [(i.id, i.status) for i in r1.items] == \
        [(i.id, i.status) for i in r2.items]


def test_evidence_non_empty_and_specific():
    """R1: evidence bắt buộc + chứa nội dung cụ thể (không check giả)."""
    report = SecurityChecker().run()
    for item in report.items:
        assert item.evidence.strip(), f"{item.id}: evidence rỗng"
        assert item.recommendation.strip(), f"{item.id}: recommendation rỗng"


def test_critical_checks_actually_verify_sources():
    """Secrets/audit/sandbox/plugin_signing phải PASS (cơ chế thật tồn tại)."""
    report = SecurityChecker().run()
    by_id = {i.id: i for i in report.items}
    for cid in ("secrets", "audit", "sandbox", "plugin_signing"):
        assert by_id[cid].status == SecurityStatus.PASS, \
            f"{cid}: {by_id[cid].evidence}"


def test_identity_check_verifies_module():
    by_id = {i.id: i for i in SecurityChecker().run().items}
    assert "Principal" in by_id["identity"].evidence


# ---------------------------------------------------------------------------
# AC4: blocking chỉ khi critical FAIL
# ---------------------------------------------------------------------------

def test_blocking_only_critical_fail():
    items = [
        SecurityItem(id="a", name="a", severity=SecuritySeverity.HIGH,
                     status=SecurityStatus.FAIL, evidence="e", recommendation="r"),
        SecurityItem(id="b", name="b", severity=SecuritySeverity.CRITICAL,
                     status=SecurityStatus.FAIL, evidence="e", recommendation="r"),
    ]
    report = SecurityReport(items=items)
    assert report.blocking is True
    assert len(report.failures) == 2

    ok = SecurityReport(items=[
        SecurityItem(id="c", name="c", severity=SecuritySeverity.CRITICAL,
                     status=SecurityStatus.PASS, evidence="e", recommendation="r"),
        SecurityItem(id="d", name="d", severity=SecuritySeverity.CRITICAL,
                     status=SecurityStatus.WARN, evidence="e", recommendation="r"),
    ])
    assert ok.blocking is False


def test_item_validation_extra_forbid_and_required():
    with pytest.raises(Exception):
        SecurityItem(id="x", name="x", severity=SecuritySeverity.HIGH,
                     status=SecurityStatus.PASS, evidence="", recommendation="r")
    with pytest.raises(Exception):
        SecurityItem(id="x", name="x", severity=SecuritySeverity.HIGH,
                     status=SecurityStatus.PASS, evidence="e", recommendation="", bogus=1)


# ---------------------------------------------------------------------------
# AC5: CLI
# ---------------------------------------------------------------------------

def test_cli_security_check(capsys):
    from aios_core.workflow.cli import main

    assert main(["security-check"]) == 0
    out = capsys.readouterr().out
    assert "identity" in out and "secrets" in out
    assert "Security:" in out
