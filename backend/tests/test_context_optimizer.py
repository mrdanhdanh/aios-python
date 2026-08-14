"""TASK-024 — Context Optimizer tests (M5-P9): tier mapping, L1/L2/L3
compression, INV-012 budget, render, determinism, integration."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from aios_core.context import (
    CompressionReport,
    ContextOptimizer,
    ContextOptimizerConfig,
    ContextSection,
    FinalContext,
    PriorityTier,
    TierBudgetReport,
    extractive_compress,
    level1_compress,
)
from aios_core.kernel.services import ContextScope, ContextService
from aios_core.memory import (
    MemoryBudget,
    MemoryCandidate,
    MemoryContext,
    MemoryKind,
    MemoryQuery,
    MemoryScore,
    MemorySelection,
)

FIXED_NOW = datetime(2026, 8, 14, tzinfo=timezone.utc)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Scenario budget (R1-2): total 3600, usable = 2800.
SCENARIO_BUDGET = MemoryBudget(
    system=400, task=500, knowledge=600, history=800, artifacts=500, reserve=800
)


@pytest.fixture
def context() -> ContextService:
    return ContextService()


def make_memory_context(
    session_id: str = "s1",
    items: list[tuple[MemoryCandidate, MemoryScore]] | None = None,
) -> MemoryContext:
    items = items or []
    query = MemoryQuery(text="", session_id=session_id)
    selection = MemorySelection(
        query=query,
        items=items,
        tokens_by_kind={kind: 0 for kind in MemoryKind},
        total_tokens=0,
        budget={kind: 0 for kind in MemoryKind},
        truncated=False,
    )
    return MemoryContext(
        session_id=session_id,
        sections={kind: [] for kind in MemoryKind},
        tokens_by_kind={kind: 0 for kind in MemoryKind},
        total_tokens=0,
        selection=selection,
        created_at=_EPOCH,
    )


def candidate(kind: MemoryKind, content: str, total: float = 0.5, cid: str = "") -> tuple[MemoryCandidate, MemoryScore]:
    return (
        MemoryCandidate(
            id=f"{kind.value}:{cid or content[:8]}", kind=kind, source_id="src",
            content=content, created_at=_EPOCH,
        ),
        MemoryScore(total=total),
    )


def make_optimizer(context: ContextService, config: ContextOptimizerConfig | None = None) -> ContextOptimizer:
    return ContextOptimizer(context=context, config=config, now=lambda: FIXED_NOW)


# ---------------------------------------------------------------------------
# YC-1 — Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            ContextSection(tier=PriorityTier.P0_SYSTEM, source="s", content="c", bogus=1)
        with pytest.raises(ValidationError):
            FinalContext(session_id="s", sections=[], total_tokens=0, usable_budget=1,
                         tier_reports=[], compression=CompressionReport(
                             original_tokens=0, final_tokens=0, ratio=1.0,
                             levels_used=[1], dropped_by_budget=0),
                         truncated=False, created_at=FIXED_NOW, bogus=1)

    def test_render_empty_p1_emits_header(self, context):
        optimizer = make_optimizer(context)
        final = optimizer.optimize("")
        rendered = final.render()
        assert "[User Request]" in rendered  # P1 empty still emits header (R3-4)

    def test_render_tier_order(self, context):
        context.set(ContextScope.SYSTEM, "sys", "system content")
        optimizer = make_optimizer(context)
        final = optimizer.optimize("user ask")
        rendered = final.render()
        assert rendered.index("[System]") < rendered.index("[User Request]")

    def test_render_deterministic(self, context):
        context.set(ContextScope.SYSTEM, "sys", "hello")
        optimizer = make_optimizer(context)
        assert optimizer.optimize("hi").render() == optimizer.optimize("hi").render()


# ---------------------------------------------------------------------------
# YC-2 — Tier mapping
# ---------------------------------------------------------------------------

class TestTierMapping:
    def test_p0_system(self, context):
        context.set(ContextScope.SYSTEM, "safety", "deny all")
        final = make_optimizer(context).optimize("hi")
        sections = [s for s in final.sections if s.tier is PriorityTier.P0_SYSTEM]
        assert sections and sections[0].source == "system.safety"
        assert sections[0].content == "deny all"

    def test_p2_execution_state(self, context):
        context.set(ContextScope.EXECUTION, "node", "n1")
        context.set(ContextScope.EXECUTION, "_private", "hidden")
        final = make_optimizer(context).optimize("hi")
        sources = {s.source for s in final.sections if s.tier is PriorityTier.P2_EXECUTION}
        assert "execution.node" in sources
        assert "_private" not in sources  # metadata keys dropped

    def test_p3_p4_p5_p6_memory(self, context):
        items = [
            candidate(MemoryKind.KNOWLEDGE, "k" * 100, total=0.9),
            candidate(MemoryKind.CONVERSATION, "m" * 100, total=0.9),
            candidate(MemoryKind.CONVERSATION, "h" * 100, total=0.2),
            candidate(MemoryKind.ARTIFACT, "a" * 100, total=0.5),
        ]
        context.set(ContextScope.EXECUTION, "memory.context", make_memory_context(items=items))
        final = make_optimizer(context).optimize("hi")
        tiers = {s.tier for s in final.sections}
        assert PriorityTier.P3_KNOWLEDGE in tiers
        assert PriorityTier.P4_MEMORY in tiers
        assert PriorityTier.P5_HISTORICAL in tiers
        assert PriorityTier.P6_OPTIONAL in tiers
        p4 = [s for s in final.sections if s.tier is PriorityTier.P4_MEMORY]
        p5 = [s for s in final.sections if s.tier is PriorityTier.P5_HISTORICAL]
        assert p4[0].content == "m" * 100
        assert p5[0].content == "h" * 100

    def test_no_memory_context_no_crash(self, context):
        final = make_optimizer(context).optimize("hi")
        tiers = {s.tier for s in final.sections}
        assert PriorityTier.P3_KNOWLEDGE not in tiers
        assert final.total_tokens >= 0

    def test_wrong_type_memory_context_treated_none(self, context):
        context.set(ContextScope.EXECUTION, "memory.context", "not a MemoryContext")
        final = make_optimizer(context).optimize("hi")  # R3-2: no AttributeError
        assert final is not None

    def test_serialize_deterministic(self, context):
        context.set(ContextScope.SYSTEM, "obj", {"b": 1, "a": [1, 2]})
        final = make_optimizer(context).optimize("hi")
        content = [s for s in final.sections if s.source == "system.obj"][0].content
        assert content == '{"a": [1, 2], "b": 1}'

    def test_serialize_pathological(self, context):
        weird = {"x": {"self": None}}
        weird["x"]["self"] = weird  # self-reference
        context.set(ContextScope.SYSTEM, "weird", weird)
        context.set(ContextScope.SYSTEM, "mixed", {1: "a", "b": 2})
        context.set(ContextScope.SYSTEM, "aset", {"p", "q"})
        final = make_optimizer(context).optimize("hi")  # C2-03: no crash
        assert final is not None


# ---------------------------------------------------------------------------
# YC-3 — L1 deterministic compression
# ---------------------------------------------------------------------------

class TestLevel1:
    def test_dedup_keeps_higher_tier(self):
        sections = [
            ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                           content="same text", tokens=1),
            ContextSection(tier=PriorityTier.P0_SYSTEM, source="system.sys",
                           content="Same  TEXT", tokens=1),
        ]
        result = level1_compress(sections)
        assert len(result) == 1
        assert result[0].tier is PriorityTier.P0_SYSTEM

    def test_p0p1_never_victim(self):
        sections = [
            ContextSection(tier=PriorityTier.P1_USER, source="user.request",
                           content="critical request", tokens=1),
            ContextSection(tier=PriorityTier.P6_OPTIONAL, source="memory.artifact",
                           content="critical request", tokens=1),
        ]
        result = level1_compress(sections)
        assert len(result) == 1
        assert result[0].tier is PriorityTier.P1_USER

    def test_memory_never_merged(self):
        sections = [
            ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                           content="k1", tokens=1),
            ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                           content="k2", tokens=1),
        ]
        result = level1_compress(sections)
        assert len(result) == 2  # C1-01: item-level granularity preserved

    def test_merge_fragments_defensive(self):
        sections = [
            ContextSection(tier=PriorityTier.P2_EXECUTION, source="execution.flow",
                           content="part one", tokens=1),
            ContextSection(tier=PriorityTier.P2_EXECUTION, source="execution.flow",
                           content="part two", tokens=1),
        ]
        result = level1_compress(sections)
        assert len(result) == 1
        assert result[0].content == "part one\npart two"

    def test_retoken_after_merge(self):
        sections = [
            ContextSection(tier=PriorityTier.P2_EXECUTION, source="execution.a",
                           content="x" * 10, tokens=999),  # stale
        ]
        result = level1_compress(sections)
        assert result[0].tokens == 3  # ceil(10/4) — re-tokenized (C2-03)


# ---------------------------------------------------------------------------
# YC-4 — L2 extractive compression
# ---------------------------------------------------------------------------

class TestLevel2:
    def test_keeps_matching_sentences(self):
        section = ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                                 content="First sentence about bugs. Second unrelated. Third mentions bug again.",
                                 tokens=10)
        result = extractive_compress(section, {"bug"}, max_chars=4000)
        assert "unrelated" not in result.content
        assert result.content.count("bug") == 2

    def test_case_insensitive(self):
        section = ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                                 content="Fix the issue now. Elsewhere nothing.", tokens=10)
        result = extractive_compress(section, {"fix"}, max_chars=4000)
        assert "Fix" in result.content  # case-insensitive match (C2-01)

    def test_punctuation_substring(self):
        section = ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                                 content="Bug, handling here. Else nothing.", tokens=10)
        result = extractive_compress(section, {"bug"}, max_chars=4000)
        assert "Bug," in result.content

    def test_no_match_keeps_original(self):
        section = ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                                 content="Nothing relevant here at all.", tokens=10)
        result = extractive_compress(section, {"zzz"}, max_chars=4000)
        assert result.content == "Nothing relevant here at all."

    def test_empty_terms_noop(self):
        section = ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                                 content="Any content at all.", tokens=10)
        assert extractive_compress(section, set(), max_chars=4000).content == section.content

    def test_truncate_max_chars(self):
        section = ContextSection(tier=PriorityTier.P3_KNOWLEDGE, source="memory.knowledge",
                                 content="bug " + "y" * 4000, tokens=1000)
        result = extractive_compress(section, {"bug"}, max_chars=100)
        assert len(result.content) == 100
        assert result.content.endswith("…")

    def test_only_p3_to_p6_applied(self, context):
        context.set(ContextScope.SYSTEM, "sys", "system text with target term")
        context.set(ContextScope.EXECUTION, "state", "state text with target term")
        budget = MemoryBudget(system=400, task=500, knowledge=600, history=800,
                              artifacts=500, reserve=800)
        optimizer = make_optimizer(context, ContextOptimizerConfig(
            budget=budget, force_extractive=True))
        final = optimizer.optimize("target")
        for s in final.sections:
            if s.tier in (PriorityTier.P0_SYSTEM, PriorityTier.P2_EXECUTION):
                assert "with target term" in s.content  # unchanged

    def test_levels_used_2_even_no_match(self, context):
        # over budget + terms present + no sentence matches -> [1,2] (R2-2)
        context.set(ContextScope.SYSTEM, "sys", "q" * 1600)  # P0 400
        context.set(ContextScope.EXECUTION, "node", "n" * 6000)  # P2 ~1502
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=SCENARIO_BUDGET))
        # P1 998 -> total 400+998+1502 = 2900 > 2800; P0+P1 1398 <= 2800
        final = optimizer.optimize("zzz " + "q" * 3988)
        assert 2 in final.compression.levels_used
        assert 1 in final.compression.levels_used

    def test_force_extractive_empty_terms_noop(self, context):
        context.set(ContextScope.SYSTEM, "sys", "q" * 1600)
        optimizer = make_optimizer(context, ContextOptimizerConfig(
            budget=SCENARIO_BUDGET, force_extractive=True))
        final = optimizer.optimize("")  # empty request -> L2 no-op (C2-09)
        assert final.compression.levels_used == [1]


# ---------------------------------------------------------------------------
# YC-5 — L3 stub
# ---------------------------------------------------------------------------

class TestLevel3:
    def test_default_no_l3(self, context):
        context.set(ContextScope.SYSTEM, "sys", "q" * 1600)
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=SCENARIO_BUDGET))
        final = optimizer.optimize("zzz")
        assert 3 not in final.compression.levels_used

    def test_compressor_called_once(self, context):
        calls: list[int] = []

        def compressor(sections, usable):
            calls.append(usable)
            return sections

        context.set(ContextScope.SYSTEM, "sys", "q" * 1600)  # P0 400
        context.set(ContextScope.EXECUTION, "node", "n" * 6000)  # P2 ~1502
        config = ContextOptimizerConfig(budget=SCENARIO_BUDGET, compressor=compressor,
                                        max_compression_level=3)
        optimizer = make_optimizer(context, config)
        optimizer.optimize("zzz " + "q" * 3988)  # total 2900 > 2800
        assert len(calls) == 1

    def test_compressor_retoken(self, context):
        def compressor(sections, usable):
            return [s.model_copy(update={"content": s.content * 2}) for s in sections]

        context.set(ContextScope.SYSTEM, "sys", "q" * 1600)
        config = ContextOptimizerConfig(budget=SCENARIO_BUDGET, compressor=compressor,
                                        max_compression_level=3)
        optimizer = make_optimizer(context, config)
        final = optimizer.optimize("zzz")
        assert final.total_tokens > 0  # re-tokenized after L3 (C2-05)

    def test_levels_1_3(self, context):
        def compressor(sections, usable):
            return sections

        # empty request -> L2 no-op; over budget (P2) -> L3 runs -> [1,3] (C2-11)
        context.set(ContextScope.SYSTEM, "sys", "q" * 8000)  # P0 2000
        context.set(ContextScope.EXECUTION, "node", "n" * 3600)  # P2 ~902
        config = ContextOptimizerConfig(budget=SCENARIO_BUDGET, compressor=compressor,
                                        max_compression_level=3)
        final = make_optimizer(context, config).optimize("")  # total ~2902 > 2800
        assert final.compression.levels_used == [1, 3]


# ---------------------------------------------------------------------------
# YC-6 — INV-012 budget & cut bottom-up
# ---------------------------------------------------------------------------

class TestBudget:
    def test_scenario_cut_order(self, context):
        """R1-2: usable 2800; seed 3700; per-tier drops P5 (600), total drops P6 (500)."""
        items = [
            candidate(MemoryKind.KNOWLEDGE, "k" * 2400, total=0.9, cid="k1"),   # P3 600
            candidate(MemoryKind.CONVERSATION, "m" * 3200, total=0.9, cid="m1"),  # P4 800
            candidate(MemoryKind.CONVERSATION, "h" * 2400, total=0.2, cid="h1"),  # P5 600
            candidate(MemoryKind.ARTIFACT, "a" * 2000, total=0.5, cid="a1"),    # P6 500
        ]
        context.set(ContextScope.SYSTEM, "sys", "s" * 1600)  # P0 400
        context.set(ContextScope.EXECUTION, "node", "n" * 2000)  # P2 500
        context.set(ContextScope.EXECUTION, "memory.context", make_memory_context(items=items))
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=SCENARIO_BUDGET))
        final = optimizer.optimize("q" * 1200)  # P1 300; term q*1200 never matches
        assert final.usable_budget == 2800
        assert final.total_tokens <= 2800
        tiers = {s.tier for s in final.sections}
        assert PriorityTier.P6_OPTIONAL not in tiers  # dropped by total cut
        assert PriorityTier.P5_HISTORICAL not in tiers  # dropped by per-tier cap
        assert PriorityTier.P4_MEMORY in tiers  # survived
        assert PriorityTier.P0_SYSTEM in tiers and PriorityTier.P1_USER in tiers
        assert final.truncated is True

    def test_per_tier_cap_drops_last_item(self, context):
        """Item-level (C1-01): 2 candidates same tier; cap cuts the last (lower score)."""
        items = [
            candidate(MemoryKind.KNOWLEDGE, "k" * 240 + "high", total=0.9, cid="high"),  # 61
            candidate(MemoryKind.KNOWLEDGE, "k" * 240 + "low", total=0.4, cid="low"),   # 61
        ]
        context.set(ContextScope.EXECUTION, "memory.context", make_memory_context(items=items))
        budget = MemoryBudget(system=400, task=500, knowledge=100, history=800,
                              artifacts=500, reserve=800)
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=budget))
        final = optimizer.optimize("")
        p3 = [s for s in final.sections if s.tier is PriorityTier.P3_KNOWLEDGE]
        assert len(p3) == 1
        assert p3[0].content == "k" * 240 + "high"  # higher score kept
        assert final.compression.dropped_by_budget >= 61

    def test_p0_exempt_from_cap(self, context):
        """P0 3600 > cap 3500 but P0+P1 <= usable 5900 -> kept whole (C1-02)."""
        context.set(ContextScope.SYSTEM, "sys", "s" * 14400)  # P0 3600
        budget = MemoryBudget(system=3500, task=500, knowledge=600, history=800,
                              artifacts=500, reserve=800)  # usable 5900
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=budget))
        final = optimizer.optimize("q" * 400)  # P1 100
        p0_report = [r for r in final.tier_reports if r.tier is PriorityTier.P0_SYSTEM][0]
        assert p0_report.used == 3600
        assert p0_report.used > (p0_report.cap or 0)  # reported, not cut
        assert [s.tier for s in final.sections].count(PriorityTier.P0_SYSTEM) == 1

    def test_p0p1_exceed_usable_raises(self, context):
        context.set(ContextScope.SYSTEM, "sys", "s" * 12000)  # P0 3000
        budget = MemoryBudget(system=400, task=500, knowledge=600, history=800,
                              artifacts=500, reserve=800)  # usable 2800
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=budget))
        with pytest.raises(ValueError, match="exceed usable budget"):
            optimizer.optimize("q" * 400)  # P1 100 -> P0+P1 3100 > 2800

    def test_enough_budget_no_truncation(self, context):
        context.set(ContextScope.SYSTEM, "sys", "s" * 400)  # P0 100
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=SCENARIO_BUDGET))
        final = optimizer.optimize("hi")
        assert final.truncated is False
        assert final.compression.dropped_by_budget == 0

    def test_section_over_cap_truncated_not_dropped(self, context):
        """C2-07: one huge execution state > cap -> truncated prefix, not dropped."""
        context.set(ContextScope.EXECUTION, "big", "b" * 20000)  # 5000 tokens
        budget = MemoryBudget(system=400, task=50, knowledge=600, history=800,
                              artifacts=500, reserve=800)
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=budget))
        final = optimizer.optimize("")
        p2 = [s for s in final.sections if s.tier is PriorityTier.P2_EXECUTION]
        assert len(p2) == 1  # still present (truncated)
        assert p2[0].content.endswith("…")
        assert p2[0].tokens <= 50

    def test_edge_two_tokens_over(self, context):
        """C2-14: after re-token, total exceeds usable by exactly 2 -> cut stops
        precisely (drops one small section, no over-cut)."""
        context.set(ContextScope.SYSTEM, "sys", "s" * 396)  # P0 99
        context.set(ContextScope.EXECUTION, "a", "x" * 8)  # P2 2
        context.set(ContextScope.EXECUTION, "b", "y" * 8)  # P2 2
        budget = MemoryBudget(system=400, task=100, knowledge=600, history=800,
                              artifacts=500, reserve=800)  # usable 2400
        optimizer = make_optimizer(context, ContextOptimizerConfig(budget=budget))
        final = optimizer.optimize("q" * 9192)  # P1 2298 -> total 99+2298+6 = 2403
        assert final.total_tokens <= 2400
        # exactly one 3-token section dropped (content includes "a: " prefix)
        assert final.compression.dropped_by_budget == 3


# ---------------------------------------------------------------------------
# YC-8 — Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_two_runs_identical(self, context):
        context.set(ContextScope.SYSTEM, "sys", "hello world")
        context.set(ContextScope.EXECUTION, "node", "n1")
        optimizer = make_optimizer(context)
        first = optimizer.optimize("hi there").model_dump()
        second = optimizer.optimize("hi there").model_dump()
        assert first == second


# ---------------------------------------------------------------------------
# YC-10 — Integration with MemoryCoordinator
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_memory_coordinator_to_optimizer(self, tmp_path, context):
        from aios_core.knowledge.embedder import Embedder
        from aios_core.knowledge.knowledge import KnowledgeMemory
        from aios_core.memory import (
            ArtifactSource,
            ConversationMemory,
            ConversationSource,
            KnowledgeSource,
            MemoryCoordinator,
            MemoryCoordinatorConfig,
            SessionSource,
        )
        from aios_core.contracts import ArtifactContract, ArtifactType
        from aios_core.kernel.events import EventBus
        from aios_core.kernel.services import ArtifactService

        class DummyEmbedder(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0]

        conversation = ConversationMemory(str(tmp_path / "conv.db"))
        conv_id = conversation.create_conversation("s1")
        conversation.add_message(conv_id, "user", "remember the oracle fix")
        knowledge = KnowledgeMemory(str(tmp_path / "k.db"))
        knowledge.index_text("doc-1", "oracle timezone knowledge", DummyEmbedder())
        artifacts = ArtifactService(str(tmp_path / "art"), EventBus())
        artifacts.store(ArtifactContract(
            id="art-1", name="oracle-patch", version="1.0.0", author="t",
            license="MIT", contract_version="1.0.0", schema_version="1.0.0",
            type=ArtifactType.PATCH, storage_path="p.md",
            metadata={"importance": 0.9}), b"x")

        coordinator = MemoryCoordinator(
            sources=[ConversationSource(conversation), SessionSource(context),
                     KnowledgeSource(knowledge, embedder=DummyEmbedder()),
                     ArtifactSource(artifacts)],
            context=context, clock=lambda: 1_800_000_000.0)
        # Default strategies = [HYBRID] (semantic+keyword+recency).
        coordinator.inject(MemoryQuery(text="oracle", session_id="s1"))
        # Conversation total = relevance 0.25 + importance 0.05 + sp 0.15 = 0.45
        # -> P4 needs threshold <= 0.45.
        optimizer = make_optimizer(context, ContextOptimizerConfig(relevant_threshold=0.4))
        final = optimizer.optimize("fix oracle")
        tiers = {s.tier for s in final.sections}
        assert PriorityTier.P4_MEMORY in tiers  # conversation
        assert PriorityTier.P3_KNOWLEDGE in tiers  # knowledge chunk
        assert PriorityTier.P6_OPTIONAL in tiers  # artifact
        assert final.total_tokens > 0


# ---------------------------------------------------------------------------
# INV-012 functional (behavioral enforcement)
# ---------------------------------------------------------------------------

def test_inv012_context_budget():
    context = ContextService()
    items = [
        candidate(MemoryKind.KNOWLEDGE, "k" * 2400, total=0.9),
        candidate(MemoryKind.CONVERSATION, "m" * 3200, total=0.9),
        candidate(MemoryKind.CONVERSATION, "h" * 2400, total=0.2),
        candidate(MemoryKind.ARTIFACT, "a" * 2000, total=0.5),
    ]
    context.set(ContextScope.SYSTEM, "sys", "s" * 1600)
    context.set(ContextScope.EXECUTION, "node", "n" * 2000)
    context.set(ContextScope.EXECUTION, "memory.context", make_memory_context(items=items))
    optimizer = ContextOptimizer(
        context=context, config=ContextOptimizerConfig(budget=SCENARIO_BUDGET),
        now=lambda: FIXED_NOW)
    final = optimizer.optimize("q" * 1200)
    assert final.total_tokens <= final.usable_budget  # INV-012: never over
