"""Upgrade & Migration 1.0 — M10-F5 (TASK-074).

MigrationEngine: plan → backup → dry-run → validate → apply → rollback
(release-grade, PLAN §M10-34). Idempotent (completed → từ chối), journal
SQLite, auto-rollback khi step fail (best-effort), tái dùng BackupStore M4.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, field_validator

from ..semver import SEMVER_RE


class MigrationError(RuntimeError):
    pass


@dataclass
class MigrationStep:
    """Một bước migration (kind + fn + rollback_fn optional)."""

    kind: str  # config | plugin | contract | workflow
    id: str
    fn: Callable[[dict[str, Any]], dict[str, Any]]
    rollback_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


class MigrationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    migration_id: str
    kind: str
    from_version: str
    to_version: str
    backup_required: bool = True
    steps: list[Any] = field(default_factory=list)  # MigrationStep (dataclass)

    @field_validator("from_version", "to_version")
    @classmethod
    def _semver(cls, value: str) -> str:
        if not SEMVER_RE.match(value):
            raise ValueError(f"Invalid semver: {value!r}")
        return value

    @field_validator("steps")
    @classmethod
    def _steps_non_empty(cls, value: list) -> list:
        if not value:
            raise ValueError("MigrationPlan phải có ít nhất 1 step")
        return value


class MigrationJournal:
    """SQLite audit trail: migration_id, from/to, status, steps done."""

    def __init__(self, db_path: str | Path = "aios/data/migrations.db") -> None:
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                migration_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                from_version TEXT NOT NULL,
                to_version TEXT NOT NULL,
                status TEXT NOT NULL,
                steps_done TEXT NOT NULL DEFAULT '[]',
                error TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self._conn.commit()

    def status(self, migration_id: str) -> str | None:
        row = self._conn.execute(
            "SELECT status FROM migrations WHERE migration_id = ?", (migration_id,)
        ).fetchone()
        return row[0] if row else None

    def start(self, plan: MigrationPlan) -> None:
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO migrations "
                "(migration_id, kind, from_version, to_version, status) VALUES (?,?,?,?,'running')",
                (plan.migration_id, plan.kind, plan.from_version, plan.to_version),
            )

    def step_done(self, migration_id: str, step_id: str) -> None:
        with self._conn:
            row = self._conn.execute(
                "SELECT steps_done FROM migrations WHERE migration_id = ?",
                (migration_id,),
            ).fetchone()
            steps = json.loads(row[0]) if row else []
            steps.append(step_id)
            self._conn.execute(
                "UPDATE migrations SET steps_done = ? WHERE migration_id = ?",
                (json.dumps(steps), migration_id),
            )

    def finish(self, migration_id: str, status: str, error: str = "") -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE migrations SET status = ?, error = ? WHERE migration_id = ?",
                (status, error, migration_id),
            )


class MigrationEngine:
    """plan → dry_run → validate → apply → rollback (release-grade)."""

    def __init__(self, journal: MigrationJournal | None = None,
                 backup_store: Any | None = None) -> None:
        self.journal = journal or MigrationJournal()
        # backup_store: M4 BackupStore (backup/restore) — optional inject
        self._backup = backup_store

    # -- pipeline -------------------------------------------------------------
    def dry_run(self, plan: MigrationPlan, payload: dict[str, Any]) -> dict[str, Any]:
        """Không side effect — fn KHÔNG được gọi (C1-03)."""
        result = dict(payload)
        for step in plan.steps:
            # mô phỏng: chỉ báo bước sẽ chạy
            result.setdefault("_dry_run_steps", []).append(step.id)
        return result

    def validate(self, plan: MigrationPlan) -> None:
        """Validate plan: version khác nhau + steps có fn."""
        if plan.from_version == plan.to_version:
            raise MigrationError("from_version == to_version — không có gì để migrate")
        for step in plan.steps:
            if not callable(step.fn):
                raise MigrationError(f"step {step.id} thiếu fn")

    def apply(self, plan: MigrationPlan, payload: dict[str, Any]) -> dict[str, Any]:
        """Steps (journal từng bước) → finish completed.

        Fail giữa chừng → journal FAILED + auto-rollback (best-effort).
        Idempotent: status completed → từ chối.
        Backup KHÔNG do engine thực hiện — caller chịu trách nhiệm
        (M12 TASK-085: bỏ call sai signature — backup phải qua
        BackupStore.backup(kind, component_id, version, payload); xem
        Aios110Migrator trong migration_110.py).
        """
        existing = self.journal.status(plan.migration_id)
        if existing == "completed":
            raise MigrationError(f"migration {plan.migration_id} đã applied (idempotent)")
        self.validate(plan)
        self.journal.start(plan)
        result = dict(payload)
        applied: list[MigrationStep] = []
        try:
            for step in plan.steps:
                result = step.fn(result)
                applied.append(step)
                self.journal.step_done(plan.migration_id, step.id)
            self.journal.finish(plan.migration_id, "completed")
            return result
        except Exception as exc:  # noqa: BLE001 — auto-rollback
            self.journal.finish(plan.migration_id, "failed", str(exc))
            self.rollback(plan, payload, applied=applied)
            raise MigrationError(f"migration failed + rolled back: {exc}") from exc

    def rollback(self, plan: MigrationPlan, payload: dict[str, Any],
                 applied: list[MigrationStep] | None = None) -> dict[str, Any]:
        """Rollback ngược các step đã apply (best-effort)."""
        result = dict(payload)
        steps = applied if applied is not None else list(plan.steps)
        for step in reversed(steps):
            if step.rollback_fn is not None:
                try:
                    result = step.rollback_fn(result)
                except Exception:  # noqa: BLE001 — best-effort
                    pass
        self.journal.finish(plan.migration_id, "rolled_back")
        return result


# ---------------------------------------------------------------------------
# Migration formats v0 → v1 (deterministic)
# ---------------------------------------------------------------------------

class MigrationFormats:
    """Format converters cho config/workflow/plugin v0 → v1 (C1-02)."""

    @staticmethod
    def config_v0_to_v1(data: dict[str, Any]) -> dict[str, Any]:
        """v0 `autonomous.budget.max_duration_s` → v1 `max_duration_seconds`."""
        out = json.loads(json.dumps(data))  # deep copy
        budget = out.get("autonomous", {}).get("budget")
        if isinstance(budget, dict) and "max_duration_s" in budget:
            budget["max_duration_seconds"] = budget.pop("max_duration_s")
        return out

    @staticmethod
    def workflow_v0_to_v1(data: dict[str, Any]) -> dict[str, Any]:
        """v0 nodes không có timeout_s → v1 bổ sung timeout_s=300 (default)."""
        out = json.loads(json.dumps(data))
        for node in out.get("nodes", []):
            node.setdefault("timeout_s", 300.0)
        return out

    @staticmethod
    def plugin_v0_to_v1(data: dict[str, Any]) -> dict[str, Any]:
        """v0 `aios: {min, max}` → v1 thêm `compatible: [semver]`."""
        out = json.loads(json.dumps(data))
        aios = out.get("aios")
        if isinstance(aios, dict) and "compatible" not in aios:
            aios["compatible"] = [aios.get("min", "1.0.0")]
        return out
