"""Tests M11-P1 RenderReplay / DeterministicHarness (TASK-079).

Cover: contracts, timeline, replay deterministic, PRNG seed, harness
stable/unstable + BLOCKED (INV-035), asset idempotency, arch allow-list.
"""

from __future__ import annotations

import pytest

from aios_core.rendering import (
    AssetIdempotencyClassifier,
    DeterministicHarness,
    RenderReplay,
    RenderTimeline,
    SeededPrng,
)
from aios_core.rendering.contracts import InputEvent, RenderFrame
from aios_core.rendering.prng import KNOWN_VECTOR
from aios_core.verification.state import VerificationState, VerificationVerdict


def make_render(width=8, height=8):
    """Mock render_fn deterministic: pixel = f(index, t, seed, state)."""

    def render_fn(frame: RenderFrame) -> bytes:
        state_byte = int(frame.state_hash[:2], 16) if frame.state_hash else 0
        buf = bytearray(width * height * 3)
        for i in range(len(buf)):
            buf[i] = (frame.frame_index * 7 + int(frame.t * 13)
                      + frame.seed + state_byte) % 256
        return bytes(buf)

    return render_fn


def sample_timeline() -> RenderTimeline:
    t = RenderTimeline()
    t.record("keydown", 100, {"key": "start"})
    t.record("pointer", 500, {"x": 10, "y": 20})
    return t


# -- AC1: contracts -----------------------------------------------------------

def test_input_event_contract():
    e = InputEvent(type="keydown", timestamp=100.0, payload={"key": "a"})
    assert e.type == "keydown"
    assert e.timestamp == 100.0
    with pytest.raises(ValueError):  # extra field bị cấm
        InputEvent(type="x", timestamp=1, extra="no")


def test_render_frame_contract():
    f = RenderFrame(frame_index=0, t=0.0, seed=1)
    assert f.pixel_hash == ""
    with pytest.raises(ValueError):
        RenderFrame(frame_index=0, t=0.0, seed=1, bogus=1)


# -- AC2: timeline ------------------------------------------------------------

def test_timeline_record_order():
    t = sample_timeline()
    assert len(t) == 2
    assert [e.type for e in t.events] == ["keydown", "pointer"]
    assert t.events[1].timestamp > t.events[0].timestamp


def test_timeline_rejects_decreasing_timestamp():
    t = RenderTimeline()
    t.record("a", 100.0)
    with pytest.raises(ValueError):
        t.record("b", 50.0)  # timestamp giảm → fail-closed


def test_timeline_state_hash_deterministic():
    t1 = sample_timeline()
    t2 = sample_timeline()
    assert t1.state_hash(10, 60.0) == t2.state_hash(10, 60.0)


# -- AC3: replay deterministic --------------------------------------------------

def test_replay_same_seed_same_hash():
    render = make_render()
    replay = RenderReplay(render, width=8, height=8, fps=60.0)
    a = replay.replay(sample_timeline(), seed=7, num_frames=30)
    b = replay.replay(sample_timeline(), seed=7, num_frames=30)
    assert [f.pixel_hash for f in a] == [f.pixel_hash for f in b]
    assert a[0].pixel_hash  # hash không rỗng


# -- AC4: đổi seed/input → khác -------------------------------------------------

def test_replay_different_seed_different_hash():
    render = make_render()
    replay = RenderReplay(render, width=8, height=8)
    a = replay.replay(sample_timeline(), seed=1, num_frames=20)
    b = replay.replay(sample_timeline(), seed=2, num_frames=20)
    assert [f.pixel_hash for f in a] != [f.pixel_hash for f in b]


def test_replay_different_input_different_hash():
    render = make_render()
    replay = RenderReplay(render, width=8, height=8)
    t1 = sample_timeline()
    t2 = sample_timeline()
    t2.record("keyup", 600, {"key": "start"})
    a = replay.replay(t1, seed=1, num_frames=60)  # 1s — đủ để event 500/600ms áp dụng
    b = replay.replay(t2, seed=1, num_frames=60)
    assert [f.pixel_hash for f in a] != [f.pixel_hash for f in b]


# -- AC5: PRNG ------------------------------------------------------------------

def test_prng_deterministic():
    assert SeededPrng(1).sequence(100) == SeededPrng(1).sequence(100)
    assert SeededPrng(1).sequence(100) != SeededPrng(2).sequence(100)


def test_prng_known_vector():
    got = SeededPrng(1).sequence(5)
    expected = KNOWN_VECTOR[1]
    for g, e in zip(got, expected):
        assert abs(g - e) < 1e-9


def test_prng_next_int_range():
    prng = SeededPrng(3)
    for _ in range(50):
        v = prng.next_int(0, 10)
        assert 0 <= v <= 10


# -- AC6: harness stable/unstable ------------------------------------------------

def test_harness_stable_same_config():
    harness = DeterministicHarness(make_render(), width=8, height=8)
    result = harness.run(sample_timeline(), seed=42, num_frames=30)
    assert result.stable is True
    assert result.diff_frames == []
    assert result.outcome.state == VerificationState.PASS
    assert result.outcome.verdict == VerificationVerdict.PASS


def test_harness_unstable_with_timeline_effect():
    """Timeline thay đổi giữa 2 replay → pixel khác (input ảnh hưởng)."""
    harness = DeterministicHarness(make_render(), width=8, height=8)

    class _MutableTimeline(RenderTimeline):
        """Cho phép thêm event sau — mô phỏng input thay đổi giữa 2 lần."""

    t = _MutableTimeline()
    t.record("keydown", 100, {"key": "start"})
    # replay lần 1
    r1 = harness.run(t, seed=5, num_frames=30)  # 0.5s
    # thêm event rồi replay lần 2 (cùng harness — mô phỏng state đổi)
    t.record("pointer", 300, {"x": 1, "y": 2})
    r2 = harness.run(t, seed=5, num_frames=30)
    assert r1.stable is True
    assert r2.stable is True  # 2 lần replay trong cùng run vẫn ổn định
    # nhưng pixel giữa 2 run khác nhau (input đổi — event 300ms áp dụng)
    assert [f.pixel_hash for f in r1.frames_a] != [f.pixel_hash for f in r2.frames_a]


# -- AC7: BLOCKED khi render_fn raise ---------------------------------------------

def test_harness_render_raise_is_blocked():
    def bad_render(frame: RenderFrame) -> bytes:
        raise RuntimeError("renderer unavailable")

    harness = DeterministicHarness(bad_render, width=8, height=8)
    result = harness.run(sample_timeline(), seed=1, num_frames=5)
    assert result.stable is False
    assert result.outcome.state == VerificationState.BLOCKED
    assert result.outcome.verdict == VerificationVerdict.BLOCKED


def test_harness_wrong_buffer_size_is_blocked():
    def tiny_render(frame: RenderFrame) -> bytes:
        return b"x"  # thiếu bytes — không đúng W×H×3

    harness = DeterministicHarness(tiny_render, width=8, height=8)
    result = harness.run(sample_timeline(), seed=1, num_frames=5)
    assert result.outcome.state == VerificationState.BLOCKED
    assert "bytes" in result.outcome.evidence


# -- AC8: asset idempotency --------------------------------------------------------

def test_idempotency_classifier():
    from aios_core.rendering.idempotency import (
        AssetOpClass,
        AssetRetryDecision,
    )

    c = AssetIdempotencyClassifier(
        exactly_once={"sprite"}, at_least_once={"audio"},
    )
    assert c.classify("sprite") == AssetOpClass.EXACTLY_ONCE
    assert c.classify("audio") == AssetOpClass.AT_LEAST_ONCE
    assert c.decision("sprite") == AssetRetryDecision.RETRY
    assert c.decision("audio") == AssetRetryDecision.RETRY
    assert c.decision("tileset") == AssetRetryDecision.APPROVE  # fail-closed
    assert c.decision("tileset", has_failed=True) == AssetRetryDecision.COMPENSATE


def test_idempotency_fail_closed():
    from aios_core.rendering.idempotency import AssetOpClass

    c = AssetIdempotencyClassifier()
    assert c.classify("anything") == AssetOpClass.AT_MOST_ONCE  # fail-closed
    assert c.is_retryable("anything") is False
    c2 = AssetIdempotencyClassifier(exactly_once={"sprite"})
    assert c2.is_retryable("sprite") is True  # sau khi khai báo


# -- C3-02: arch allow-list ---------------------------------------------------------

def test_rendering_import_allowlist():
    """rendering/ chỉ import stdlib + verification + kernel.durability."""
    import inspect

    from aios_core import rendering
    from aios_core.rendering import harness as harness_mod

    src = inspect.getsource(rendering)
    assert "RenderReplay" in src
    # harness dùng Verification Kernel (INV-035)
    hsrc = inspect.getsource(harness_mod)
    assert "from ..verification" in hsrc
    # Không import agent/enterprise/... (isolated module)
    for forbidden in ("agents", "enterprise", "orchestrator", "autonomous"):
        assert f"from ..{forbidden}" not in hsrc
        assert f"from ..{forbidden}" not in src
