"""PluginRegistry — read-through view over the plugins table (TASK-044).

DB is the single source of truth; the manager keeps the provides index.
"""

from __future__ import annotations

from pathlib import Path

from .contracts import PluginState, PluginType
from .manager import PluginManager


class PluginRegistry:
    def __init__(self, db_path: Path | str) -> None:
        # Reuse manager for reads (same connection pattern, no state).
        self._manager = PluginManager(db_path)

    def get(self, plugin_id: str) -> "object | None":
        return self._manager.get(plugin_id)

    def list(self) -> list:
        return self._manager.list()

    def list_by_state(self, state: PluginState) -> list:
        return self._manager.list_by_state(state)

    def list_by_kind(self, kind: PluginType) -> list:
        return self._manager.list_by_type(kind)

    def provides(self, kind: PluginType | str) -> dict[str, str]:
        return self._manager.provides(kind)

    def _db_path(self) -> Path:
        return self._manager._db_path  # noqa: SLF001 — test access
