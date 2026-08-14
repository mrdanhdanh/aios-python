"""Harness ABC + registry (TASK-029, H1): thread-safe, deterministic."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Any

from .context import HarnessContext
from .errors import HarnessRegistrationError, HarnessNotFoundError


class Harness(ABC):
    """Hooks default no-op — subclasses override what they need."""

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    description: str = ""
    tags: list[str] = []

    def prepare(self, ctx: HarnessContext) -> None: ...
    def validate(self, ctx: HarnessContext) -> None: ...
    def run(self, ctx: HarnessContext) -> Any: ...
    def verify(self, ctx: HarnessContext, payload: Any) -> None: ...
    def complete(self, ctx: HarnessContext, payload: Any) -> None: ...
    def on_failure(self, ctx: HarnessContext, error: Exception) -> None: ...
    def diagnose(self, ctx: HarnessContext, error: Exception) -> None: ...


class HarnessRegistry:
    """Register/resolve harnesses by id (deterministic, RLock)."""

    def __init__(self) -> None:
        self._entries: dict[str, Harness] = {}
        self._lock = threading.RLock()

    def register(self, harness: Harness) -> None:
        if not harness.id or not harness.name or not harness.version:
            raise HarnessRegistrationError("id/name/version must be non-empty")
        with self._lock:
            if harness.id in self._entries:
                raise HarnessRegistrationError(
                    f"duplicate harness id: {harness.id!r}")
            self._entries[harness.id] = harness

    def get(self, harness_id: str) -> Harness:
        with self._lock:
            harness = self._entries.get(harness_id)
            if harness is None:
                raise HarnessNotFoundError(f"unknown harness: {harness_id!r}")
            return harness

    def list(self) -> list[str]:
        with self._lock:
            return sorted(self._entries)
