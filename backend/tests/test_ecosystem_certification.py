"""TASK-049 — Certification (M8-E7) tests."""

import pytest

from aios_core.ecosystem import (
    CertLevel,
    CertReport,
    CertificationEngine,
    CertificationError,
)

GOOD_MANIFEST = {
    "id": "github.integration",
    "name": "GitHub Integration",
    "version": "1.2.0",
    "aios": {"min": "1.8.0", "max": "2.x"},
    "permissions": ["repository.read", "repository.write"],
    "publisher": {"id": "danh", "name": "Danh"},
    "signature": "abc123",
}


def test_cert_levels():
    assert [level.value for level in CertLevel] == [
        "community", "verified", "certified", "enterprise_certified",
    ]


def test_good_manifest_enterprise_certified():
    report = CertificationEngine().certify(GOOD_MANIFEST)
    assert report.level == CertLevel.ENTERPRISE_CERTIFIED
    assert report.passed == 6 and report.failed == 0
    assert len(report.checks) == 6


def test_missing_permissions_blocks():
    manifest = {**GOOD_MANIFEST, "permissions": []}
    report = CertificationEngine().certify(manifest)
    assert report.level == CertLevel.COMMUNITY
    assert any(check.name == "permission" and not check.passed for check in report.checks)


def test_wildcard_security_fail_hard_blocks():
    manifest = {**GOOD_MANIFEST, "permissions": ["*"]}
    report = CertificationEngine().certify(manifest)
    assert report.level == CertLevel.COMMUNITY
    assert any(check.name == "security" and not check.passed for check in report.checks)


def test_verified_without_publisher_signature():
    manifest = {**GOOD_MANIFEST}
    del manifest["publisher"]
    del manifest["signature"]
    report = CertificationEngine().certify(manifest)
    assert report.level == CertLevel.CERTIFIED  # certified (có security pass), chưa enterprise


def test_contract_check_catches_bad_version():
    report = CertificationEngine().certify({**GOOD_MANIFEST, "version": "nope"})
    assert report.level == CertLevel.COMMUNITY
    assert any(check.name == "contract" and not check.passed for check in report.checks)


def test_injectable_check_fn():
    def fake_check(manifest):
        return False, "harness gate failed"

    engine = CertificationEngine(checks=[("harness", fake_check)])
    report = engine.certify(GOOD_MANIFEST)
    assert report.level == CertLevel.COMMUNITY
    assert report.failed == 1


def test_threshold_validation():
    with pytest.raises(CertificationError):
        CertificationEngine(threshold=1.5)
    with pytest.raises(CertificationError):
        CertificationEngine(checks=[])


def test_deterministic_and_no_mutation():
    engine = CertificationEngine()
    first = engine.certify(dict(GOOD_MANIFEST))
    second = engine.certify(dict(GOOD_MANIFEST))
    assert first.model_dump() == second.model_dump()
    assert "unknown" not in GOOD_MANIFEST  # input không bị mutate
