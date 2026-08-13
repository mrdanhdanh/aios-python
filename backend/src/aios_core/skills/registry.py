"""SkillRegistry — read-through view over the skills table (TASK-015).

DB is the single source of truth; no in-memory cache (lesson F-006).
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from .base import SkillState
from .manager import SkillManager


class SkillRegistry:
    def __init__(self, db_path: Path | str) -> None:
        # Reuse manager for reads (same connection pattern, no state).
        self._manager = SkillManager(db_path)

    def get(self, skill_id: str) -> "object | None":
        return self._manager.get(skill_id)

    def list(self) -> list:
        return self._manager.list()

    def list_by_state(self, state: SkillState) -> list:
        return self._manager.list_by_state(state)

    def list_by_capability(self, capability: str) -> list:
        return self._manager.list_by_capability(capability)

    def _db_path(self) -> Path:
        return self._manager._db_path  # noqa: SLF001 — test access
