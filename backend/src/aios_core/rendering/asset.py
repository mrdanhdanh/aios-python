"""AssetPipeline contract (R9) — M11-P3 (TASK-081).

AssetSpec → AssetPipeline.produce() → AssetOutput.
Fail-closed: pipeline không hỗ trợ kind → AssetError (caller → ERROR, không PASS);
idempotency mặc định at-most-once (AssetIdempotencyClassifier — P1).
"""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, field_validator

from .idempotency import AssetOpClass

ASSET_KINDS = ("sprite", "tileset", "map", "audio", "animation", "ui_asset")


class AssetError(RuntimeError):
    """Pipeline không produce được (kind không hỗ trợ / lỗi generate)."""


class AssetSpec(BaseModel):
    """Yêu cầu asset — deterministic (seed) + golden hash optional."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    name: str
    params: dict[str, Any] = {}
    seed: int = 0  # determinism-first: đổi seed/params → output khác
    expected_hash: str = ""  # golden — verify output khớp

    @field_validator("kind")
    @classmethod
    def _kind_valid(cls, value: str) -> str:
        if value not in ASSET_KINDS:
            raise ValueError(
                f"kind không hợp lệ: {value!r} (chấp nhận: {ASSET_KINDS})"
            )
        return value


class AssetOutput(BaseModel):
    """Kết quả produce — đủ để verify + trace."""

    model_config = ConfigDict(extra="forbid")

    spec: AssetSpec
    artifact_ref: str
    sha256: str
    size: int
    produced_at: str
    idempotency: AssetOpClass


class AssetPipeline(Protocol):
    """Pipeline sinh asset — deterministic theo spec.

    produce(spec) -> AssetOutput; raise AssetError khi không produce được.
    """

    def produce(self, spec: AssetSpec) -> AssetOutput: ...


class AssetCapability(BaseModel):
    """Capability manifest (R4) — pipeline duck-typed (không serialize)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    kinds: list[str]
    pipeline: Any  # AssetPipeline — duck-typed (không serialize)
    version: str = "1.0"
    source: str = ""  # path tương đối repo (vd skills/agent-sprite-forge/)

    def model_dump_manifest(self) -> dict[str, Any]:
        """Dump không pipeline (cho CLI/registry list)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "kinds": self.kinds,
            "version": self.version,
            "source": self.source,
        }
