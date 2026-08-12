"""Capability registry: agents know capabilities, not tools."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from .errors import CapabilityError

logger = logging.getLogger(__name__)


@dataclass
class Capability:
    name: str
    description: str = ""
    tools: list[str] = field(default_factory=list)  # tool ids providing it


class CapabilityRegistry:
    """Map capabilities to tools and agents (registry is the source of truth).

    M1: ``tool_id`` is a free-form string (no Tool Registry yet); M2 auto-maps
    from ToolContracts. ``get`` returns the live object — callers must not mutate.
    """

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._agent_use: dict[str, set[str]] = {}  # capability -> {agent_id}
        self._lock = threading.RLock()

    def register_capability(self, name: str, description: str = "") -> None:
        if not name.strip():
            raise ValueError("capability name must not be empty")
        with self._lock:
            if name in self._capabilities:
                logger.warning("Overwriting capability %s", name)
            self._capabilities[name] = Capability(name=name, description=description)

    def _check(self, capability: str) -> None:
        if capability not in self._capabilities:
            raise CapabilityError(f"Unknown capability: {capability!r}")

    def bind_tool(self, capability: str, tool_id: str) -> None:
        with self._lock:
            self._check(capability)
            if not tool_id.strip():
                raise ValueError("tool_id must not be empty")
            cap = self._capabilities[capability]
            if tool_id not in cap.tools:
                cap.tools.append(tool_id)

    def unbind_tool(self, capability: str, tool_id: str) -> None:
        with self._lock:
            self._check(capability)
            cap = self._capabilities[capability]
            if tool_id in cap.tools:
                cap.tools.remove(tool_id)

    def get(self, capability: str) -> Capability:
        with self._lock:
            self._check(capability)
            return self._capabilities[capability]

    def tools_for(self, capability: str) -> list[str]:
        with self._lock:
            self._check(capability)
            return list(self._capabilities[capability].tools)

    def list(self) -> list[str]:
        with self._lock:
            return list(self._capabilities.keys())

    def register_agent_use(self, agent_id: str, capability: str) -> None:
        if not agent_id.strip():
            raise ValueError("agent_id must not be empty")
        with self._lock:
            self._check(capability)
            self._agent_use.setdefault(capability, set()).add(agent_id)

    def agents_using(self, capability: str) -> list[str]:
        with self._lock:
            self._check(capability)
            return sorted(self._agent_use.get(capability, set()))
