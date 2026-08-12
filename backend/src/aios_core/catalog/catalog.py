"""System catalog: index + search system metadata (no registry scans)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from .errors import CatalogError


@dataclass
class CatalogEntry:
    kind: str
    id: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _collect_scalar_strings(value: Any, out: list[str]) -> None:
    if value is None:
        return
    if isinstance(value, dict):
        for v in value.values():
            _collect_scalar_strings(v, out)
    elif isinstance(value, list):
        for v in value:
            _collect_scalar_strings(v, out)
    else:
        out.append(str(value).lower())


class SystemCatalog:
    """In-memory metadata catalog ("mục lục" của AIOS).

    Search matches scalar string values recursively (keys are NOT searched).
    """

    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], CatalogEntry] = {}
        self._lock = threading.RLock()

    def index_entry(self, kind: str, id: str, metadata: dict[str, Any]) -> None:
        with self._lock:
            self._entries[(kind, id)] = CatalogEntry(kind=kind, id=id, metadata=dict(metadata))

    def remove_entry(self, kind: str, id: str) -> None:
        with self._lock:
            self._entries.pop((kind, id), None)  # idempotent

    def get(self, kind: str, id: str) -> CatalogEntry:
        with self._lock:
            entry = self._entries.get((kind, id))
            if entry is None:
                raise CatalogError(f"Unknown catalog entry: {kind}/{id}")
            return entry

    def search(self, query: str, kind: str | None = None) -> list[CatalogEntry]:
        if not query.strip():
            with self._lock:
                return self._filtered(kind)
        lowered = query.lower()
        with self._lock:
            results = []
            for entry in self._filtered(kind):
                haystack: list[str] = [entry.id.lower()]
                _collect_scalar_strings(entry.metadata, haystack)
                if any(lowered in h for h in haystack):
                    results.append(entry)
            return results

    def _filtered(self, kind: str | None) -> list[CatalogEntry]:
        entries = list(self._entries.values())
        if kind is not None:
            entries = [e for e in entries if e.kind == kind]
        return sorted(entries, key=lambda e: (e.kind, e.id))

    def count(self) -> int:
        with self._lock:
            return len(self._entries)
