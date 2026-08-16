"""Tests M11-P2/P2b — VisualEvidence + UIState (TASK-080).

Cover: UIState canonical/hash/diff, VisualEvidence fields, probe compare
(giống/state-diff/missing-ref/pixel-diff), observability metrics.
"""

from __future__ import annotations

import pytest

from aios_core.observability.visual import VisualMetrics, get_visual_metrics
from aios_core.rendering import (
    PNG_1PX_BASE64,
    UIState,
    VisualEvidence,
    VisualRegressionProbe,
)
from aios_core.rendering.contracts import InputEvent
from aios_core.verification.state import VerificationState, VerificationVerdict


def make_state(**overrides) -> UIState:
    base = dict(
        screen="game",
        entities={"player": {"x": 160, "y": 90, "scale": 3}},
        input={"left": False, "right": True},
        t=0.5,
        seed=42,
    )
    base.update(overrides)
    return UIState(**base)


def make_evidence(**overrides) -> VisualEvidence:
    base = dict(
        screenshot=PNG_1PX_BASE64,
        dom_snapshot={"tag": "canvas", "attrs": {"id": "game"}, "children": []},
        render_state=make_state(),
        input_timeline=[InputEvent(type="keydown", timestamp=100.0,
                                   payload={"key": "start"})],
        browser_meta={"browser": "chromium", "os": "windows",
                      "viewport": [640, 360], "device_scale_factor": 1.0},
        seed=42,
    )
    base.update(overrides)
    return VisualEvidence(**base)


# -- AC1: UIState canonical + hash ---------------------------------------------

def test_ui_state_hash_deterministic():
    a = make_state()
    b = make_state()
    assert a.canonical() == b.canonical()
    assert a.state_hash() == b.state_hash()


def test_ui_state_canonical_sorted():
    s = UIState(screen="game", entities={"z": {"v": 1}, "a": {"v": 2}},
                input={"b": True, "a": False})
    c = s.canonical()
    # sort_keys: "entities.a" trước "entities.z" (cùng nhóm)
    assert c.index('"a":{"v":2}') < c.index('"z":{"v":1}')


# -- AC2: UIState validation -----------------------------------------------------

def test_ui_state_extra_forbidden():
    with pytest.raises(ValueError):
        UIState(screen="game", bogus=1)


def test_ui_state_entities_must_be_dict():
    with pytest.raises(ValueError):
        UIState(screen="game", entities=[1, 2])


# -- AC3: VisualEvidence fields --------------------------------------------------

def test_visual_evidence_fields():
    ev = make_evidence()
    assert ev.screenshot.startswith("data:image/png;base64,")
    assert ev.render_state.screen == "game"
    assert ev.input_timeline[0].type == "keydown"
    assert ev.browser_meta["browser"] == "chromium"
    assert ev.pixel_diff == -1.0
    assert ev.has_screenshot() is True


def test_visual_evidence_requires_render_state():
    with pytest.raises(ValueError):
        VisualEvidence(screenshot=PNG_1PX_BASE64)  # thiếu render_state


# -- AC4: probe giống nhau → PASS --------------------------------------------------

def test_probe_identical_evidence_passes():
    probe = VisualRegressionProbe()
    result = probe.compare(make_evidence(), make_evidence())
    assert result.passed is True
    assert result.pixel_diff == 0.0
    assert result.outcome.state == VerificationState.PASS
    assert result.outcome.verdict == VerificationVerdict.PASS


# -- AC5: state khác → phát hiện (reasoning R10) ------------------------------------

def test_probe_detects_state_diff():
    probe = VisualRegressionProbe()
    current = make_evidence(render_state=make_state(
        entities={"player": {"x": 160, "y": 90, "scale": 2}},  # bug scale
    ))
    result = probe.compare(make_evidence(), current)
    assert result.passed is False
    assert result.outcome.state == VerificationState.FAIL
    assert any(d["path"].endswith("scale") for d in result.state_diffs)
    assert result.outcome.verdict == VerificationVerdict.FAIL


# -- AC6: missing ref → MISSING_EVIDENCE (KHÔNG PASS — INV-035) -----------------------

def test_probe_missing_ref_not_pass():
    probe = VisualRegressionProbe()
    result = probe.compare(None, make_evidence())
    assert result.passed is False
    assert result.outcome.state == VerificationState.MISSING_EVIDENCE
    assert result.outcome.verdict == VerificationVerdict.INCONCLUSIVE
    assert "INV-035" in result.outcome.evidence


def test_probe_missing_screenshot_not_pass():
    probe = VisualRegressionProbe()
    # screenshot không phải data URI → has_screenshot()=False → MISSING_EVIDENCE
    bad = make_evidence(screenshot="file:///golden/ref.png")
    result = probe.compare(bad, make_evidence())
    assert result.outcome.state == VerificationState.MISSING_EVIDENCE
    assert result.passed is False


def test_probe_both_missing_ref_still_not_pass():
    probe = VisualRegressionProbe()
    result = probe.compare(None, None)
    assert result.outcome.state == VerificationState.MISSING_EVIDENCE
    assert result.passed is False


# -- AC7: pixel diff → FAIL kèm evidence ------------------------------------------------

def test_probe_pixel_diff_fails_with_evidence():
    probe = VisualRegressionProbe()
    diff = make_evidence(screenshot=(
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        "AA=="  # thêm bytes → kích thước khác → 100% diff
    ))
    result = probe.compare(make_evidence(), diff)
    assert result.passed is False
    assert result.outcome.state == VerificationState.FAIL
    assert result.pixel_diff > 0
    assert "pixel_diff" in result.outcome.evidence


def test_probe_corrupt_screenshot_is_missing_evidence():
    probe = VisualRegressionProbe()
    bad = make_evidence(screenshot="data:image/png;base64,!!!not-base64!!!")
    result = probe.compare(make_evidence(), bad)
    assert result.outcome.state == VerificationState.MISSING_EVIDENCE
    assert result.passed is False


# -- AC8: observability metrics ----------------------------------------------------------

def test_visual_metrics_registry():
    m = VisualMetrics()
    m.record_probe(passed=True, pixel_diff=0.0)
    m.record_probe(passed=False, pixel_diff=12.5)
    snap = m.snapshot()
    assert snap["counters"]["visual_probe_count"] == 2
    assert snap["counters"]["visual_fail_closed_violations"] == 1
    assert snap["gauges"]["visual_pixel_diff_max"] == 12.5


def test_visual_metrics_singleton_idempotent():
    a = get_visual_metrics()
    b = get_visual_metrics()
    assert a is b


# -- AC9 helper: evidence model_dump roundtrip (JSON CLI) ----------------------------------

def test_evidence_json_roundtrip():
    import json

    ev = make_evidence()
    restored = VisualEvidence.model_validate(
        json.loads(ev.model_dump_json())
    )
    assert restored == ev
