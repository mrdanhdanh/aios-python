"""Upgrade pipeline (TASK-020) — Compatibility → Dependencies → Backup → Migration → Health Check → Rollback.

Deterministic (INV-010), event-driven (INV-009), only the ROOT component is
migrated — dependencies are resolved/validated, never mutated (C2-03).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..contracts.compatibility import CompatibilityChecker
from ..semver import compare
from .backup import BackupStore
from .dependency import ComponentSpec, Dependency, DependencyResolver, Resolution
from .migrator import Migrator

# type_str = EventType member NAME (e.g. "UPGRADE_STARTED") — wiring maps it.
Emit = Callable[[str, dict[str, Any]], None]

# validate(kind, component_id, new_version) -> None | str (None = healthy)
Validate = Callable[[str, str, str], str | None]


@dataclass(frozen=True)
class UpgradeResult:
    status: str                     # ok | skipped | failed
    step: str | None                # compatibility | dependencies | backup | migrate | health
    backup_id: int | None
    reason: str | None
    plan: tuple[ComponentSpec, ...]  # topo order (resolution.ordered)


class UpgradePipeline:
    """Six-step upgrade with safe rollback."""

    def __init__(
        self,
        migrator: Migrator,
        backup_store: BackupStore,
        resolver: DependencyResolver,
        checker: type[CompatibilityChecker] = CompatibilityChecker,
        validate: Validate | None = None,
        emit: Emit | None = None,
    ) -> None:
        self._migrator = migrator
        self._backup = backup_store
        self._resolver = resolver
        self._checker = checker
        self._validate = validate
        self._emit = emit

    def _fire(self, type_str: str, payload: dict[str, Any]) -> None:
        if self._emit:
            self._emit(type_str, payload)

    def run(
        self,
        kind: str,
        component_id: str,
        new_version: str,
        dry_run: bool = False,
    ) -> UpgradeResult:
        self._fire(
            "UPGRADE_STARTED",
            {"kind": kind, "component_id": component_id, "version": new_version, "step": "start"},
        )

        # -- 0.1 read current (once, reused) ------------------------------------
        current = self._migrator.read_current(kind, component_id)
        if current is None or not current.get("version"):
            reason = f"component not found: {component_id}"
            return UpgradeResult(status="failed", step="compatibility", backup_id=None, reason=reason, plan=())

        current_version = str(current["version"])

        # -- 0.5 skip check -----------------------------------------------------
        if compare(new_version, current_version) <= 0:
            self._fire(
                "UPGRADE_SKIPPED",
                {"kind": kind, "component_id": component_id, "version": new_version,
                 "step": "skip", "current_version": current_version},
            )
            return UpgradeResult(status="skipped", step=None, backup_id=None,
                                 reason=f"{current_version} -> {new_version} is not an upgrade", plan=())

        # -- 1 compatibility ----------------------------------------------------
        result = self._checker.check_upgrade(current_version, new_version)
        if not result.compatible:
            return UpgradeResult(status="failed", step="compatibility", backup_id=None,
                                 reason=result.reason, plan=())
        self._fire(
            "UPGRADE_COMPATIBILITY_OK",
            {"kind": kind, "component_id": component_id, "version": new_version,
             "step": "compatibility", "from_version": current_version},
        )

        # -- 2 dependencies -----------------------------------------------------
        root_spec = self._root_spec(kind, component_id, current_version)
        resolution: Resolution = self._resolver.resolve(root_spec)
        if not resolution.ok:
            return UpgradeResult(status="failed", step="dependencies", backup_id=None,
                                 reason=resolution.reason, plan=())
        self._fire(
            "UPGRADE_DEPENDENCIES_OK",
            {"kind": kind, "component_id": component_id, "version": new_version,
             "step": "dependencies", "plan": [f"{s.component_id}@{s.version}" for s in resolution.ordered]},
        )
        if dry_run:
            return UpgradeResult(status="ok", step=None, backup_id=None,
                                 reason="dry-run (no changes applied)", plan=resolution.ordered)

        # -- 3 backup -----------------------------------------------------------
        try:
            backup_id = self._backup.backup(
                kind, component_id, current_version, dict(current)
            )
        except Exception as exc:  # noqa: BLE001 — SQLite errors surface as reason
            return UpgradeResult(status="failed", step="backup", backup_id=None,
                                 reason=f"backup failed: {exc}", plan=resolution.ordered)
        self._fire(
            "UPGRADE_BACKUP_CREATED",
            {"kind": kind, "component_id": component_id, "version": new_version,
             "step": "backup", "backup_id": backup_id},
        )

        # -- 4 migrate ----------------------------------------------------------
        try:
            self._migrator.migrate(kind, component_id, new_version)
        except Exception as exc:  # noqa: BLE001 — UpgradeError wraps underlying
            self._rollback(kind, component_id, backup_id, new_version, "migrate", reason=str(exc))
            return UpgradeResult(status="failed", step="migrate", backup_id=backup_id,
                                 reason=str(exc), plan=resolution.ordered)
        self._fire(
            "UPGRADE_MIGRATED",
            {"kind": kind, "component_id": component_id, "version": new_version, "step": "migrate"},
        )

        # -- 5 health -----------------------------------------------------------
        health_error = self._health_check(kind, component_id, new_version)
        if health_error:
            self._rollback(kind, component_id, backup_id, new_version, "health", reason=health_error)
            return UpgradeResult(status="failed", step="health", backup_id=backup_id,
                                 reason=health_error, plan=resolution.ordered)
        self._fire(
            "UPGRADE_HEALTH_OK",
            {"kind": kind, "component_id": component_id, "version": new_version, "step": "health"},
        )

        # -- 6 complete ---------------------------------------------------------
        self._fire(
            "UPGRADE_COMPLETED",
            {"kind": kind, "component_id": component_id, "version": new_version,
             "step": "complete", "backup_id": backup_id},
        )
        return UpgradeResult(status="ok", step=None, backup_id=backup_id,
                             reason=f"upgraded {current_version} -> {new_version}",
                             plan=resolution.ordered)

    # -- helpers ----------------------------------------------------------------

    def _root_spec(self, kind: str, component_id: str, current_version: str) -> ComponentSpec:
        """Build the root ComponentSpec from the stored payload (dependencies
        stored as list[{"name","version"}] — see SkillMigrator conversion)."""
        payload = self._migrator.read_current(kind, component_id) or {}
        deps: list[Any] = []
        for dep in payload.get("dependencies", []) or []:
            if isinstance(dep, dict) and dep.get("name") and dep.get("version"):
                deps.append(Dependency(dep["name"], dep["version"]))
        return ComponentSpec(kind=kind, component_id=component_id,
                             version=current_version, dependencies=tuple(deps))

    def _health_check(self, kind: str, component_id: str, new_version: str) -> str | None:
        """Verify the migration actually applied + optional validate hook."""
        after = self._migrator.read_current(kind, component_id)
        if after is None:
            return "health check failed: component disappeared after migration"
        if str(after.get("version")) != new_version:
            return (
                f"health check failed: expected version {new_version}, "
                f"got {after.get('version')}"
            )
        if self._validate:
            reason = self._validate(kind, component_id, new_version)
            if reason:
                return f"health check failed: {reason}"
        return None

    def _rollback(
        self,
        kind: str,
        component_id: str,
        backup_id: int,
        new_version: str,
        step: str,
        reason: str,
    ) -> None:
        """Best-effort rollback — errors are recorded, never raised."""
        errors: list[str] = []
        rolled_back = False
        try:
            self._migrator.rollback(kind, component_id)
            rolled_back = True
        except NotImplementedError:
            try:
                payload = self._backup.restore(backup_id)
                self._migrator.write_current(kind, component_id, payload)
                rolled_back = True
            except Exception as exc:  # noqa: BLE001
                errors.append(f"restore failed: {exc}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"rollback failed: {exc}")
        self._fire(
            "UPGRADE_ROLLED_BACK",
            {"kind": kind, "component_id": component_id, "version": new_version,
             "step": step, "rolled_back": rolled_back, "errors": errors, "reason": reason},
        )
