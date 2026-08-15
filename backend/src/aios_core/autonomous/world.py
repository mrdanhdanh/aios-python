"""World Model (TASK-052 — M9-P1).

Autonomous World State — AIOS tin thế giới hiện tại như thế nào (PLAN §M9-8).
**World State ≠ Memory**: WorldModel là store thuần của observable state; mọi
fact có ``source · observed_at · confidence · freshness``. Các fact được
observe từ ngoài (loop/engine) — WorldModel KHÔNG sinh dữ liệu (C1-05 v1).
"""

from __future__ import annotations

import threading
from typing import Any, Callable

from .contracts import WorldFact, WorldScope, WorldState

_TTL_S = 86400.0  # 24h (C1-01 v1)


class WorldModel:
    """In-memory world state store (v1) + confidence decay deterministic.

    Thread-safe (RLock). key = ``f"{scope.value}.{name}"`` (C1-04 v1) —
    unambiguous giữa các scope. History bounded (max_history per scope, FIFO).
    """

    def __init__(
        self,
        clock: Callable[[], float] | None = None,
        ttl_s: float = _TTL_S,
        max_history: int = 100,
    ) -> None:
        self._clock = clock or _default_clock
        self._ttl_s = ttl_s
        self._max_history = max_history
        self._lock = threading.RLock()
        self._facts: dict[str, WorldFact] = {}  # key -> fact mới nhất
        self._history: dict[str, list[dict[str, Any]]] = {}  # scope -> list raw

    # -- public API ------------------------------------------------------------

    def observe(
        self,
        scope: WorldScope,
        name: str,
        value: Any,
        source: str,
        confidence: float = 1.0,
    ) -> WorldFact:
        """Ghi fact + append history (bounded FIFO). Confidence clamp [0,1]."""
        with self._lock:
            conf = min(1.0, max(0.0, confidence))
            fact = WorldFact(
                name=name,
                value=value,
                source=source,
                observed_at=self._clock(),
                confidence=conf,
            )
            key = self._key(scope, name)
            self._facts[key] = fact
            hist = self._history.setdefault(scope.value, [])
            hist.append(
                {
                    "name": name,
                    "value": fact.value,
                    "source": source,
                    "observed_at": fact.observed_at,
                    "confidence": conf,
                }
            )
            if len(hist) > self._max_history:
                del hist[: len(hist) - self._max_history]
            return fact

    def get_fact(self, scope: WorldScope, name: str) -> WorldFact | None:
        """Trả fact mới nhất (raw). None nếu chưa observe."""
        with self._lock:
            return self._facts.get(self._key(scope, name))

    def effective_confidence(self, scope: WorldScope, name: str) -> float:
        """confidence * freshness tại thời điểm get (C2-02 v2)."""
        with self._lock:
            fact = self.get_fact(scope, name)
            if fact is None:
                return 0.0
            return fact.confidence * self._freshness(fact.observed_at)

    def freshness(self, scope: WorldScope, name: str) -> float:
        """freshness của fact: max(0, 1 - age_s / TTL_S) (C1-01 v1)."""
        with self._lock:
            fact = self.get_fact(scope, name)
            if fact is None:
                return 0.0
            return self._freshness(fact.observed_at)

    def snapshot(self) -> WorldState:
        """Snapshot deterministic (sorted theo key) — đủ 7 nhóm (AC7)."""
        with self._lock:
            groups: dict[str, dict[str, Any]] = {scope.value: {} for scope in WorldScope}
            for key, fact in sorted(self._facts.items()):
                scope_name, _, name = key.partition(".")
                if scope_name in groups:
                    groups[scope_name][name] = fact.value
            history = {scope: list(items) for scope, items in sorted(self._history.items())}
            return WorldState(
                system=groups[WorldScope.SYSTEM.value],
                runtime=groups[WorldScope.RUNTIME.value],
                goals=groups[WorldScope.GOALS.value],
                tasks=groups[WorldScope.TASKS.value],
                environment=groups[WorldScope.ENVIRONMENT.value],
                constraints=groups[WorldScope.CONSTRAINTS.value],
                history=history,
            )

    def has_changed(self) -> bool:
        """Bất kỳ history nào có > 1 entry? (dùng cho governor REPLAN predicate)."""
        with self._lock:
            return any(len(items) > 1 for items in self._history.values())

    # -- internals -------------------------------------------------------------

    def _key(self, scope: WorldScope, name: str) -> str:
        return f"{scope.value}.{name}"

    def _freshness(self, observed_at: float) -> float:
        age_s = max(0.0, self._clock() - observed_at)
        return max(0.0, 1.0 - age_s / self._ttl_s)


def _default_clock() -> float:
    import time

    return time.time()
