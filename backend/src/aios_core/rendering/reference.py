"""Reference-Asset Understanding — R12 (M11-P3d, TASK-082).

Ingest reference image → structured description (scene/object/style/palette)
→ feed AssetPipeline (AssetSpec params). Vision model injectable — default
MockVisionAnalyzer (deterministic, seed từ sha256(file), offline).
Fail-closed (INV-035): ảnh không tồn tại/không đọc được → AssetError.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, field_validator

from .asset import AssetError


class ReferenceDescription(BaseModel):
    """Structured description của reference image (R12)."""

    model_config = ConfigDict(extra="forbid")

    scene: str
    objects: list[str] = []
    style: str = ""
    palette: list[str] = []  # hex lowercase (#rrggbb)
    raw_text: str = ""

    @field_validator("objects")
    @classmethod
    def _dedup_sort(cls, value: list[str]) -> list[str]:
        return sorted(dict.fromkeys(v.strip() for v in value if v.strip()))

    @field_validator("palette")
    @classmethod
    def _normalize_palette(cls, value: list[str]) -> list[str]:
        out: list[str] = []
        for color in value:
            color = color.strip().lower()
            if not color.startswith("#"):
                color = f"#{color}"
            if color not in out:
                out.append(color)
        return out


class VisionAnalyzer(Protocol):
    """Vision model injectable — phân tích ảnh → mô tả cấu trúc."""

    def analyze(self, image_path: str) -> ReferenceDescription: ...


class MockVisionAnalyzer:
    """Deterministic mock — seed từ sha256(file) (C2-05).

    Cùng ảnh → cùng description; khác ảnh → khác (đủ để test + offline).
    """

    def analyze(self, image_path: str) -> ReferenceDescription:
        digest = hashlib.sha256(Path(image_path).read_bytes()).hexdigest()
        seed = int(digest[:8], 16)
        palette = [
            "#" + digest[i : i + 6]
            for i in (8, 16, 24)
        ]
        return ReferenceDescription(
            scene=f"scene-{seed % 97}",
            objects=[f"object-{seed % 13}", f"object-{(seed // 7) % 11}"],
            style=f"style-{seed % 5}",
            palette=palette,
            raw_text=f"mock vision digest={digest[:16]}",
        )


class ReferenceAssetUnderstanding:
    """R12 — ingest reference image → description → AssetSpec params."""

    def __init__(self, analyzer: VisionAnalyzer | None = None) -> None:
        self._analyzer = analyzer or MockVisionAnalyzer()

    def ingest(self, image_path: str) -> ReferenceDescription:
        """Phân tích ảnh reference — fail-closed nếu không đọc được (INV-035)."""
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            raise AssetError(f"reference image not found: {image_path}")
        try:
            return self._analyzer.analyze(str(path))
        except AssetError:
            raise
        except Exception as exc:  # noqa: BLE001 — fail-closed
            raise AssetError(f"cannot analyze reference image: {exc}") from exc

    def to_asset_params(
        self,
        image_path: str,
        existing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Merge description vào params an toàn — không ghi đè params có sẵn."""
        desc = self.ingest(image_path)
        merged = dict(existing or {})
        merged["reference"] = desc.model_dump()
        return merged
