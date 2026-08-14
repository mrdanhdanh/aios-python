"""Context optimizer: deterministic, budgeted context assembly (M5 TASK-024).

Pipeline (PLAN §4/§5/§6): build (tier mapping) → L1 deterministic compress →
L2 extractive (only when over budget) → L3 LLM stub (optional compressor) →
pre-check → cut bottom-up (per-tier cap, then total budget). Everything is
deterministic: no LLM, no randomness, injectable clock (``now``).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Callable

from ..kernel.services import ContextScope, ContextService
from ..memory import MemoryBudget, MemoryContext, MemoryKind, estimate_tokens
from .contracts import (
    CompressionReport,
    ContextSection,
    FinalContext,
    PriorityTier,
    TierBudgetReport,
)

_WHITESPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

# Memory sections are never merged (C1-01): one section per candidate keeps
# cut-from-bottom item-level granularity.
_MEMORY_PREFIX = "memory."

_TIER_ORDER = [t for t in PriorityTier]  # P0..P6 (priority desc)
_TIER_DESC = [  # cut order: lowest priority first
    PriorityTier.P6_OPTIONAL,
    PriorityTier.P5_HISTORICAL,
    PriorityTier.P4_MEMORY,
    PriorityTier.P3_KNOWLEDGE,
    PriorityTier.P2_EXECUTION,
]
_PRIORITY_INDEX = {tier: i for i, tier in enumerate(_TIER_ORDER)}

ContentCompressor = Callable[[list[ContextSection], int], list[ContextSection]]


def _normalize(text: str) -> str:
    """Dedup key basis: lowercase + collapsed whitespace."""
    return _WHITESPACE_RE.sub(" ", text.strip().lower())


def _tokens(content: str) -> int:
    """Token heuristic; empty content -> 0 (C2-12, not estimate_tokens)."""
    if not content:
        return 0
    return estimate_tokens(content)


def _retoken(section: ContextSection) -> ContextSection:
    """Recompute tokens from current content (C2-03: after every transform)."""
    if section.tokens == _tokens(section.content):
        return section
    return section.model_copy(update={"tokens": _tokens(section.content)})


def _serialize_value(value: Any) -> str:
    """Deterministic stringification (C2-02/C2-03): no memory addresses,
    stable ordering, never raises on pathological containers."""
    if value is None:
        return ""
    if isinstance(value, (set, frozenset)):
        try:
            return str(sorted(value, key=str))
        except TypeError:
            return f"<{type(value).__name__}>"
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, sort_keys=True, default=str)
        except (TypeError, ValueError):  # mixed keys / self-reference
            return f"<{type(value).__name__}>"
    return str(value)


# ---------------------------------------------------------------------------
# L1 — Deterministic compression (always runs)
# ---------------------------------------------------------------------------

def level1_compress(sections: list[ContextSection]) -> list[ContextSection]:
    """Dedup (keep highest tier; P0/P1 never victims — C3-07), drop empties,
    defensive merge for same (tier, source) EXCEPT memory.* (C1-01/C2-02).
    Re-tokens everything (C2-03).
    """
    best: dict[str, tuple[int, ContextSection]] = {}
    order: list[str] = []
    for section in sections:
        if not section.content.strip():
            if section.tier is PriorityTier.P1_USER:
                order.append(_key(section))  # P1 empty is exempt (C2-04)
                best.setdefault(_key(section), (_PRIORITY_INDEX[section.tier], section))
            continue
        key = _key(section)
        existing = best.get(key)
        prio = _PRIORITY_INDEX[section.tier]
        if existing is None:
            best[key] = (prio, section)
            order.append(key)
        elif prio < existing[0]:  # higher priority wins
            best[key] = (prio, section)
        # P0/P1 as victims is impossible: higher-priority sections win dedup,
        # and lower tiers are removed when colliding with P0/P1.
    kept: list[ContextSection] = []
    for key in order:
        _, section = best[key]
        if section.source.startswith(_MEMORY_PREFIX):
            kept.append(_retoken(section))
            continue
        # Defensive merge: same (tier, source) fragments -> join "\n".
        merged = [s for s in kept if s.tier is section.tier and s.source == section.source]
        if merged:
            base = merged[0]
            content = base.content + "\n" + section.content
            kept[kept.index(base)] = _retoken(
                base.model_copy(update={"content": content})
            )
        else:
            kept.append(_retoken(section))
    return kept


def _key(section: ContextSection) -> str:
    return hashlib.sha256(_normalize(section.content).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# L2 — Extractive compression (deterministic heuristic)
# ---------------------------------------------------------------------------

def extractive_compress(
    section: ContextSection, query_terms: set[str], max_chars: int
) -> ContextSection:
    """Keep sentences containing any query term (substring, case-insensitive —
    C2-01). No match -> keep the section unchanged. Truncate to max_chars.
    """
    if not query_terms:
        return section
    sentences = _SENTENCE_SPLIT_RE.split(section.content)
    kept = [
        sentence
        for sentence in sentences
        if any(term in sentence.lower() for term in query_terms)
    ]
    if not kept:
        return section
    content = " ".join(kept)
    if len(content) > max_chars:
        content = content[: max_chars - 1] + "…"
    return _retoken(section.model_copy(update={"content": content}))


# ---------------------------------------------------------------------------
# ContextOptimizer
# ---------------------------------------------------------------------------

class ContextOptimizerConfig:
    """Defaults consolidated (C3-06); clock lives on __init__ only."""

    def __init__(
        self,
        budget: MemoryBudget | None = None,
        relevant_threshold: float = 0.5,
        max_compression_level: int = 2,
        force_extractive: bool = False,
        extractive_max_chars: int = 4000,
        compressor: ContentCompressor | None = None,
    ) -> None:
        self.budget = budget or MemoryBudget()
        if not (0.0 <= relevant_threshold <= 1.0):
            raise ValueError("relevant_threshold must be in [0, 1]")
        self.relevant_threshold = relevant_threshold
        if max_compression_level not in (1, 2, 3):
            raise ValueError("max_compression_level must be 1, 2 or 3")
        self.max_compression_level = max_compression_level
        self.force_extractive = force_extractive
        if extractive_max_chars <= 0:
            raise ValueError("extractive_max_chars must be > 0")
        self.extractive_max_chars = extractive_max_chars
        self.compressor = compressor

    @property
    def total_budget(self) -> int:
        """sum(budget) — use model_dump().values() (R1-1: pydantic iter)."""
        return sum(self.budget.model_dump().values())

    @property
    def usable_budget(self) -> int:
        return self.total_budget - self.budget.reserve


class ContextOptimizer:
    """Assembles a priority-ordered, budgeted context for the model."""

    def __init__(
        self,
        context: ContextService,
        config: ContextOptimizerConfig | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._context = context
        self._config = config or ContextOptimizerConfig()
        self._now = now

    # -- main ---------------------------------------------------------------

    def optimize(self, user_request: str) -> FinalContext:
        config = self._config
        sections = self._build(user_request)
        original_tokens = sum(s.tokens for s in sections)

        levels: list[int] = [1]
        sections = level1_compress(sections)
        total = sum(s.tokens for s in sections)

        terms = set(user_request.lower().split())
        if terms and (total > config.usable_budget or config.force_extractive):
            levels.append(2)
            sections = [
                extractive_compress(s, terms, config.extractive_max_chars)
                if s.tier
                in (PriorityTier.P3_KNOWLEDGE, PriorityTier.P4_MEMORY,
                    PriorityTier.P5_HISTORICAL, PriorityTier.P6_OPTIONAL)
                else s
                for s in sections
            ]
            total = sum(s.tokens for s in sections)

        if (
            config.compressor is not None
            and config.max_compression_level >= 3
            and total > config.usable_budget
        ):
            levels.append(3)
            sections = config.compressor(sections, config.usable_budget)
            sections = [_retoken(s) for s in sections]  # C2-05
            total = sum(s.tokens for s in sections)

        # Pre-check AFTER L2/L3 on re-tokenized totals (C2-10): the ONLY
        # enforcement for P0/P1 (C1-02).
        p0p1 = sum(s.tokens for s in sections if s.tier in (
            PriorityTier.P0_SYSTEM, PriorityTier.P1_USER))
        if p0p1 > config.usable_budget:
            raise ValueError("system + user request exceed usable budget")

        # Per-tier cap (P6 -> P2; P0/P1 exempt).
        sections, tier_dropped = self._cut_per_tier(sections)
        # Total budget cut (bottom-up).
        sections, total_dropped = self._cut_total(sections)

        dropped_tokens = sum(tier_dropped.values()) + sum(total_dropped.values())
        truncated = dropped_tokens > 0

        final_total = sum(s.tokens for s in sections)
        tier_reports = self._tier_reports(sections, tier_dropped, total_dropped)
        compression = CompressionReport(
            original_tokens=original_tokens,
            final_tokens=final_total,
            ratio=round(final_total / original_tokens, 4) if original_tokens else 1.0,
            levels_used=levels,
            dropped_by_budget=dropped_tokens,
        )
        return FinalContext(
            session_id=self._session_id(),
            sections=sections,
            total_tokens=final_total,
            usable_budget=config.usable_budget,
            tier_reports=tier_reports,
            compression=compression,
            truncated=truncated,
            created_at=self._now(),
        )

    # -- build (tier mapping, YC-2) -----------------------------------------

    def _session_id(self) -> str:
        memory_context = self._context.get(
            ContextScope.EXECUTION, "memory.context", inherit=False)
        if isinstance(memory_context, MemoryContext):
            return memory_context.session_id
        return ""

    def _build(self, user_request: str) -> list[ContextSection]:
        sections: list[ContextSection] = []

        for key, value in self._context.get_all(ContextScope.SYSTEM).items():
            content = _serialize_value(value)
            if not content:
                continue
            sections.append(ContextSection(
                tier=PriorityTier.P0_SYSTEM, source=f"system.{key}",
                content=content, tokens=_tokens(content)))

        sections.append(ContextSection(
            tier=PriorityTier.P1_USER, source="user.request",
            content=user_request, tokens=_tokens(user_request)))

        state_keys = [
            key for key in self._context.get_all(
                ContextScope.EXECUTION, inherit=False).keys()
            if key != "memory.context" and not key.startswith("_")
        ]
        for key in state_keys:
            value = self._context.get(ContextScope.EXECUTION, key, inherit=False)
            content = f"{key}: {_serialize_value(value)}"
            if not content.strip():
                continue
            sections.append(ContextSection(
                tier=PriorityTier.P2_EXECUTION, source=f"execution.{key}",
                content=content, tokens=_tokens(content)))

        memory_context = self._context.get(
            ContextScope.EXECUTION, "memory.context", inherit=False)
        if isinstance(memory_context, MemoryContext):  # R3-2
            for candidate, score in memory_context.selection.items:
                if candidate.kind is MemoryKind.SESSION:
                    sections.append(ContextSection(
                        tier=PriorityTier.P2_EXECUTION, source="memory.session",
                        content=candidate.content, tokens=_tokens(candidate.content)))
                elif candidate.kind is MemoryKind.KNOWLEDGE:
                    sections.append(ContextSection(
                        tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                        content=candidate.content, tokens=_tokens(candidate.content)))
                elif candidate.kind is MemoryKind.CONVERSATION:
                    tier = (PriorityTier.P4_MEMORY
                            if score.total >= self._config.relevant_threshold
                            else PriorityTier.P5_HISTORICAL)
                    sections.append(ContextSection(
                        tier=tier, source="memory.history",
                        content=candidate.content, tokens=_tokens(candidate.content)))
                elif candidate.kind is MemoryKind.ARTIFACT:
                    sections.append(ContextSection(
                        tier=PriorityTier.P6_OPTIONAL, source="memory.artifact",
                        content=candidate.content, tokens=_tokens(candidate.content)))

        # Sort: tier asc; stable order within a tier (build order).
        sections.sort(key=lambda s: _PRIORITY_INDEX[s.tier])
        return sections

    # -- cut stages ----------------------------------------------------------

    def _cut_per_tier(self, sections: list[ContextSection]) -> tuple[list[ContextSection], dict[PriorityTier, int]]:
        kept = list(sections)
        dropped: dict[PriorityTier, int] = {tier: 0 for tier in _TIER_ORDER}
        for tier in _TIER_DESC:
            cap = self._cap_for(tier)
            if cap is None:
                continue
            group = [s for s in kept if s.tier is tier]
            if tier is PriorityTier.P4_MEMORY:
                # Shared history cap: P5 (cap None) + P4.
                group = [s for s in kept if s.tier in (
                    PriorityTier.P4_MEMORY, PriorityTier.P5_HISTORICAL)]
            used = sum(s.tokens for s in group)
            if used <= cap:
                continue
            for section in reversed(group):
                if used <= cap:
                    break
                if section.tokens > cap and cap > 0:
                    # Section bigger than its cap: truncate prefix instead of
                    # dropping the whole state (C2-07); not counted as dropped.
                    limit = cap * 4  # chars ≈ cap tokens (heuristic ceil(len/4))
                    content = section.content[: max(limit - 1, 0)] + "…"
                    replacement = _retoken(
                        section.model_copy(update={"content": content}))
                    used -= section.tokens - replacement.tokens
                    idx = kept.index(section)
                    kept[idx] = replacement
                    if used <= cap:
                        break
                    continue
                kept.remove(section)
                used -= section.tokens
                dropped[section.tier] += section.tokens
        return kept, dropped

    def _cap_for(self, tier: PriorityTier) -> int | None:
        budget = self._config.budget
        if tier is PriorityTier.P0_SYSTEM:
            return budget.system  # report-only (exempt — C1-02)
        if tier is PriorityTier.P1_USER:
            return None
        if tier is PriorityTier.P2_EXECUTION:
            return budget.task
        if tier is PriorityTier.P3_KNOWLEDGE:
            return budget.knowledge
        if tier is PriorityTier.P4_MEMORY:
            return budget.history  # shared with P5
        if tier is PriorityTier.P5_HISTORICAL:
            return None  # shared cap reported at P4
        return budget.artifacts  # P6

    def _cut_total(self, sections: list[ContextSection]) -> tuple[list[ContextSection], dict[PriorityTier, int]]:
        kept = list(sections)
        dropped: dict[PriorityTier, int] = {tier: 0 for tier in _TIER_ORDER}
        used = sum(s.tokens for s in kept)
        while used > self._config.usable_budget:
            removed = False
            for tier in _TIER_DESC:
                for idx in range(len(kept) - 1, -1, -1):
                    if kept[idx].tier is tier:
                        section = kept.pop(idx)
                        used -= section.tokens
                        dropped[tier] += section.tokens
                        removed = True
                        break
                if removed:
                    break
            if not removed:  # only P0/P1 left; pre-check would have raised
                break
        return kept, dropped

    def _tier_reports(
        self, sections: list[ContextSection],
        tier_dropped: dict[PriorityTier, int],
        total_dropped: dict[PriorityTier, int],
    ) -> list[TierBudgetReport]:
        reports: list[TierBudgetReport] = []
        for tier in _TIER_ORDER:
            used = sum(s.tokens for s in sections if s.tier is tier)
            cap = self._cap_for(tier)
            reports.append(TierBudgetReport(
                tier=tier, cap=cap, used=used,
                dropped_tokens=tier_dropped[tier] + total_dropped[tier],
                dropped_items=0,
            ))
        return reports
