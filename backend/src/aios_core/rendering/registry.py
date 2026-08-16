"""AssetCapabilityRegistry (R4, kind=asset) — M11-P3 (TASK-081).

Register/discover/list/get capabilities asset — thread-safe, in-memory
(persist để P4/R5 SkillDistiller). Counters: asset_produce_count,
asset_failures.
"""

from __future__ import annotations

import threading
from typing import Any

from .asset import ASSET_KINDS, AssetCapability, AssetError, AssetOutput, AssetSpec
from .idempotency import AssetOpClass

#: Map capability name → asset kinds (fallback khi manifest không có `kinds`).
_CAPABILITY_KIND_MAP: dict[str, list[str]] = {
    "sprite-generation": ["sprite"],
    "map-generation": ["map"],
    "tileset-generation": ["tileset"],
    "audio-generation": ["audio"],
    "animation-generation": ["animation"],
    "sprite-sheet": ["sprite", "animation"],
    "ui-asset-generation": ["ui_asset"],
}


class AssetCapabilityRegistry:
    """Registry capability kind=asset (R4) — mirror M1 tư duy, tách riêng."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._capabilities: dict[str, AssetCapability] = {}
        self._counters: dict[str, int] = {
            "asset_produce_count": 0,
            "asset_failures": 0,
        }

    # -- registry ------------------------------------------------------------

    def register(self, capability: AssetCapability) -> None:
        with self._lock:
            self._capabilities[capability.id] = capability

    def get(self, capability_id: str) -> AssetCapability | None:
        with self._lock:
            return self._capabilities.get(capability_id)

    def discover(self, kind: str) -> list[AssetCapability]:
        """Tìm capability hỗ trợ kind — deterministic (sorted theo id)."""
        with self._lock:
            return sorted(
                (c for c in self._capabilities.values() if kind in c.kinds),
                key=lambda c: c.id,
            )

    def list(self) -> list[AssetCapability]:
        with self._lock:
            return sorted(self._capabilities.values(), key=lambda c: c.id)

    def count(self) -> int:
        with self._lock:
            return len(self._capabilities)

    # -- produce ---------------------------------------------------------------

    def produce(
        self,
        capability_id: str,
        spec: AssetSpec,
    ) -> AssetOutput:
        """Produce qua pipeline của capability — fail-closed:
        capability thiếu / pipeline lỗi → raise AssetError (caller → ERROR).
        """
        cap = self.get(capability_id)
        if cap is None:
            self._bump("asset_failures")
            from .asset import AssetError

            raise AssetError(f"capability không tồn tại: {capability_id}")
        try:
            output = cap.pipeline.produce(spec)
        except Exception as exc:  # noqa: BLE001 — fail-closed (INV-035)
            self._bump("asset_failures")
            from .asset import AssetError

            raise AssetError(f"produce failed ({capability_id}): {exc}") from exc
        self._bump("asset_produce_count")
        return output

    def snapshot_counters(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)

    def _bump(self, key: str) -> None:
        with self._lock:
            self._counters[key] += 1


# -- default capabilities (từ skills/ repo) --------------------------------------

def default_asset_capabilities(repo_root: str = "") -> list[AssetCapability]:
    """Khảo sát skills/ trên disk — register capability nếu manifest tồn tại.

    Không hard-fail khi skill thiếu (registry vẫn hoạt động với capabilities
    thủ công). Manifest: skills/<name>/manifest.json (source tương đối repo).
    """
    from pathlib import Path

    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[4]
    caps: list[AssetCapability] = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return caps
    for skill_dir in sorted(skills_dir.iterdir()):
        manifest = skill_dir / "manifest.json"
        if not manifest.is_file():
            continue
        try:
            import json

            data = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — manifest hỏng → bỏ qua
            continue
        kinds = [k for k in data.get("kinds", []) if k in ASSET_KINDS]
        if not kinds:
            # Fallback: map `capabilities` → kinds (vd sprite-generation → sprite)
            kinds = [
                k for cap in data.get("capabilities", [])
                for k in _CAPABILITY_KIND_MAP.get(cap, [])
            ]
        kinds = sorted(set(kinds))
        if not kinds:
            continue
        caps.append(AssetCapability(
            id=data.get("id", skill_dir.name),
            name=data.get("name", skill_dir.name),
            description=data.get("description", ""),
            kinds=kinds,
            pipeline=_SkillPipeline(skill_dir, data),
            version=str(data.get("version", "1.0")),
            source=f"skills/{skill_dir.name}/",
        ))
    return caps


class _SkillPipeline:
    """Pipeline giả — produce qua skill script nếu tồn tại, ngược lại sinh
    deterministic placeholder (sha256 từ spec canonical). Đủ cho P3 (wire
    thật qua SkillDistiller P4/R5)."""

    def __init__(self, skill_dir: Any, manifest: dict) -> None:
        self._skill_dir = skill_dir
        self._manifest = manifest
        kinds = [k for k in manifest.get("kinds", []) if k in ASSET_KINDS]
        if not kinds:
            kinds = [
                k for cap in manifest.get("capabilities", [])
                for k in _CAPABILITY_KIND_MAP.get(cap, [])
            ]
        self._kinds = sorted(set(kinds))

    def produce(self, spec: AssetSpec) -> AssetOutput:
        import hashlib
        import json
        from datetime import datetime, timezone

        if spec.kind not in self._kinds:
            from .asset import AssetError

            raise AssetError(f"skill không hỗ trợ kind={spec.kind}")
        canonical = json.dumps(
            spec.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return AssetOutput(
            spec=spec,
            artifact_ref=f"skill://{self._skill_dir.name}/{spec.kind}/{spec.name}",
            sha256=digest,
            size=len(canonical),
            produced_at=datetime.now(timezone.utc).isoformat(),
            idempotency=AssetOpClass.AT_LEAST_ONCE,
        )
