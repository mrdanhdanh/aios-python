"""Contract 1.0 Catalog — M10-F2 (TASK-064).

Freeze 10 public contracts. Mỗi contract có: name · version · schema ·
compatibility · lifecycle · deprecation · migration. Data-driven — catalog
phản ánh code thật (schema_ref import được, xác minh bằng test).
"""

from __future__ import annotations

import importlib
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..semver import SEMVER_RE

#: 10 public contracts frozen at AIOS 1.0 (PLAN §M10-7).
CONTRACT_IDS = (
    "agent",
    "capability",
    "tool",
    "workflow",
    "runtime",
    "event",
    "artifact",
    "plugin",
    "model",
    "memory",
)


class ContractLifecycle(str, Enum):
    STABLE = "stable"          # backward-compatible thay đổi được phép
    FROZEN = "frozen"          # chỉ bug fix/security (không đổi hành vi)
    DEPRECATED = "deprecated"  # vẫn hoạt động, khuyến cáo di chuyển
    REMOVED = "removed"        # không còn hỗ trợ


class ContractDefinition(BaseModel):
    """Định nghĩa một public contract trong catalog 1.0."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str  # version freeze tại 1.0 (semver)
    schema_ref: tuple[str, str]  # (module_path, class_name) — import được thật
    compatibility: str = "semver: patch=bugfix, minor=backward-compatible, major=breaking"
    lifecycle: ContractLifecycle = ContractLifecycle.STABLE
    deprecated_in: str | None = None  # version bắt đầu deprecate (semver)
    deprecated_reason: str | None = None
    migration_path: str | None = None  # bắt buộc khi DEPRECATED
    notes: str | None = None

    @field_validator("version", "deprecated_in")
    @classmethod
    def _semver(cls, value: str | None) -> str | None:
        if value is not None and not SEMVER_RE.match(value):
            raise ValueError(f"Invalid semver: {value!r}")
        return value

    @field_validator("id")
    @classmethod
    def _id_lower(cls, value: str) -> str:
        if not value.islower() or " " in value:
            raise ValueError(f"Contract id phải lowercase, không space: {value!r}")
        return value

    @model_validator(mode="after")
    def _deprecated_requires_fields(self) -> "ContractDefinition":
        """DEPRECATED bắt buộc: deprecated_in + deprecated_reason + migration_path."""
        if self.lifecycle == ContractLifecycle.DEPRECATED:
            for field in ("deprecated_in", "deprecated_reason", "migration_path"):
                if not getattr(self, field):
                    raise ValueError(
                        f"Contract DEPRECATED phải khai báo {field}"
                    )
        return self

    def schema_exists(self) -> bool:
        """Xác minh schema_ref import được thật (fail-closed)."""
        try:
            module = importlib.import_module(self.schema_ref[0])
            return hasattr(module, self.schema_ref[1])
        except ImportError:
            return False


# ---------------------------------------------------------------------------
# Catalog 1.1 — khớp code thật (backend/src/aios_core/).
# version = baseline freeze 1.1.0 (M12 Issue #7 — minor bump từ 1.0.0, backward-compatible).
# deprecated_in của plugin GIỮ 1.0.0 (R3 review — test_cli_contract_check_full_has_warnings phụ thuộc plugin còn deprecated).
# ---------------------------------------------------------------------------

CONTRACTS: tuple[ContractDefinition, ...] = (
    ContractDefinition(
        id="agent",
        name="Agent Contract",
        version="1.1.0",
        schema_ref=("aios_core.agents.base", "Assistant"),
        lifecycle=ContractLifecycle.STABLE,
        notes="Agent interface (Worker Plane) — INV-001/002; Agent Contract mở rộng M8 "
              "(accepts/produces/capabilities/permissions) cho ecosystem.",
    ),
    ContractDefinition(
        id="capability",
        name="Capability Contract",
        version="1.1.0",
        schema_ref=("aios_core.capabilities.registry", "Capability"),
        lifecycle=ContractLifecycle.STABLE,
        notes="Capability registry — agent chỉ chọn capability, không chọn tool (INV-002).",
    ),
    ContractDefinition(
        id="tool",
        name="Tool Contract",
        version="1.1.0",
        schema_ref=("aios_core.tools.base", "Tool"),
        lifecycle=ContractLifecycle.STABLE,
        notes="Tool ABC template run 1-6, gate fail-closed, 6 loại tool (M2).",
    ),
    ContractDefinition(
        id="workflow",
        name="Workflow Contract",
        version="1.1.0",
        schema_ref=("aios_core.workflow.definition", "WorkflowDefinition"),
        lifecycle=ContractLifecycle.STABLE,
        notes="Workflow Definition declarative, engine-agnostic (INV-003).",
    ),
    ContractDefinition(
        id="runtime",
        name="Runtime Contract",
        version="1.1.0",
        schema_ref=("aios_core.kernel.runtime_kernel", "RuntimeKernel"),
        lifecycle=ContractLifecycle.FROZEN,
        notes="Runtime = 9 services + DI container + start/stop; FROZEN tại 1.0 "
              "(chỉ bug/security fix).",
    ),
    ContractDefinition(
        id="event",
        name="Event Contract",
        version="1.1.0",
        schema_ref=("aios_core.kernel.events", "EventType"),
        lifecycle=ContractLifecycle.STABLE,
        notes="EventType bus — thêm event mới được phép (minor), đổi tên/giá trị = breaking.",
    ),
    ContractDefinition(
        id="artifact",
        name="Artifact Contract",
        version="1.1.0",
        schema_ref=("aios_core.contracts.artifact", "ArtifactContract"),
        lifecycle=ContractLifecycle.FROZEN,
        notes="Artifact = ContractMetadata + checksum + sidecar (INV-008).",
    ),
    ContractDefinition(
        id="plugin",
        name="Plugin Contract",
        version="1.1.0",
        schema_ref=("aios_core.plugins.contracts", "PluginManifest"),
        lifecycle=ContractLifecycle.DEPRECATED,
        deprecated_in="1.0.0",
        deprecated_reason="PluginManifest v1 được thay thế bằng Ecosystem Entry "
                          "(ecosystem/contracts.py) — manifest v1 vẫn hoạt động, "
                          "khuyến cáo di chuyển khi nâng cấp 1.x.",
        migration_path="plugin v2 → Ecosystem Entry (ecosystem registry) — "
                       "TASK-074 Migration 1.0",
        notes="Plugin lifecycle 10-state tái dùng SkillState (M8) — không tạo "
              "state machine thứ hai.",
    ),
    ContractDefinition(
        id="model",
        name="Model Contract",
        version="1.1.0",
        schema_ref=("aios_core.models.base", "ModelContract"),
        lifecycle=ContractLifecycle.STABLE,
        notes="ModelContract ABC + providers (Mock/OpenAI/Ollama) — model "
              "independence (AIOS không thành OpenAI wrapper).",
    ),
    ContractDefinition(
        id="memory",
        name="Memory Contract",
        version="1.1.0",
        schema_ref=("aios_core.memory.contracts", "MemoryContext"),
        lifecycle=ContractLifecycle.STABLE,
        notes="MemoryQuery/Candidate/Score/Selection/Context + MemoryBudget — "
              "Agent không truy cập memory trực tiếp (INV-011).",
    ),
)


class ContractCatalog:
    """Registry 10 public contracts (data-driven, không cần DI)."""

    def __init__(self, contracts: tuple[ContractDefinition, ...] = CONTRACTS) -> None:
        self._contracts: dict[str, ContractDefinition] = {c.id: c for c in contracts}

    def get(self, contract_id: str) -> ContractDefinition:
        return self._contracts[contract_id]

    def all(self) -> list[ContractDefinition]:
        return list(self._contracts.values())

    def ids(self) -> list[str]:
        return list(self._contracts)

    def __contains__(self, contract_id: str) -> bool:
        return contract_id in self._contracts

    def verify_schema_refs(self) -> list[str]:
        """Trả danh sách id có schema_ref KHÔNG import được (rỗng = OK)."""
        return [c.id for c in self._contracts.values() if not c.schema_exists()]
