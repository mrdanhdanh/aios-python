"""Tests M11-P3 — AssetPipeline/R4 Registry/R11 Matcher (TASK-081)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest

from aios_core.rendering import (
    AssetCapability,
    AssetCapabilityRegistry,
    AssetError,
    AssetIdempotencyClassifier,
    AssetOutput,
    AssetPipeline,
    AssetSpec,
    CreativeMatcher,
    default_asset_capabilities,
)
from aios_core.rendering.idempotency import AssetOpClass


class MockPipeline:
    """Pipeline deterministic: sha256 từ spec canonical."""

    def produce(self, spec: AssetSpec) -> AssetOutput:
        import json

        if spec.kind == "audio":
            raise AssetError("audio chưa hỗ trợ trong mock")
        canonical = json.dumps(
            spec.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        )
        return AssetOutput(
            spec=spec,
            artifact_ref=f"mock://{spec.kind}/{spec.name}",
            sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            size=len(canonical),
            produced_at=datetime.now(timezone.utc).isoformat(),
            idempotency=AssetOpClass.AT_LEAST_ONCE,
        )


def sprite_cap(**overrides) -> AssetCapability:
    base = dict(
        id="sprite-forge",
        name="Sprite Forge",
        description="Generate 2D pixel sprites with palette",
        kinds=["sprite", "animation"],
        pipeline=MockPipeline(),
        version="1.0",
        source="skills/agent-sprite-forge/",
    )
    base.update(overrides)
    return AssetCapability(**base)


def audio_cap(**overrides) -> AssetCapability:
    base = dict(
        id="audio-synth",
        name="Audio Synth",
        description="Synthesize chiptune audio assets",
        kinds=["audio"],
        pipeline=MockPipeline(),
    )
    base.update(overrides)
    return AssetCapability(**base)


# -- AC1: contracts --------------------------------------------------------------

def test_asset_spec_contract():
    s = AssetSpec(kind="sprite", name="cat", seed=1, params={"palette": "pixel"})
    assert s.kind == "sprite"
    assert s.seed == 1
    with pytest.raises(ValueError):
        AssetSpec(kind="bogus", name="x")  # kind ngoài 6 loại
    with pytest.raises(ValueError):
        AssetSpec(kind="sprite", name="x", extra=1)  # extra=forbid


def test_asset_output_contract():
    spec = AssetSpec(kind="sprite", name="cat")
    out = AssetOutput(spec=spec, artifact_ref="mock://sprite/cat", sha256="a" * 64,
                      size=10, produced_at="2026-01-01T00:00:00Z",
                      idempotency=AssetOpClass.EXACTLY_ONCE)
    assert out.sha256 == "a" * 64


# -- AC2: pipeline produce ----------------------------------------------------------

def test_pipeline_produce_deterministic():
    p = MockPipeline()
    s1 = AssetSpec(kind="sprite", name="cat", seed=5)
    s2 = AssetSpec(kind="sprite", name="cat", seed=5)
    assert p.produce(s1).sha256 == p.produce(s2).sha256


def test_pipeline_unsupported_kind_raises():
    p = MockPipeline()
    with pytest.raises(AssetError):
        p.produce(AssetSpec(kind="audio", name="bgm"))


# -- AC3/AC4: registry ---------------------------------------------------------------

def test_registry_register_discover_list_get():
    reg = AssetCapabilityRegistry()
    reg.register(sprite_cap())
    reg.register(audio_cap())
    assert reg.count() == 2
    assert [c.id for c in reg.discover("sprite")] == ["sprite-forge"]
    assert {c.id for c in reg.discover("audio")} == {"audio-synth"}
    assert reg.get("sprite-forge").name == "Sprite Forge"
    assert reg.get("nope") is None


def test_registry_same_kind_multiple():
    reg = AssetCapabilityRegistry()
    reg.register(sprite_cap())
    reg.register(sprite_cap(id="sprite-forge-2", name="Sprite Forge 2"))
    assert len(reg.discover("sprite")) == 2


# -- AC8: produce idempotency fail-closed ---------------------------------------------

def test_registry_produce_fail_closed():
    reg = AssetCapabilityRegistry()
    reg.register(sprite_cap())
    out = reg.produce("sprite-forge", AssetSpec(kind="sprite", name="cat"))
    assert out.sha256
    assert reg.snapshot_counters()["asset_produce_count"] == 1
    # capability thiếu → AssetError + counter failures
    with pytest.raises(AssetError):
        reg.produce("nope", AssetSpec(kind="sprite", name="x"))
    # pipeline raise → AssetError + counter failures
    reg.register(audio_cap())
    with pytest.raises(AssetError):
        reg.produce("audio-synth", AssetSpec(kind="audio", name="bgm"))
    snap = reg.snapshot_counters()
    assert snap["asset_failures"] == 2
    assert snap["asset_produce_count"] == 1


def test_idempotency_fail_closed_classifier():
    c = AssetIdempotencyClassifier()
    assert c.classify("sprite") == AssetOpClass.AT_MOST_ONCE  # không khai báo
    assert c.is_retryable("sprite") is False


# -- AC5/AC6: matcher ---------------------------------------------------------------

def test_matcher_kind_match_priority():
    reg = AssetCapabilityRegistry()
    reg.register(sprite_cap())
    reg.register(audio_cap())
    m = CreativeMatcher(reg)
    results = m.match("generate sprite")
    assert results, "phải match sprite"
    assert results[0].capability_id == "sprite-forge"
    assert results[0].score >= 10  # kind match


def test_matcher_keyword_and_sort():
    reg = AssetCapabilityRegistry()
    reg.register(sprite_cap())
    reg.register(audio_cap())
    m = CreativeMatcher(reg)
    results = m.match("pixel art")
    assert results[0].capability_id == "sprite-forge"  # "pixel" trong description


def test_matcher_suggest_reuse():
    reg = AssetCapabilityRegistry()
    reg.register(sprite_cap())
    m = CreativeMatcher(reg)
    suggest = m.suggest("generate pixel art")
    assert suggest, "phải gợi ý capability tồn tại (reuse > reimplement)"
    assert suggest[0].capability_id == "sprite-forge"


def test_matcher_no_match_empty():
    m = CreativeMatcher(AssetCapabilityRegistry())
    assert m.match("anything weird") == []


# -- AC7: default capabilities từ skills/ -----------------------------------------------

def test_default_capabilities_from_repo(tmp_path):
    # Tạo skills/agent-sprite-forge/manifest.json giả trong tmp_path
    skill_dir = tmp_path / "skills" / "agent-sprite-forge"
    skill_dir.mkdir(parents=True)
    (skill_dir / "manifest.json").write_text(json.dumps({
        "id": "agent-sprite-forge",
        "name": "Agent Sprite Forge",
        "description": "Generate pixel sprites + animations",
        "kinds": ["sprite", "animation"],
        "version": "1.0",
    }), encoding="utf-8")
    caps = default_asset_capabilities(str(tmp_path))
    assert len(caps) == 1
    assert caps[0].id == "agent-sprite-forge"
    assert caps[0].source == "skills/agent-sprite-forge/"
    # produce qua skill pipeline (placeholder deterministic)
    out = caps[0].pipeline.produce(AssetSpec(kind="sprite", name="cat", seed=1))
    assert out.sha256


def test_default_capabilities_missing_skill_no_fail(tmp_path):
    # Không có skills/ → registry không fail, trả rỗng
    assert default_asset_capabilities(str(tmp_path)) == []


# -- misc ----------------------------------------------------------------------------

def test_asset_pipeline_protocol_duck_typed():
    """AssetCapability chấp nhận pipeline duck-typed (không cần subclass)."""
    cap = sprite_cap()
    assert callable(cap.pipeline.produce)
    manifest = cap.model_dump_manifest()
    assert "pipeline" not in manifest  # không serialize pipeline
    assert manifest["kinds"] == ["sprite", "animation"]
