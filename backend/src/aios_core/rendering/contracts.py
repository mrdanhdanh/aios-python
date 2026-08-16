"""Rendering contracts — M11-P1 (TASK-079).

RenderFn contract (C1-01): bytes = raw pixel buffer W×H×3 RGB (không nén);
pixel_hash = SHA256(buffer). render_fn KHÔNG được đọc ngoài frame (pure).
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from ..verification.contracts import VerificationOutcome


class InputEvent(BaseModel):
    """Một sự kiện input trong timeline (record order + timestamp)."""

    model_config = ConfigDict(extra="forbid")

    type: str  # "keydown" | "pointer" | "custom" ...
    timestamp: float  # ms — tăng dần trong timeline
    payload: dict[str, Any] = {}


class RenderFrame(BaseModel):
    """Frame để render_fn tính ảnh — pure function input.

    frame_index: thứ tự frame 0-based
    t: thời gian frame (theo freeze_policy)
    seed: seed cố định của replay
    state_hash: hash trạng thái (từ timeline events đã áp dụng tới frame này)
    """

    model_config = ConfigDict(extra="forbid")

    frame_index: int
    t: float
    seed: int
    state_hash: str = ""
    pixel_hash: str = ""  # SHA256 của raw pixel buffer (render_fn tính xong)


RenderFn = Callable[[RenderFrame], bytes]


class RenderReplayResult(BaseModel):
    """Kết quả 2 lần replay — stable/diff + outcome fail-closed (INV-035).

    Harness KHÔNG raise khi unstable — caller quyết định qua `outcome`.
    """

    model_config = ConfigDict(extra="forbid")

    frames_a: list[RenderFrame] = []
    frames_b: list[RenderFrame] = []
    stable: bool = False
    diff_frames: list[int] = []  # chỉ số frame có pixel_hash khác
    outcome: VerificationOutcome
