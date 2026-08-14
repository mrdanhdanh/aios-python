"""Memory coordinator contracts: query/candidate/score/selection/context.

Domain-local contracts (INV-006 purity — no imports from aios_core.contracts).
All models are pydantic with ``extra="forbid"`` for strict validation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryKind(str, Enum):
    """The four memory store kinds the coordinator can query."""

    CONVERSATION = "conversation"
    SESSION = "session"
    KNOWLEDGE = "knowledge"
    ARTIFACT = "artifact"


class MemoryBudget(BaseModel):
    """Token budget caps per category (PLAN §3.3 — totals 20K).

    Mirrors ``MemoryBudgetSettings`` in aios_core.config (same schema, kept
    local to avoid a config → memory dependency; RuntimeKernel maps between
    the two).
    """

    model_config = ConfigDict(extra="forbid")

    system: int = 3000
    task: int = 2000
    knowledge: int = 6000
    history: int = 5000
    artifacts: int = 3000
    reserve: int = 1000


class MemoryStrategy(str, Enum):
    """Retrieval strategies (PLAN §3.1)."""

    EXACT = "exact"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    METADATA = "metadata"
    RECENCY = "recency"
    IMPORTANCE = "importance"
    HYBRID = "hybrid"


class MemoryQuery(BaseModel):
    """A single retrieval request against the coordinator."""

    model_config = ConfigDict(extra="forbid")

    text: str
    session_id: str
    strategies: list[MemoryStrategy] = [MemoryStrategy.HYBRID]
    sources: list[MemoryKind] | None = None  # None = all four kinds
    top_k_per_source: int = Field(gt=0, default=20)
    since: datetime | None = None
    min_importance: float = Field(ge=0.0, le=1.0, default=0.0)
    max_chars: int = Field(gt=0, default=2000)  # per-candidate compress cap


class MemoryCandidate(BaseModel):
    """A candidate memory item produced by a source adapter."""

    model_config = ConfigDict(extra="forbid")

    id: str  # dedup-adjacent stable id: "{kind}:{source_id}:{item_id}"
    kind: MemoryKind
    source_id: str
    content: str
    created_at: datetime
    importance: float = 0.5
    metadata: dict[str, Any] = {}
    strategy_hits: list[MemoryStrategy] = []


class MemoryScore(BaseModel):
    """Per-candidate score components (all in [0, 1])."""

    model_config = ConfigDict(extra="forbid")

    semantic: float = 0.0
    relevance: float = 0.0
    recency: float = 0.0
    importance: float = 0.0
    source_priority: float = 0.0
    total: float = 0.0  # weighted sum


class MemorySelection(BaseModel):
    """Ranked, compressed, budgeted selection (result of the pipeline)."""

    model_config = ConfigDict(extra="forbid")

    query: MemoryQuery
    items: list[tuple[MemoryCandidate, MemoryScore]]
    tokens_by_kind: dict[MemoryKind, int]
    total_tokens: int
    budget: dict[MemoryKind, int]  # 4 kinds only; system/reserve live in settings
    truncated: bool


class MemoryContext(BaseModel):
    """The memory section injected into ContextService (scope EXECUTION)."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    sections: dict[MemoryKind, list[str]]
    tokens_by_kind: dict[MemoryKind, int]
    total_tokens: int
    selection: MemorySelection
    created_at: datetime
