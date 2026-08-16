"""Tests M11-P3b/c/d — R6 Creative Domain + R8 Vendor Integrity + R12 Reference (TASK-082)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from aios_core.config import Settings
from aios_core.orchestrator.workflow_matcher import (
    CREATIVE_CONFIDENCE,
    WorkflowMatcher,
)
from aios_core.rendering import (
    AssetError,
    CreativeMatcher,
    ReferenceAssetUnderstanding,
    register_creative_workflows,
)
from aios_core.security.checks import SecurityChecks, SecurityContext
from aios_core.security.contracts import SecurityStatus
from aios_core.workflow.compiler import MockCompiler
from aios_core.workflow.library import WorkflowLibrary


# -- AC1/AC2/AC3: R6 Creative Domain ------------------------------------------

class _FakeCreativeMatcher:
    """CreativeMatcher giả — suggest() trả list MatchResult."""

    def __init__(self, capability_id: str = "asset:sprite") -> None:
        self._cap = capability_id

    def suggest(self, request: str):  # noqa: ANN201
        from aios_core.rendering import MatchResult

        return [MatchResult(
            capability_id=self._cap,
            name="sprite-forge",
            score=10,
            reason="kind:sprite",
        )]


def _library_with_creative() -> WorkflowLibrary:
    library = WorkflowLibrary()
    register_creative_workflows(library)
    return library


def test_r6_creative_pre_route_build_game():
    matcher = WorkflowMatcher(_library_with_creative(), _FakeCreativeMatcher())
    result = matcher.match("build a game for my cat")
    assert result is not None
    assert result.workflow_name == "creative:asset:asset:sprite"
    assert result.matched_by == "creative"
    assert result.confidence == CREATIVE_CONFIDENCE


def test_r6_creative_pre_route_pixel_art():
    matcher = WorkflowMatcher(_library_with_creative(), _FakeCreativeMatcher("asset:sprite"))
    result = matcher.match("generate pixel art sprite")
    assert result is not None
    assert result.matched_by == "creative"
    assert result.workflow_name.startswith("creative:asset:")


def test_r6_no_creative_matcher_falls_through():
    """creative_matcher=None → KHÔNG pre-route creative (hành vi cũ)."""
    matcher = WorkflowMatcher(_library_with_creative())
    result = matcher.match("build a game")
    # Workflow creative trong library vẫn match qua token-search (fallthrough)
    # nhưng KHÔNG qua pre-route creative (matched_by != "creative")
    assert result is not None
    assert result.matched_by != "creative"


def test_r6_backend_request_unchanged():
    """Request backend thường không có từ khóa creative → không pre-route."""
    matcher = WorkflowMatcher(_library_with_creative(), _FakeCreativeMatcher())
    result = matcher.match("run workflow.yaml")
    assert result is None or result.matched_by != "creative"


def test_r6_creative_matcher_empty_suggestion_no_match():
    class _Empty:
        def suggest(self, request):  # noqa: ANN001, ANN201
            return []

    matcher = WorkflowMatcher(_library_with_creative(), _Empty())
    result = matcher.match("build a game")
    # Matcher rỗng → fallthrough (không pre-route), có thể match token
    assert result is None or result.matched_by != "creative"


def test_r6_workflows_registered_and_compile():
    library = _library_with_creative()
    names = library.list()
    assert "creative/game_scaffold" in names
    assert "creative/sprite_generate" in names
    for name in ("creative/game_scaffold", "creative/sprite_generate"):
        definition = library.get(name)
        MockCompiler().compile(definition)  # không raise


# -- AC4/AC5/AC6: R8 Vendor Integrity -----------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_r8_vendor_integrity_hash_match_pass(tmp_path: Path):
    bundle = tmp_path / "vendor.js"
    bundle.write_bytes(b"console.log('v1')")
    settings = Settings(security={"vendor_bundles": {str(bundle): _sha256(bundle.read_bytes())}})
    checks = SecurityChecks(SecurityContext(settings=settings))
    item = checks.vendor_integrity()
    assert item.status == SecurityStatus.PASS


def test_r8_vendor_integrity_hash_mismatch_fail(tmp_path: Path):
    bundle = tmp_path / "vendor.js"
    bundle.write_bytes(b"console.log('v1')")
    settings = Settings(security={"vendor_bundles": {str(bundle): "0" * 64}})
    checks = SecurityChecks(SecurityContext(settings=settings))
    item = checks.vendor_integrity()
    assert item.status == SecurityStatus.FAIL
    assert "hash mismatch" in item.evidence


def test_r8_vendor_integrity_missing_file_fail(tmp_path: Path):
    settings = Settings(security={"vendor_bundles": {str(tmp_path / "nope.js"): "0" * 64}})
    checks = SecurityChecks(SecurityContext(settings=settings))
    item = checks.vendor_integrity()
    assert item.status == SecurityStatus.FAIL
    assert "missing" in item.evidence


def test_r8_no_config_is_pass():
    checks = SecurityChecks(SecurityContext(settings=Settings()))
    item = checks.vendor_integrity()
    assert item.status == SecurityStatus.PASS
    assert "no vendor bundles" in item.evidence


def test_r8_twelve_checks_total():
    checks = SecurityChecks(SecurityContext(settings=Settings()))
    items = checks.run_all()
    assert len(items) == 12
    assert any(i.id == "vendor_integrity" for i in items)


# -- AC7/AC8/AC9: R12 Reference-Asset -----------------------------------------

def test_r12_ingest_full_description(tmp_path: Path):
    image = tmp_path / "ref.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\nfakepng")
    desc = ReferenceAssetUnderstanding().ingest(str(image))
    assert desc.scene
    assert desc.objects
    assert desc.style
    assert len(desc.palette) == 3
    assert all(c.startswith("#") for c in desc.palette)


def test_r12_mock_deterministic(tmp_path: Path):
    image = tmp_path / "ref.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\nsamecontent")
    a = ReferenceAssetUnderstanding().ingest(str(image))
    b = ReferenceAssetUnderstanding().ingest(str(image))
    assert a.model_dump() == b.model_dump()


def test_r12_different_image_different_description(tmp_path: Path):
    img1 = tmp_path / "a.png"
    img1.write_bytes(b"content-a")
    img2 = tmp_path / "b.png"
    img2.write_bytes(b"content-b")
    d1 = ReferenceAssetUnderstanding().ingest(str(img1))
    d2 = ReferenceAssetUnderstanding().ingest(str(img2))
    assert d1.scene != d2.scene or d1.palette != d2.palette


def test_r12_missing_image_fail_closed(tmp_path: Path):
    with pytest.raises(AssetError):
        ReferenceAssetUnderstanding().ingest(str(tmp_path / "missing.png"))


def test_r12_merge_params_no_overwrite(tmp_path: Path):
    image = tmp_path / "ref.png"
    image.write_bytes(b"data")
    merged = ReferenceAssetUnderstanding().to_asset_params(
        str(image), existing={"width": 32, "palette": ["#ff0000"]}
    )
    assert merged["width"] == 32  # params có sẵn giữ nguyên
    assert merged["palette"] == ["#ff0000"]  # không bị ghi đè bởi desc.palette
    assert "reference" in merged
    assert merged["reference"]["scene"]
