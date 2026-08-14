"""Memory coordinator: deterministic pipeline over the four memory stores.

Pipeline: Retrieve → Filter → Rank → Compress → Deduplicate → Prioritize
(C2-03: compress before dedup so long same-prefix contents collapse).
Everything is deterministic: no LLM, no randomness, injectable clock.
The coordinator is a pure orchestrator — store logic lives in ``sources.py``.
"""

from __future__ import annotations

import hashlib
import math
import re
import time
from datetime import datetime, timezone
from typing import Callable

from ..kernel.services import ContextScope, ContextService
from .contracts import (
    MemoryBudget,
    MemoryCandidate,
    MemoryContext,
    MemoryKind,
    MemoryQuery,
    MemoryScore,
    MemorySelection,
    MemoryStrategy,
)
from .sources import MemorySource

_WHITESPACE_RE = re.compile(r"\s+")
_EMPTY_ITEMS: list[tuple[MemoryCandidate, MemoryScore]] = []

# HYBRID expands to these concrete strategies (PLAN §3.1).
_HYBRID_EXPANSION = (
    MemoryStrategy.SEMANTIC,
    MemoryStrategy.KEYWORD,
    MemoryStrategy.RECENCY,
)

# Strategies that do NOT need query text (they work with empty text).
_TEXT_FREE_STRATEGIES = frozenset(
    {MemoryStrategy.RECENCY, MemoryStrategy.IMPORTANCE}
)

# kind → category name (PLAN §3.3; system/reserve are TASK-024's domain).
_KIND_TO_CATEGORY: dict[MemoryKind, str] = {
    MemoryKind.CONVERSATION: "history",
    MemoryKind.SESSION: "task",
    MemoryKind.KNOWLEDGE: "knowledge",
    MemoryKind.ARTIFACT: "artifacts",
}


def estimate_tokens(text: str) -> int:
    """Deterministic token heuristic: ceil(len/4) (PLAN §3.3)."""
    return max(1, math.ceil(len(text) / 4))


def _normalize(text: str) -> str:
    """Dedup key basis: lowercase + collapsed whitespace."""
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class MemoryCoordinatorConfig:
    """Weights must sum to 1.0 (validated). Budget mirrors PLAN §3.3 caps."""

    def __init__(
        self,
        budget: MemoryBudget | None = None,
        weights: dict[str, float] | None = None,
        half_life_days: float = 7.0,
        source_priority: dict[MemoryKind, float] | None = None,
    ) -> None:
        self.budget = budget or MemoryBudget()
        self.weights = weights or {
            "semantic": 0.35,
            "relevance": 0.25,
            "recency": 0.15,
            "importance": 0.10,
            "source_priority": 0.15,
        }
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1.0, got {total}")
        if half_life_days <= 0:
            raise ValueError("half_life_days must be > 0")
        self.half_life_days = half_life_days
        self.source_priority = source_priority or {
            MemoryKind.CONVERSATION: 1.0,
            MemoryKind.SESSION: 0.9,
            MemoryKind.KNOWLEDGE: 0.8,
            MemoryKind.ARTIFACT: 0.7,
        }

    def budget_for(self, kind: MemoryKind) -> int:
        return getattr(self.budget, _KIND_TO_CATEGORY[kind])


class MemoryCoordinator:
    """Orchestrates retrieve → filter → rank → compress → dedup → budget.

    ``inject()`` writes the resulting MemoryContext into ContextService
    (EXECUTION scope) — agents never talk to memory stores directly (INV-011).
    """

    def __init__(
        self,
        sources: list[MemorySource],
        context: ContextService,
        config: MemoryCoordinatorConfig | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._sources = list(sources)
        self._context = context
        self._config = config or MemoryCoordinatorConfig()
        self._clock = clock

    # -- pipeline ---------------------------------------------------------

    def retrieve(self, query: MemoryQuery) -> MemorySelection:
        """Run the full pipeline and return the budgeted selection."""
        if query.text.strip() == "" and not (
            set(query.strategies) & _TEXT_FREE_STRATEGIES
        ):
            return self._empty_selection(query)
        candidates = self._retrieve(query)
        candidates = self._filter(query, candidates)
        candidates = self._top_k(query, candidates)
        scored = self._rank(query, candidates)
        scored = self._compress(query, scored)
        scored = self._dedup(scored)
        return self._prioritize(query, scored)

    def inject(self, query: MemoryQuery) -> MemoryContext:
        """Run the pipeline and write the context into ContextService."""
        selection = self.retrieve(query)
        sections: dict[MemoryKind, list[str]] = {}
        for kind in MemoryKind:
            sections[kind] = [
                candidate.content
                for candidate, _ in selection.items
                if candidate.kind is kind
            ]
        memory_context = MemoryContext(
            session_id=query.session_id,
            sections=sections,
            tokens_by_kind=selection.tokens_by_kind,
            total_tokens=selection.total_tokens,
            selection=selection,
            created_at=datetime.now(timezone.utc),
        )
        self._context.set(ContextScope.EXECUTION, "memory.context", memory_context)
        return memory_context

    # -- stages ------------------------------------------------------------

    def _retrieve(self, query: MemoryQuery) -> list[MemoryCandidate]:
        strategies: list[MemoryStrategy] = []
        for strategy in query.strategies:
            if strategy is MemoryStrategy.HYBRID:
                strategies.extend(_HYBRID_EXPANSION)
            else:
                strategies.append(strategy)
        candidates: list[MemoryCandidate] = []
        for source in self._sources:
            for strategy in strategies:
                if strategy not in source.supported_strategies:
                    continue
                candidates.extend(source.retrieve(query, strategy))
        return candidates

    def _filter(self, query: MemoryQuery, candidates: list[MemoryCandidate]) -> list[MemoryCandidate]:
        allowed = set(query.sources) if query.sources is not None else None
        result: list[MemoryCandidate] = []
        for candidate in candidates:
            if allowed is not None and candidate.kind not in allowed:
                continue
            if query.since is not None and candidate.kind is not MemoryKind.KNOWLEDGE:
                # Knowledge has no real timestamp (epoch) → skips `since` (C2-12).
                if _coerce_utc(candidate.created_at) < query.since:
                    continue
            if candidate.importance < query.min_importance:
                continue
            if not candidate.content.strip():
                continue
            result.append(candidate)
        return result

    def _top_k(self, query: MemoryQuery, candidates: list[MemoryCandidate]) -> list[MemoryCandidate]:
        """Per (kind, source_id): keep the N newest (created_at desc, id asc)."""
        groups: dict[tuple[MemoryKind, str], list[MemoryCandidate]] = {}
        for candidate in candidates:
            groups.setdefault((candidate.kind, candidate.source_id), []).append(candidate)
        result: list[MemoryCandidate] = []
        for group in groups.values():
            group.sort(
                key=lambda c: (
                    _coerce_utc(c.created_at),
                    c.id,
                ),
                reverse=True,
            )
            result.extend(group[: query.top_k_per_source])
        return result

    def _rank(self, query: MemoryQuery, candidates: list[MemoryCandidate]) -> list[tuple[MemoryCandidate, MemoryScore]]:
        scored: list[tuple[MemoryCandidate, MemoryScore]] = []
        now = self._clock()
        for candidate in candidates:
            score = self._score(query, candidate, now)
            scored.append((candidate, score))
        scored.sort(
            key=lambda pair: (
                pair[1].total,
                pair[1].source_priority,
                _coerce_utc(pair[0].created_at),
                pair[0].id,
            ),
            reverse=True,
        )
        return scored

    def _score(self, query: MemoryQuery, candidate: MemoryCandidate, now: float) -> MemoryScore:
        hits = set(candidate.strategy_hits)
        semantic = float(candidate.metadata.get("semantic_score", 0.0))
        if MemoryStrategy.SEMANTIC not in hits:
            semantic = 0.0
        relevance = 0.0
        if MemoryStrategy.EXACT in hits:
            relevance = 1.0
        elif MemoryStrategy.KEYWORD in hits:
            query_terms = set(query.text.lower().split())
            content_terms = set(candidate.content.lower().split())
            relevance = (
                len(query_terms & content_terms) / len(query_terms) if query_terms else 0.0
            )
        age_days = max(0.0, now - _coerce_utc(candidate.created_at).timestamp()) / 86400.0
        recency = max(0.0, min(1.0, 1.0 - age_days / self._config.half_life_days))
        importance = max(0.0, min(1.0, candidate.importance))
        source_priority = self._config.source_priority.get(candidate.kind, 0.5)
        w = self._config.weights
        total = (
            w["semantic"] * semantic
            + w["relevance"] * relevance
            + w["recency"] * recency
            + w["importance"] * importance
            + w["source_priority"] * source_priority
        )
        return MemoryScore(
            semantic=semantic,
            relevance=relevance,
            recency=recency,
            importance=importance,
            source_priority=source_priority,
            total=round(total, 6),
        )

    def _compress(
        self, query: MemoryQuery, scored: list[tuple[MemoryCandidate, MemoryScore]]
    ) -> list[tuple[MemoryCandidate, MemoryScore]]:
        result: list[tuple[MemoryCandidate, MemoryScore]] = []
        for candidate, score in scored:
            content = candidate.content
            if len(content) > query.max_chars:
                content = content[: query.max_chars - 1] + "…"
            result.append((candidate.model_copy(update={"content": content}), score))
        return result

    def _dedup(
        self, scored: list[tuple[MemoryCandidate, MemoryScore]]
    ) -> list[tuple[MemoryCandidate, MemoryScore]]:
        best: dict[str, tuple[MemoryCandidate, MemoryScore]] = {}
        for candidate, score in scored:
            key = hashlib.sha256(_normalize(candidate.content).encode("utf-8")).hexdigest()
            existing = best.get(key)
            if existing is None or score.total > existing[1].total:
                best[key] = (candidate, score)
        # Preserve global ranking order (already sorted by total desc).
        seen: set[str] = set()
        result: list[tuple[MemoryCandidate, MemoryScore]] = []
        for candidate, score in scored:
            key = hashlib.sha256(_normalize(candidate.content).encode("utf-8")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            result.append(best[key])
        return result

    def _prioritize(
        self, query: MemoryQuery, scored: list[tuple[MemoryCandidate, MemoryScore]]
    ) -> MemorySelection:
        tokens_by_kind = {kind: 0 for kind in MemoryKind}
        budget = {kind: self._config.budget_for(kind) for kind in MemoryKind}
        kept: list[tuple[MemoryCandidate, MemoryScore]] = []
        truncated = False
        for candidate, score in scored:
            cost = estimate_tokens(candidate.content)  # after compress (R3-2)
            if tokens_by_kind[candidate.kind] + cost > budget[candidate.kind]:
                truncated = True
                continue
            tokens_by_kind[candidate.kind] += cost
            kept.append((candidate, score))
        return MemorySelection(
            query=query,
            items=kept,
            tokens_by_kind=tokens_by_kind,
            total_tokens=sum(tokens_by_kind.values()),
            budget=budget,
            truncated=truncated,
        )

    def _empty_selection(self, query: MemoryQuery) -> MemorySelection:
        return MemorySelection(
            query=query,
            items=[],
            tokens_by_kind={kind: 0 for kind in MemoryKind},
            total_tokens=0,
            budget={kind: self._config.budget_for(kind) for kind in MemoryKind},
            truncated=False,
        )
