"""Migrator protocol + concrete migrators for the upgrade pipeline (TASK-020)."""

from __future__ import annotations

from typing import Any, Protocol

from ..skills.errors import SkillError, SkillStateError
from .errors import UpgradeError


class Migrator(Protocol):
    """Reads/mutates a component's stored state.

    rollback() may raise NotImplementedError — the pipeline then falls back
    to write_current(backup payload).
    """

    def read_current(self, kind: str, component_id: str) -> dict[str, Any] | None: ...

    def migrate(self, kind: str, component_id: str, new_version: str) -> None: ...

    def rollback(self, kind: str, component_id: str) -> None: ...

    def write_current(self, kind: str, component_id: str, payload: dict[str, Any]) -> None: ...


class DictMigrator:
    """In-memory migrator (tests / workflow / prompt kinds)."""

    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def _key(self, kind: str, component_id: str) -> str:
        return f"{kind}:{component_id}"

    def read_current(self, kind: str, component_id: str) -> dict[str, Any] | None:
        return self._store.get(self._key(kind, component_id))

    def migrate(self, kind: str, component_id: str, new_version: str) -> None:
        key = self._key(kind, component_id)
        if key not in self._store:
            raise UpgradeError(f"component not found: {component_id}")
        self._store[key] = {**self._store[key], "version": new_version}

    def rollback(self, kind: str, component_id: str) -> None:
        raise NotImplementedError("DictMigrator has no native rollback — use write_current")

    def write_current(self, kind: str, component_id: str, payload: dict[str, Any]) -> None:
        self._store[self._key(kind, component_id)] = dict(payload)


class SkillMigrator:
    """Wraps SkillManager (kind=skill) — state-machine-safe operations only."""

    def __init__(self, skill_manager: Any) -> None:
        self._manager = skill_manager

    def read_current(self, kind: str, component_id: str) -> dict[str, Any] | None:
        skill = self._manager.get(component_id)
        if skill is None:
            return None
        return skill.model_dump(mode="json")

    def migrate(self, kind: str, component_id: str, new_version: str) -> None:
        try:
            self._manager.upgrade(component_id, new_version)
        except (SkillError, SkillStateError) as exc:
            raise UpgradeError(
                f"skill {component_id} upgrade failed: {exc}"
            ) from exc

    def rollback(self, kind: str, component_id: str) -> None:
        try:
            self._manager.rollback(component_id)
        except (SkillError, SkillStateError) as exc:
            raise UpgradeError(
                f"skill {component_id} rollback failed: {exc}"
            ) from exc

    def write_current(self, kind: str, component_id: str, payload: dict[str, Any]) -> None:
        raise NotImplementedError("SkillMigrator rolls back via SkillManager.rollback")
