"""Rendering — Deterministic Visual Runtime (M11-P1, TASK-079).

RenderReplay + DeterministicHarness: render là pure function của
(state, time, seed) — AIOS có thể replay đúng ảnh (pixel-stable).

Kết quả dùng Verification Kernel (INV-035, TASK-078): fail-closed,
không chạy được → BLOCKED/NOT_EXECUTED (KHÔNG PASS).
"""

from __future__ import annotations

from .contracts import (
    InputEvent,
    RenderFrame,
    RenderFn,
    RenderReplayResult,
)
from .evidence import PNG_1PX_BASE64, VisualEvidence
from .harness import DeterministicHarness
from .idempotency import AssetIdempotencyClassifier
from .prng import SeededPrng
from .probe import ProbeResult, VisualRegressionProbe
from .replay import RenderReplay
from .timeline import RenderTimeline
from .ui_state import UIState, canonical_json

__all__ = [
    "AssetIdempotencyClassifier",
    "DeterministicHarness",
    "InputEvent",
    "PNG_1PX_BASE64",
    "ProbeResult",
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
]
