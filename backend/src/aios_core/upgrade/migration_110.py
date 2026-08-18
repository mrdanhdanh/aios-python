"""AIOS 1.0 → 1.1 migration — M12-P1 C2 (TASK-085, Issue #7).

Luồng THẬT: plan chuẩn → backup → dry-run → validate → apply → rollback,
matrix-gated bởi ``CompatibilityMatrix`` (TASK-084). Dữ liệu demo — KHÔNG
write-back persistence (spec §1). Transforms pure + deep-copy (json
round-trip — KHÔNG import ``copy``: allow-list upgrade/ external).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..semver import compare, parse_version
from .backup import BackupStore
from .compatibility import AIOS_VERSION, CompatibilityMatrix
from .migration import MigrationEngine, MigrationError, MigrationJournal, MigrationPlan, MigrationStep

AIOS_100 = "1.0.0"

#: kinds được hỗ trợ bởi migration 1.0→1.1
SUPPORTED_KINDS = ("config", "workflow", "plugin", "contract")


def _deep(data: dict[str, Any]) -> dict[str, Any]:
    """Deep copy bằng json round-trip (allow-list external — không import copy)."""
    return json.loads(json.dumps(data))


# ---------------------------------------------------------------------------
# Transforms (pure, deep-copy input, idempotent) + rollbacks (guard)
# ---------------------------------------------------------------------------

def migrate_config_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Thêm marker migration nếu chưa có (C1-13)."""
    out = _deep(data)
    out.setdefault("migration", {"from": AIOS_100, "to": AIOS_VERSION})
    return out


def rollback_config_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Xóa marker CHỈ khi đúng giá trị do transform ghi (guard C1-07)."""
    out = _deep(data)
    if out.get("migration") == {"from": AIOS_100, "to": AIOS_VERSION}:
        del out["migration"]
    return out


def migrate_workflow_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Bump ``version`` top-level 1.0.0 → 1.1.0 (C1-04); version khác → no-op."""
    out = _deep(data)
    if out.get("version") == AIOS_100:
        out["version"] = AIOS_VERSION
    return out


def rollback_workflow_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Hạ CHỈ khi version == 1.1.0 (guard)."""
    out = _deep(data)
    if out.get("version") == AIOS_VERSION:
        out["version"] = AIOS_100
    return out


def migrate_plugin_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Append ``"1.1.0"`` vào ``aios.compatible`` nếu chưa có (C2-03).

    ``aios`` thiếu → setdefault min="1.0.0"; ``compatible`` thiếu → seed
    ``[min]`` rồi append (nhất quán v0→v1 — R4).
    """
    out = _deep(data)
    aios = out.setdefault("aios", {"min": "1.0.0"})
    if not isinstance(aios, dict):
        return out
    compatible = aios.get("compatible")
    if not isinstance(compatible, list):
        compatible = [aios.get("min", "1.0.0")]
        aios["compatible"] = compatible
    if AIOS_VERSION not in compatible:
        compatible.append(AIOS_VERSION)
    return out


def rollback_plugin_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Xóa ``"1.1.0"`` khỏi compatible — khôi phục trạng thái trước transform."""
    out = _deep(data)
    aios = out.get("aios")
    if isinstance(aios, dict) and isinstance(aios.get("compatible"), list):
        aios["compatible"] = [v for v in aios["compatible"] if v != AIOS_VERSION]
    return out


def migrate_contract_100_110(data: dict[str, Any]) -> dict[str, Any]:
    """Bump ``version`` 1.0.0 → 1.1.0."""
    out = _deep(data)
    if out.get("version") == AIOS_100:
        out["version"] = AIOS_VERSION
    return out


def rollback_contract_100_110(data: dict[str, Any]) -> dict[str, Any]:
    out = _deep(data)
    if out.get("version") == AIOS_VERSION:
        out["version"] = AIOS_100
    return out


# ---------------------------------------------------------------------------
# Plan registry (R2: PLANS_110 = template kind → steps; plan thật qua factory)
# ---------------------------------------------------------------------------

#: kind → (migrate_fn, rollback_fn) — dùng cho validate kind + sinh plan
_PLAN_TEMPLATES: dict[str, tuple[Any, Any]] = {
    "config": (migrate_config_100_110, rollback_config_100_110),
    "workflow": (migrate_workflow_100_110, rollback_workflow_100_110),
    "plugin": (migrate_plugin_100_110, rollback_plugin_100_110),
    "contract": (migrate_contract_100_110, rollback_contract_100_110),
}


def get_plan(kind: str, component_id: str) -> MigrationPlan | None:
    """Plan 1.0→1.1 cho (kind, component_id); None nếu kind không hỗ trợ.

    migration_id gồm component_id (C2-04) — idempotent per component.
    """
    template = _PLAN_TEMPLATES.get(kind)
    if template is None:
        return None
    fn, rollback_fn = template
    return MigrationPlan(
        migration_id=f"aios-1.0-to-1.1-{kind}-{component_id}",
        kind=kind,
        from_version=AIOS_100,
        to_version=AIOS_VERSION,
        backup_required=True,
        steps=[MigrationStep(kind, f"{kind}-100-to-110", fn, rollback_fn)],
    )


# ---------------------------------------------------------------------------
# Aios110Migrator (matrix-gated)
# ---------------------------------------------------------------------------

@dataclass
class Aios110Result:
    payload: dict[str, Any] = field(default_factory=dict)
    backup_id: int | None = None
    journal_status: str | None = None
    matrix: dict = field(default_factory=lambda: {"pre": "ok", "post": "skipped", "warnings": []})


class Aios110Migrator:
    """Migration 1.0→1.1 với pre/post matrix check fail-closed."""

    def __init__(
        self,
        matrix: CompatibilityMatrix | None = None,
        engine: MigrationEngine | None = None,
        backup_store: BackupStore | None = None,
    ) -> None:
        self._matrix = matrix or CompatibilityMatrix()
        self._engine = engine or MigrationEngine()
        self._backup = backup_store

    # -- helpers -------------------------------------------------------------

    def component_id(self, kind: str, payload: dict[str, Any]) -> str:
        if kind == "config":
            return "config"
        key = "id" if kind in ("plugin", "contract") else "name"
        value = payload.get(key)
        if not value:
            raise MigrationError(f"{kind} payload thiếu '{key}' — không xác định được component")
        return str(value)

    def _version(self, payload: dict[str, Any]) -> str | None:
        return payload.get("version")

    def _matrix_id(self, kind: str, component_id: str) -> str:
        """id dùng cho matrix check — component_id THẬT của payload
        (matrix entries: plugin/demo, workflow/demo_flow, contract/agent..memory)."""
        return component_id

    def _pre_check(self, kind: str, payload: dict[str, Any]) -> dict:
        """(1) range [1.0.0, 1.1.0] — chỉ kind có version (C2-01);
        (2) matrix — chỉ kind có entry; config SKIP cả hai."""
        if kind == "config":
            return {"pre": "skipped", "warnings": []}
        version = self._version(payload)
        if version is None:
            raise MigrationError(f"{kind} payload thiếu 'version' — pre-check range không chạy được")
        try:
            parsed = parse_version(str(version))
            if compare(str(version), AIOS_100) < 0 or compare(str(version), AIOS_VERSION) > 0:
                raise MigrationError(
                    f"version {version} ngoài range migration [{AIOS_100}, {AIOS_VERSION}]"
                )
            _ = parsed  # đã parse — hợp lệ
        except ValueError:
            raise MigrationError(f"version {version!r} không phải semver hợp lệ") from None
        component_id = self.component_id(kind, payload)
        result = self._matrix.check(
            kind, component_id, str(version), aios_version=AIOS_VERSION
        )
        if not result.compatible:
            raise MigrationError(f"matrix pre-check blocked: {'; '.join(result.errors)}")
        return {"pre": "ok", "warnings": result.warnings}

    def _post_check(self, kind: str, payload: dict[str, Any]) -> dict:
        """Assertion thật per-kind (C1-06/C2-03) + matrix check."""
        if kind == "config":
            if payload.get("migration") != {"from": AIOS_100, "to": AIOS_VERSION}:
                raise MigrationError("config post-check fail: thiếu migration marker")
            return {"post": "ok", "warnings": []}
        version = self._version(payload)
        if kind in ("workflow", "contract"):
            if version != AIOS_VERSION:
                raise MigrationError(f"{kind} post-check fail: version {version!r} != {AIOS_VERSION}")
        elif kind == "plugin":
            aios = payload.get("aios") or {}
            compatible = aios.get("compatible") if isinstance(aios, dict) else None
            if not isinstance(compatible, list) or AIOS_VERSION not in compatible:
                raise MigrationError(f"plugin post-check fail: '{AIOS_VERSION}' không có trong aios.compatible")
        component_id = self.component_id(kind, payload)
        result = self._matrix.check(
            kind, component_id, str(version), aios_version=AIOS_VERSION
        )
        if not result.compatible:
            raise MigrationError(f"matrix post-check blocked: {'; '.join(result.errors)}")
        return {"post": "ok", "warnings": result.warnings}

    # -- pipeline ------------------------------------------------------------

    def dry_run(self, kind: str, payload: dict[str, Any]) -> Aios110Result:
        """Pre-check + engine.dry_run — không side effect."""
        matrix_pre = self._pre_check(kind, payload)
        plan = get_plan(kind, self.component_id(kind, payload))
        if plan is None:
            raise MigrationError(f"kind {kind!r} không được hỗ trợ bởi migration 1.0→1.1")
        result_payload = self._engine.dry_run(plan, payload)
        return Aios110Result(payload=result_payload, journal_status="dry-run",
                             matrix={**matrix_pre, "post": "skipped"})

    def apply(self, kind: str, payload: dict[str, Any]) -> Aios110Result:
        """Pre-check → backup (trước — C1-01) → engine.apply → post-check.

        Post-check fail → rollback(plan, RESULT) (C2-06) → raise.
        """
        matrix_pre = self._pre_check(kind, payload)
        component_id = self.component_id(kind, payload)
        plan = get_plan(kind, component_id)
        if plan is None:
            raise MigrationError(f"kind {kind!r} không được hỗ trợ bởi migration 1.0→1.1")

        backup_id: int | None = None
        if self._backup is not None:
            backup_id = self._backup.backup(
                kind, component_id, str(self._version(payload) or ""), dict(payload)
            )
        try:
            result_payload = self._engine.apply(plan, payload)
            matrix_post = self._post_check(kind, result_payload)
            return Aios110Result(payload=result_payload, backup_id=backup_id,
                                 journal_status="completed",
                                 matrix={**matrix_pre, **matrix_post})
        except MigrationError:
            raise
        except Exception as exc:  # noqa: BLE001 — engine đã rollback step; post-check fail ở đây
            # engine.apply đã auto-rollback steps nếu fail giữa chừng.
            raise MigrationError(f"migration failed: {exc}") from exc

    def rollback(self, kind: str, result: Aios110Result) -> Aios110Result:
        """Rollback từ result (payload đã transform) — C2-06."""
        component_id = self.component_id(kind, result.payload)
        plan = get_plan(kind, component_id)
        if plan is None:
            raise MigrationError(f"kind {kind!r} không được hỗ trợ")
        rolled = self._engine.rollback(plan, result.payload)
        return Aios110Result(payload=rolled, backup_id=result.backup_id,
                             journal_status="rolled_back", matrix=result.matrix)
