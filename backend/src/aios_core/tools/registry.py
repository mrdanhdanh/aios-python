"""ToolRegistry — thread-safe tool registry + capability binding (TASK-014)."""

from __future__ import annotations

import threading
from collections.abc import Callable

from .base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not isinstance(tool, Tool):
            raise TypeError(f"expected Tool, got {type(tool).__name__}")
        with self._lock:
            if tool.id in self._tools:
                raise ValueError(f"tool already registered: {tool.id}")
            self._tools[tool.id] = tool

    def get(self, tool_id: str) -> Tool | None:
        with self._lock:
            return self._tools.get(tool_id)

    def list(self) -> list[Tool]:
        with self._lock:
            return list(self._tools.values())

    def list_by_capability(self, capability: str) -> list[Tool]:
        with self._lock:
            return [t for t in self._tools.values() if capability in t.capabilities]

    def tools_for_capability(self, capability: str) -> list[Tool]:
        return self.list_by_capability(capability)

    def all_available(self) -> list[Tool]:
        with self._lock:
            return [t for t in self._tools.values() if t.available()]

    def capabilities(self) -> dict[str, list[str]]:
        with self._lock:
            mapping: dict[str, set[str]] = {}
            for tool in self._tools.values():
                for cap in tool.capabilities:
                    mapping.setdefault(cap, set()).add(tool.id)
            return {cap: sorted(ids) for cap, ids in mapping.items()}

    def bind_capabilities(self, bind_tool: Callable[[str, str], None]) -> int:
        """Bind every (capability, tool_id) pair via the injectable callable.

        Returns the total number of pairs processed (6 for default tools —
        including a second call, C1-11). No rollback on mid-way raise (C2-06).
        Pairs are collected under the lock; bind_tool is called OUTSIDE it (R5).
        """
        with self._lock:
            pairs = []
            for tool in self._tools.values():
                seen: set[str] = set()
                for cap in tool.capabilities:
                    if cap not in seen:
                        seen.add(cap)
                        pairs.append((cap, tool.id))
        for cap, tool_id in pairs:
            bind_tool(cap, tool_id)
        return len(pairs)
