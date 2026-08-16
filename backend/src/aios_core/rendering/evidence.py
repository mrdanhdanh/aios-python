"""VisualEvidence — M11-P2 (R1, TASK-080).

7 trường evidence (proposal §R1): Screenshot · DOM Snapshot · Render State ·
Input Timeline · Browser/OS metadata · Seed · Pixel Diff.
pixel_diff chỉ là 1 trường — metric sau evidence (không SLO sớm).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from .contracts import InputEvent
from .ui_state import UIState

#: PNG 1×1 trong suốt (base64) — dùng cho test/CLI mock.
PNG_1PX_BASE64 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


class VisualEvidence(BaseModel):
    """Một mẫu bằng chứng visual — đủ để replay + reason (R1 + R10)."""

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    # Screenshot — base64 data URI (self-contained, CI-safe)
    screenshot: str
    # DOM Snapshot — {"tag", "text", "attrs", "children"} recursive
    dom_snapshot: dict[str, Any] = {}
    # Render State — BẮT BUỘC (R10 là nền R1)
    render_state: UIState
    # Input Timeline — dùng InputEvent (P1, không duplicate contract)
    input_timeline: list[InputEvent] = []
    # Browser/OS metadata — chẩn đoán diff do GPU/font/DSF
    browser_meta: dict[str, Any] = {}
    # Seed — replay deterministic (P1)
    seed: int = 0
    # Pixel Diff — -1 = thiếu ref, 0 = giống, >0 = % pixel khác (so ref vs current)
    pixel_diff: float = -1.0

    def has_screenshot(self) -> bool:
        return bool(self.screenshot) and self.screenshot.startswith("data:image/")
