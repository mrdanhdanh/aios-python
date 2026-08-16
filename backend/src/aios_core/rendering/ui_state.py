"""UIState contract — M11-P2b (R10, TASK-080).

`UI State → Render → Screenshot` — chuẩn hóa state có thể reason:
AIOS debug UI bằng reasoning (state diff), không chỉ pixel compare.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


def canonical_json(obj: Any) -> str:
    """Canonical JSON — sort_keys + separators chặt (deterministic cross-version)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class UIState(BaseModel):
    """Render state chuẩn hóa (R10) — ví dụ từ proposal:

    {"screen": "game", "player": {"x": 160, "y": 90, "scale": 3},
     "input": {"left": false, "right": true}}
    """

    model_config = ConfigDict(extra="forbid")

    version: str = "1.0"
    screen: str  # "title" | "game" | "gameover" ...
    entities: dict[str, dict[str, Any]] = {}  # player/x/y/scale...
    input: dict[str, Any] = {}  # input state
    t: float = 0.0
    seed: int = 0

    @field_validator("entities", "input")
    @classmethod
    def _must_be_dict(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            raise ValueError("entities/input phải là dict")
        return value

    def canonical(self) -> str:
        """Canonical JSON — nguồn cho state_hash (deterministic)."""
        return canonical_json(self.model_dump(mode="json"))

    def state_hash(self) -> str:
        """SHA256(canonical) — cùng state → cùng hash."""
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()

    def diff(self, other: "UIState") -> list[dict[str, Any]]:
        """So sánh reasoning — trả list {"path", "before", "after"}."""
        diffs: list[dict[str, Any]] = []
        a = self.model_dump(mode="json")
        b = other.model_dump(mode="json")

        def walk(pa: dict, pb: dict, path: str = "") -> None:
            for key in sorted(set(pa) | set(pb)):
                p = f"{path}.{key}" if path else key
                va, vb = pa.get(key), pb.get(key)
                if va == vb:
                    continue
                if isinstance(va, dict) and isinstance(vb, dict):
                    walk(va, vb, p)
                else:
                    diffs.append({"path": p, "before": va, "after": vb})

        walk(a, b)
        return diffs
