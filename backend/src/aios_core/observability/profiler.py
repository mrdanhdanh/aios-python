"""In-memory performance profiler (TASK-021) — deterministic, no threads."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileSection:
    name: str
    section: str
    duration_ms: float


class Profiler:
    """Records elapsed time per (name, section) — injectable clock for tests."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.perf_counter
        self._sections: list[ProfileSection] = []
        self._active: dict[tuple[str, str], float] = {}

    def start(self, name: str, section: str) -> None:
        key = (name, section)
        if key in self._active:
            raise ValueError(f"profiler section already started: {name}/{section}")
        self._active[key] = self._clock()

    def stop(self, name: str, section: str) -> ProfileSection:
        key = (name, section)
        if key not in self._active:
            raise ValueError(f"profiler section not started: {name}/{section}")
        duration_ms = (self._clock() - self._active.pop(key)) * 1000.0
        record = ProfileSection(name=name, section=section, duration_ms=duration_ms)
        self._sections.append(record)
        return record

    def profile(self, name: str, section: str) -> "Profiler._ProfileCtx":
        return self._ProfileCtx(self, name, section)

    class _ProfileCtx:
        def __init__(self, profiler: "Profiler", name: str, section: str) -> None:
            self._profiler = profiler
            self._name = name
            self._section = section

        def __enter__(self) -> "Profiler._ProfileCtx":
            self._profiler.start(self._name, self._section)
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            self._profiler.stop(self._name, self._section)

    def report(self) -> list[ProfileSection]:
        return list(self._sections)

    def clear(self) -> None:
        self._sections.clear()
        self._active.clear()
