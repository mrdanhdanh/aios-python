"""Compatibility Matrix registry — M12-P0 C1 (TASK-084, Issue #7).

Registry tham chiếu (reference registry): khai báo khoảng AIOS version hỗ trợ
cho từng thành phần (plugin/contract/workflow/skill/sdk). Trong C1 chỉ CLI
``compat`` và test tiêu thụ; C2 (TASK-085) nối upgrade pipeline, C4 (TASK-087)
nối conformance (spec §3.5 — không wiring sớm).

Chính sách fail-closed (spec §3.3): kind/id lạ → error; version không parse
được → error; aios_version ngoài [aios_min, aios_max] → error; version component
≠ entry.version → warning (không chặn).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from ..plugins.compat import check_compatibility
from ..semver import parse_version

#: AIOS version hiện hành (M12). Literal cố định — KHÔNG import ``..__version__``
#: (review R2: relative import resolve về root ``aios_core`` → vi phạm
#: allow-list upgrade/ trong test_inv_upgrade_import_allowlist).
AIOS_VERSION = "1.1.0"

ComponentKind = Literal["plugin", "contract", "workflow", "skill", "sdk"]


class CompatibilityResult(BaseModel):
    """Outcome of a compatibility check (fail-closed: có errors → not compatible)."""

    compatible: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CompatibilityEntry(BaseModel):
    """Một dòng trong matrix: component + khoảng AIOS version được hỗ trợ."""

    kind: ComponentKind
    id: str  # không prefix loại (vd "demo", "agent") — spec C1-11
    version: str  # version component (semver)
    aios_min: str = "1.0.0"  # semver thuần — mốc AIOS tối thiểu
    aios_max: str | None = None  # constraint (hỗ trợ "1.1.x", "2.x"); None = không chặn

    @field_validator("version", "aios_min")
    @classmethod
    def _semver(cls, value: str) -> str:
        parse_version(value)  # raise ValueError nếu không hợp lệ
        return value


def _default_entries() -> tuple[CompatibilityEntry, ...]:
    """≥ 14 entry: 10 contract catalog + plugin + workflow + skill + sdk (spec C1-04)."""
    contracts = ("agent", "capability", "tool", "workflow", "runtime",
                 "event", "artifact", "plugin", "model", "memory")
    base = tuple(
        CompatibilityEntry(kind="contract", id=cid, version="1.1.0", aios_min="1.0.0")
        for cid in contracts
    )
    return base + (
        CompatibilityEntry(kind="plugin", id="demo", version="1.0.0", aios_min="1.0.0"),
        CompatibilityEntry(kind="workflow", id="demo_flow", version="1.0.0",
                           aios_min="1.0.0", aios_max="1.1.x"),
        CompatibilityEntry(kind="skill", id="agent-sprite-forge", version="1.0.0",
                           aios_min="1.0.0"),
        CompatibilityEntry(kind="sdk", id="python", version="1.0.0", aios_min="1.0.0"),
    )


class CompatibilityMatrix:
    """Registry tham chiếu các component + khoảng AIOS version hỗ trợ."""

    def __init__(self, entries: tuple[CompatibilityEntry, ...] | None = None) -> None:
        self._entries = entries if entries is not None else _default_entries()

    def list(self) -> list[dict]:
        return [
            {
                "kind": e.kind,
                "id": e.id,
                "version": e.version,
                "aios_min": e.aios_min,
                "aios_max": e.aios_max,
            }
            for e in self._entries
        ]

    def check(
        self,
        kind: str,
        component_id: str,
        version: str,
        aios_version: str = AIOS_VERSION,
    ) -> CompatibilityResult:
        """Fail-closed check của một component so với matrix."""
        normalized_kind = kind.strip().lower()
        normalized_id = component_id.strip().lower()

        if normalized_kind not in ("plugin", "contract", "workflow", "skill", "sdk"):
            return CompatibilityResult(
                compatible=False, errors=[f"unknown kind: {kind!r}"]
            )

        entry = next(
            (e for e in self._entries
             if e.kind == normalized_kind and e.id == normalized_id),
            None,
        )
        if entry is None:
            return CompatibilityResult(
                compatible=False,
                errors=[f"no matrix entry for {normalized_kind}/{normalized_id}"],
            )

        try:
            parse_version(version)
        except ValueError:
            return CompatibilityResult(
                compatible=False, errors=[f"invalid component version: {version!r}"]
            )

        warnings: list[str] = []
        if version != entry.version:
            warnings.append(
                f"version {version!r} differs from matrix entry version "
                f"{entry.version!r}"
            )

        try:
            ok = check_compatibility(entry.aios_min, entry.aios_max or "*", aios_version)
        except Exception as exc:  # noqa: BLE001 — parse fail → fail-closed
            return CompatibilityResult(
                compatible=False, errors=[f"aios version check failed: {exc}"]
            )

        errors: list[str] = []
        if not ok:
            errors.append(
                f"aios version {aios_version} outside supported range "
                f"[{entry.aios_min}, {entry.aios_max or '*'}] for "
                f"{normalized_kind}/{normalized_id}"
            )
        return CompatibilityResult(
            compatible=not errors, errors=errors, warnings=warnings
        )
