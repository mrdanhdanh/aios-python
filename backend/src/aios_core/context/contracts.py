"""Context optimizer contracts: priority tiers, sections, budget reports.

Domain-local contracts (INV-006 purity — no imports from aios_core.contracts).
All models are pydantic with ``extra="forbid"``.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class PriorityTier(str, Enum):
    """PLAN §M5-5: P0 System/Safety .. P6 Optional (cut bottom-up)."""

    P0_SYSTEM = "p0_system"  # System/Safety — never cut
    P1_USER = "p1_user"  # User Request — never cut
    P2_EXECUTION = "p2_execution"  # Current Execution State
    P3_KNOWLEDGE = "p3_knowledge"  # Relevant Knowledge
    P4_MEMORY = "p4_memory"  # Relevant Memory (conversation >= threshold)
    P5_HISTORICAL = "p5_historical"  # Historical (conversation < threshold)
    P6_OPTIONAL = "p6_optional"  # Optional (artifacts)


class ContextSection(BaseModel):
    """One unit of context content bound to a priority tier."""

    model_config = ConfigDict(extra="forbid")

    tier: PriorityTier
    source: str  # "system.<key>" | "user.request" | "execution.<key>" | "memory.*"
    content: str
    tokens: int = 0  # set at build; empty content -> 0 (C2-12)


class TierBudgetReport(BaseModel):
    """Per-tier budget accounting (cap None = uncapped or shared — C2-13)."""

    model_config = ConfigDict(extra="forbid")

    tier: PriorityTier
    cap: int | None  # None = uncapped (P1) or shared cap reported elsewhere (P5 -> P4)
    used: int
    dropped_tokens: int
    dropped_items: int


class CompressionReport(BaseModel):
    """Compression + budget drop accounting."""

    model_config = ConfigDict(extra="forbid")

    original_tokens: int  # total right after build, BEFORE L1
    final_tokens: int  # total after EVERY step (C3-08)
    ratio: float  # round(final/original, 4); original=0 -> 1.0
    levels_used: list[int]  # [1], [1,2], [1,2,3], [1,3] (L2 no-op on empty terms — C2-11)
    dropped_by_budget: int  # tokens dropped by budget (not compression)


class FinalContext(BaseModel):
    """The final, ordered, budgeted context for the model."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    sections: list[ContextSection]  # sorted tier asc; tier-internal order preserved
    total_tokens: int
    usable_budget: int  # total - reserve
    tier_reports: list[TierBudgetReport]
    compression: CompressionReport
    truncated: bool
    created_at: datetime

    def render(self) -> str:
        """Deterministic plain-text rendering for model input (YC-7)."""
        _HEADERS = {
            PriorityTier.P0_SYSTEM: "[System]",
            PriorityTier.P1_USER: "[User Request]",
            PriorityTier.P2_EXECUTION: "[Execution State]",
            PriorityTier.P3_KNOWLEDGE: "[Knowledge]",
            PriorityTier.P4_MEMORY: "[Memory]",
            PriorityTier.P5_HISTORICAL: "[Historical]",
            PriorityTier.P6_OPTIONAL: "[Optional]",
        }
        blocks: list[str] = []
        for tier in PriorityTier:
            parts = [s.content for s in self.sections if s.tier is tier]
            if not parts and tier is not PriorityTier.P1_USER:
                continue  # empty tier -> no header (P1 empty still emits header — R3-4)
            blocks.append(_HEADERS[tier])
            if parts:
                blocks.append("\n".join(parts))
        return "\n".join(blocks)
