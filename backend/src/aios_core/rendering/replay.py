"""RenderReplay — record input timeline + seed → replay (M11-P1, TASK-079).

Cùng seed + cùng timeline + cùng render_fn → frames có pixel_hash giống hệt.
"""

from __future__ import annotations

import hashlib
from typing import Callable

from .contracts import RenderFrame, RenderFn
from .timeline import RenderTimeline


def pixel_hash(buffer: bytes) -> str:
    """SHA256 của raw pixel buffer (không nén)."""
    return hashlib.sha256(buffer).hexdigest()


class RenderReplay:
    """Replay deterministic: render_fn(frame) → bytes (W×H×3 RGB).

    freeze_policy:
      - "none"   : t = frame_index / fps (time thật theo timeline)
      - "fixed"  : t = timestamp của event cuối đã áp dụng (đóng băng theo state)
      - "paused" : t = 0 với mọi frame (đóng băng hoàn toàn)
    """

    def __init__(
        self,
        render_fn: RenderFn,
        *,
        width: int = 64,
        height: int = 64,
        fps: float = 60.0,
        freeze_policy: str = "none",
    ) -> None:
        if freeze_policy not in ("none", "fixed", "paused"):
            raise ValueError(f"freeze_policy không hợp lệ: {freeze_policy}")
        self.render_fn = render_fn
        self.width = width
        self.height = height
        self.fps = fps
        self.freeze_policy = freeze_policy

    def _frame_t(self, frame_index: int, timeline: RenderTimeline) -> float:
        """Tính t theo freeze_policy."""
        if self.freeze_policy == "paused":
            return 0.0
        t = frame_index / self.fps
        if self.freeze_policy == "fixed":
            # Đóng băng theo state: dùng timestamp event cuối <= t
            applied = [e for e in timeline.events
                       if e.timestamp <= t * 1000.0]
            if applied:
                return applied[-1].timestamp / 1000.0
            return t
        return t  # "none"

    def replay(
        self,
        timeline: RenderTimeline,
        seed: int,
        num_frames: int,
    ) -> list[RenderFrame]:
        """Chạy render_fn num_frames frame với seed cố định → list frame.

        Deterministic: cùng (timeline, seed, num_frames) → cùng pixel_hash.
        render_fn raise → exception lan ra (harness biến thành BLOCKED).
        """
        frames: list[RenderFrame] = []
        for i in range(num_frames):
            t = self._frame_t(i, timeline)
            state_hash = timeline.state_hash(i, self.fps)
            frames.append(self.render_frame(i, seed, t, state_hash))
        return frames

    def render_frame(
        self,
        frame_index: int,
        seed: int,
        t: float,
        state_hash: str,
    ) -> RenderFrame:
        """Render MỘT frame — pure function (state, time, seed)."""
        frame = RenderFrame(
            frame_index=frame_index,
            t=t,
            seed=seed,
            state_hash=state_hash,
        )
        buffer = self.render_fn(frame)
        expected = self.width * self.height * 3
        if len(buffer) != expected:
            raise ValueError(
                f"render_fn trả {len(buffer)} bytes, cần {expected} "
                f"(W×H×3 RGB raw buffer)"
            )
        frame = frame.model_copy(update={"pixel_hash": pixel_hash(buffer)})
        return frame
