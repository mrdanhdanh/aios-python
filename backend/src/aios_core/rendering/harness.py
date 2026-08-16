"""DeterministicHarness — M11-P1 (TASK-079).

Chạy render_fn 2 lần (cùng seed + timeline) → so sánh pixel_hash →
RenderReplayResult (stable, diff_frames, outcome INV-035).

Không chạy được (render_fn raise) → outcome BLOCKED (fail-closed).
"""

from __future__ import annotations

from ..verification.contracts import VerificationOutcome
from ..verification.state import (
    VerificationState,
    VerificationVerdict,
)
from .contracts import RenderFn, RenderReplayResult
from .replay import RenderReplay
from .timeline import RenderTimeline


class DeterministicHarness:
    """Pixel-stable verification cho render deterministic."""

    def __init__(
        self,
        render_fn: RenderFn,
        *,
        width: int = 64,
        height: int = 64,
        fps: float = 60.0,
        freeze_policy: str = "none",
    ) -> None:
        self._replay = RenderReplay(
            render_fn,
            width=width,
            height=height,
            fps=fps,
            freeze_policy=freeze_policy,
        )

    def run(
        self,
        timeline: RenderTimeline,
        *,
        seed: int = 42,
        num_frames: int = 60,
    ) -> RenderReplayResult:
        """Replay 2 lần cùng seed → so sánh pixel-stable.

        - render_fn raise → outcome BLOCKED (fail-closed, INV-035)
        - frames khác nhau → stable=False + diff_frames + outcome FAIL
        - giống hệt → stable=True + outcome PASS
        """
        try:
            frames_a = self._replay.replay(timeline, seed, num_frames)
            frames_b = self._replay.replay(timeline, seed, num_frames)
        except Exception as exc:  # noqa: BLE001 — INV-035: không chạy → BLOCKED
            return RenderReplayResult(
                stable=False,
                outcome=VerificationOutcome(
                    mechanism_id="render-replay",
                    state=VerificationState.BLOCKED,
                    verdict=VerificationVerdict.BLOCKED,
                    evidence=f"replay failed: {exc}",
                ),
            )

        diff = [
            i for i, (a, b) in enumerate(zip(frames_a, frames_b))
            if a.pixel_hash != b.pixel_hash
        ]
        stable = not diff
        if stable:
            outcome = VerificationOutcome(
                mechanism_id="render-replay",
                state=VerificationState.PASS,
                verdict=VerificationVerdict.PASS,
                evidence=(
                    f"pixel-stable: {num_frames} frames, seed={seed}, "
                    f"policy={self._replay.freeze_policy}"
                ),
            )
        else:
            outcome = VerificationOutcome(
                mechanism_id="render-replay",
                state=VerificationState.FAIL,
                verdict=VerificationVerdict.FAIL,
                evidence=(f"pixel diff tại {len(diff)} frames: {diff[:10]}"),
            )
        return RenderReplayResult(
            frames_a=frames_a,
            frames_b=frames_b,
            stable=stable,
            diff_frames=diff,
            outcome=outcome,
        )
