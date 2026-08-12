"""Workflow library: register/search/promote reusable workflows."""

from __future__ import annotations

import logging
import threading

from .definition import WorkflowDefinition
from .errors import WorkflowError

logger = logging.getLogger(__name__)


class WorkflowLibrary:
    """In-memory registry of workflow definitions.

    Canonical name = ``definition.name`` (no separate registration key).
    ``promote`` only bumps a usage counter (M2 uses it for ranking).
    """

    def __init__(self) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}
        self._usage: dict[str, int] = {}
        self._lock = threading.RLock()

    def register(self, definition: WorkflowDefinition) -> None:
        if not isinstance(definition, WorkflowDefinition):
            raise TypeError("register expects a WorkflowDefinition instance")
        with self._lock:
            if definition.name in self._definitions:
                logger.warning("Overwriting workflow %s", definition.name)
            self._definitions[definition.name] = definition
            self._usage.setdefault(definition.name, 0)

    def get(self, name: str) -> WorkflowDefinition:
        with self._lock:
            definition = self._definitions.get(name)
            if definition is None:
                raise WorkflowError(f"Unknown workflow: {name!r}")
            return definition

    def list(self) -> list[str]:
        with self._lock:
            return list(self._definitions.keys())  # insertion order

    def search(self, query: str) -> list[str]:
        if not query.strip():
            return []
        lowered = query.lower()
        with self._lock:
            return [
                name
                for name, definition in self._definitions.items()
                if lowered in name.lower() or lowered in definition.description.lower()
            ]

    def promote(self, name: str) -> int:
        with self._lock:
            if name not in self._definitions:
                raise WorkflowError(f"Unknown workflow: {name!r}")
            self._usage[name] += 1
            return self._usage[name]

    def usage(self, name: str) -> int:
        with self._lock:
            if name not in self._definitions:
                raise WorkflowError(f"Unknown workflow: {name!r}")
            return self._usage[name]
