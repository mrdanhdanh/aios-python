"""TASK-048 — Marketplace / Trust Chain (M8-E6) tests."""

import pytest

from aios_core.ecosystem import (
    MarketplaceError,
    MarketplaceRegistry,
    Publisher,
    TrustChain,
    canonical_json,
    sign_manifest,
    verify_signature,
)

KEY = "k" * 64

MANIFEST = {
    "id": "github.integration",
    "name": "GitHub Integration",
    "version": "1.2.0",
    "aios": {"min": "0.1.0", "max": "2.x"},
    "permissions": ["repository.read"],
    "dependencies": ["aios-core"],
}


def test_signature_deterministic_and_verify():
    sig = sign_manifest(MANIFEST, KEY)
    assert sig == sign_manifest(MANIFEST, KEY)  # deterministic
    assert verify_signature(MANIFEST, KEY, sig)
    tampered = {**MANIFEST, "version": "9.9.9"}
    assert not verify_signature(tampered, KEY, sig)
    assert canonical_json(MANIFEST) == canonical_json(dict(MANIFEST))


def test_trust_chain_full_pass(tmp_path):
    registry = MarketplaceRegistry(tmp_path / "mp.db")
    registry.register_publisher(Publisher(id="danh", name="Danh"), KEY)
    record = registry.publish("danh", KEY, MANIFEST)
    result = registry.install_flow("danh", record.name, KEY)
    assert result.approved
    assert result.step == "install"
    assert result.cert_level.value in ("certified", "enterprise_certified")


def test_trust_chain_signature_fail():
    chain = TrustChain()
    result = chain.run(MANIFEST, "bad-signature", KEY)
    assert not result.approved
    assert result.step == "signature_verification"


def test_trust_chain_manifest_fail():
    chain = TrustChain()
    result = chain.run({"id": "x"}, "sig", KEY)
    assert not result.approved
    assert result.step == "manifest_validation"


def test_trust_chain_dependency_fail():
    chain = TrustChain(entry_resolver=lambda _id: None)
    result = chain.run(MANIFEST, sign_manifest(MANIFEST, KEY), KEY)
    assert not result.approved
    assert result.step == "dependency_check"


def test_trust_chain_compat_fail():
    chain = TrustChain(aios_version="3.0.0")
    result = chain.run(MANIFEST, sign_manifest(MANIFEST, KEY), KEY)
    assert not result.approved
    assert result.step == "compatibility_check"


def test_trust_chain_security_scan_fail():
    manifest = {**MANIFEST, "permissions": ["*"]}
    chain = TrustChain()
    result = chain.run(manifest, sign_manifest(manifest, KEY), KEY)
    assert not result.approved
    assert result.step == "security_scan"


def test_trust_chain_no_permissions_fail():
    manifest = {**MANIFEST, "permissions": []}
    chain = TrustChain()
    result = chain.run(manifest, sign_manifest(manifest, KEY), KEY)
    assert not result.approved
    assert result.step == "permission_analysis"


def test_publisher_key_not_serialized(tmp_path):
    registry = MarketplaceRegistry(tmp_path / "mp.db")
    registry.register_publisher(Publisher(id="danh", signing_key_id="fp-1"), KEY)
    registry.publish("danh", KEY, MANIFEST)
    raw = (tmp_path / "mp.db").read_bytes()
    assert KEY.encode() not in raw  # raw key không bao giờ persist


def test_install_flow_package_missing(tmp_path):
    registry = MarketplaceRegistry(tmp_path / "mp.db")
    result = registry.install_flow("danh", "nope", KEY)
    assert not result.approved
    assert result.step == "download"


def test_publish_upsert_version(tmp_path):
    registry = MarketplaceRegistry(tmp_path / "mp.db")
    registry.register_publisher(Publisher(id="danh"), KEY)
    registry.publish("danh", KEY, MANIFEST)
    registry.publish("danh", KEY, {**MANIFEST, "version": "2.0.0"})
    record = registry.get_package("danh", "GitHub Integration")
    assert record.version == "2.0.0"
    assert registry.get_package("danh", "GitHub Integration").signature != ""


def test_short_key_rejected(tmp_path):
    registry = MarketplaceRegistry(tmp_path / "mp.db")
    with pytest.raises(MarketplaceError):
        registry.register_publisher(Publisher(id="danh"), "short")
