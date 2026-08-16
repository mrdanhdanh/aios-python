"""Rendering — Deterministic Visual Runtime (M11-P1, TASK-079).

RenderReplay + DeterministicHarness: render là pure function của
(state, time, seed) — AIOS có thể replay đúng ảnh (pixel-stable).

Kết quả dùng Verification Kernel (INV-035, TASK-078): fail-closed,
không chạy được → BLOCKED/NOT_EXECUTED (KHÔNG PASS).
"""

from __future__ import annotations

from .asset import (
    ASSET_KINDS,
    AssetCapability,
    AssetError,
    AssetOutput,
    AssetPipeline,
    AssetSpec,
)
from .contracts import (
    InputEvent,
    RenderFrame,
    RenderFn,
    RenderReplayResult,
)
from .evidence import PNG_1PX_BASE64, VisualEvidence
from .harness import DeterministicHarness
from .idempotency import AssetIdempotencyClassifier
from .matcher import CreativeMatcher, MatchResult
from .prng import SeededPrng
from .probe import ProbeResult, VisualRegressionProbe
from .reference import (
    MockVisionAnalyzer,
    ReferenceAssetUnderstanding,
    ReferenceDescription,
)
from .registry import AssetCapabilityRegistry, default_asset_capabilities
from .replay import RenderReplay
from .timeline import RenderTimeline
from .ui_state import UIState, canonical_json
from .workflows import (
    creative_workflow_definitions,
    register_creative_workflows,
)

__all__ = [
    "ASSET_KINDS",
    "AssetCapability",
    "AssetCapabilityRegistry",
    "AssetError",
    "AssetIdempotencyClassifier",
    "AssetOutput",
    "AssetPipeline",
    "AssetSpec",
    "CreativeMatcher",
    "DeterministicHarness",
    "InputEvent",
    "MatchResult",
    "PNG_1PX_BASE64",
    "ProbeResult",
    "ReferenceAssetUnderstanding",
    "ReferenceDescription",
    "MockVisionAnalyzer",
    "RenderFn",
    "RenderFrame",
    "RenderReplay",
    "RenderReplayResult",
    "RenderTimeline",
    "SeededPrng",
    "UIState",
    "VisualEvidence",
    "VisualRegressionProbe",
    "canonical_json",
    "creative_workflow_definitions",
    "default_asset_capabilities",
    "register_creative_workflows",
]
