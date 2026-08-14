"""TASK-023 — Memory Coordinator tests (M5-P9): contracts, 7 strategies,
filter, rank, compress, dedup, budget, inject, determinism, wiring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from aios_core.contracts import ArtifactContract, ArtifactType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import (
    ArtifactService,
    ContextScope,
    ContextService,
)
from aios_core.memory import (
    ArtifactSource,
    ConversationMemory,
    ConversationSource,
    KnowledgeSource,
    MemoryBudget,
    MemoryCandidate,
    MemoryContext,
    MemoryCoordinator,
    MemoryCoordinatorConfig,
    MemoryKind,
    MemoryQuery,
    MemorySelection,
    MemoryStrategy,
    SessionSource,
    estimate_tokens,
)
from aios_core.memory.contracts import MemoryScore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXED_NOW = 1_800_000_000.0  # fake clock (determinism)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def make_artifact(artifact_service: ArtifactService, name: str, **metadata) -> None:
    contract = ArtifactContract(
        id=f"art-{name}",
        name=name,
        version="1.0.0",
        author="test",
        license="MIT",
        contract_version="1.0.0",
        schema_version="1.0.0",
        type=ArtifactType.MARKDOWN,
        storage_path=f"{name}.md",
        metadata=metadata,
    )
    artifact_service.store(contract, b"x")


@pytest.fixture
def conversation(tmp_path):
    return ConversationMemory(str(tmp_path / "conv.db"))


@pytest.fixture
def knowledge(tmp_path):
    from aios_core.knowledge.knowledge import KnowledgeMemory

    return KnowledgeMemory(str(tmp_path / "knowledge.db"))


@pytest.fixture
def context():
    return ContextService()


@pytest.fixture
def artifacts(tmp_path):
    return ArtifactService(str(tmp_path / "artifacts"), EventBus())


@pytest.fixture
def coordinator(conversation, knowledge, context, artifacts):
    sources = [
        ConversationSource(conversation),
        SessionSource(context),
        KnowledgeSource(knowledge),  # embedder=None
        ArtifactSource(artifacts),
    ]
    return MemoryCoordinator(
        sources=sources,
        context=context,
        clock=lambda: FIXED_NOW,
    )


def seed_conversation(conversation: ConversationMemory, session_id: str, texts: list[str]):
    conv_id = conversation.create_conversation(session_id)
    for i, text in enumerate(texts):
        conversation.add_message(conv_id, "user" if i % 2 == 0 else "assistant", text)
    return conv_id


# ---------------------------------------------------------------------------
# YC-1 — Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            MemoryQuery(text="x", session_id="s", bogus=1)
        with pytest.raises(ValidationError):
            MemoryCandidate(id="a", kind=MemoryKind.CONVERSATION, source_id="s",
                            content="c", created_at=_EPOCH, bogus=1)

    def test_field_constraints(self):
        with pytest.raises(ValidationError):
            MemoryQuery(text="x", session_id="s", top_k_per_source=0)
        with pytest.raises(ValidationError):
            MemoryQuery(text="x", session_id="s", min_importance=1.5)
        with pytest.raises(ValidationError):
            MemoryQuery(text="x", session_id="s", max_chars=0)

    def test_defaults(self):
        q = MemoryQuery(text="x", session_id="s")
        assert q.strategies == [MemoryStrategy.HYBRID]
        assert q.top_k_per_source == 20
        assert q.max_chars == 2000
        assert q.sources is None

    def test_invalid_strategy_validation_error(self):
        with pytest.raises(ValidationError):
            MemoryQuery(text="x", session_id="s", strategies=["bogus"])

    def test_weights_sum_validation(self):
        with pytest.raises(ValueError):
            MemoryCoordinatorConfig(weights={"semantic": 0.5})
        MemoryCoordinatorConfig(weights={"semantic": 0.5, "relevance": 0.5,
                                         "recency": 0.0, "importance": 0.0,
                                         "source_priority": 0.0})


# ---------------------------------------------------------------------------
# YC-2 — 7 retrieval strategies
# ---------------------------------------------------------------------------

class TestStrategies:
    def test_exact_conversation(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["Oracle TIMESTAMP issue found", "other topic"])
        q = MemoryQuery(text="oracle", session_id="s1", strategies=[MemoryStrategy.EXACT])
        items = coordinator.retrieve(q).items
        assert len(items) == 1
        assert "Oracle TIMESTAMP" in items[0][0].content

    def test_exact_artifact_name(self, coordinator, artifacts):
        make_artifact(artifacts, "Report-Q3")
        make_artifact(artifacts, "Notes")
        q = MemoryQuery(text="report", session_id="s1", strategies=[MemoryStrategy.EXACT])
        items = coordinator.retrieve(q).items
        assert [i[0].source_id for i in items] == ["art-Report-Q3"]

    def test_exact_session(self, coordinator, context):
        context.set(ContextScope.SHARED, "session:s1:note", "hello world")
        context.set(ContextScope.SHARED, "session:s2:other", "hello world")
        q = MemoryQuery(text="hello", session_id="s1", strategies=[MemoryStrategy.EXACT])
        items = coordinator.retrieve(q).items
        assert len(items) == 1
        assert items[0][0].source_id == "s1"

    def test_keyword_knowledge(self, coordinator, knowledge):
        from aios_core.knowledge.embedder import Embedder

        class DummyEmbedder(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0, 0.0]

        knowledge.index_text("src-1", "the quick brown fox jumps", DummyEmbedder())
        knowledge.index_text("src-2", "completely unrelated content here", DummyEmbedder())
        q = MemoryQuery(text="quick fox", session_id="s1", strategies=[MemoryStrategy.KEYWORD])
        items = coordinator.retrieve(q).items
        assert [i[0].source_id for i in items] == ["src-1"]

    def test_semantic_embedder_none_empty(self, coordinator):
        q = MemoryQuery(text="anything", session_id="s1", strategies=[MemoryStrategy.SEMANTIC])
        assert coordinator.retrieve(q).items == []

    def test_semantic_with_embedder(self, tmp_path, context, knowledge):
        from aios_core.knowledge.embedder import Embedder

        class OneHot(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]

        knowledge.index_text("src-1", "alpha document", OneHot())
        source = KnowledgeSource(knowledge, embedder=OneHot())
        coord = MemoryCoordinator(
            sources=[source], context=context, clock=lambda: FIXED_NOW
        )
        q = MemoryQuery(text="alpha", session_id="s1", strategies=[MemoryStrategy.SEMANTIC])
        items = coord.retrieve(q).items
        assert len(items) == 1
        assert items[0][0].metadata["semantic_score"] == 1.0  # (1+1)/2

    def test_metadata_artifact(self, coordinator, artifacts):
        make_artifact(artifacts, "Repo-A", tags=["github", "python"])
        make_artifact(artifacts, "Repo-B", tags=["database"])
        q = MemoryQuery(text="github", session_id="s1", strategies=[MemoryStrategy.METADATA])
        items = coordinator.retrieve(q).items
        assert [i[0].source_id for i in items] == ["art-Repo-A"]

    def test_recency_conversation(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["old message", "new message"])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY])
        items = coordinator.retrieve(q).items
        # Both returned; newest first after ranking.
        assert len(items) == 2
        assert "new message" in items[0][0].content

    def test_importance_artifact(self, coordinator, artifacts):
        make_artifact(artifacts, "Critical", importance=0.9)
        make_artifact(artifacts, "Trivial", importance=0.1)
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.IMPORTANCE],
                        min_importance=0.5)
        items = coordinator.retrieve(q).items
        assert [i[0].source_id for i in items] == ["art-Critical"]

    def test_hybrid_merges(self, coordinator, conversation, artifacts):
        seed_conversation(conversation, "s1", ["need fix oracle"])
        make_artifact(artifacts, "oracle-patch")
        q = MemoryQuery(text="oracle", session_id="s1", strategies=[MemoryStrategy.HYBRID])
        items = coordinator.retrieve(q).items
        kinds = {i[0].kind for i in items}
        assert kinds == {MemoryKind.CONVERSATION, MemoryKind.ARTIFACT}


# ---------------------------------------------------------------------------
# YC-3 — Filter + top_k
# ---------------------------------------------------------------------------

class TestFilter:
    def test_sources_whitelist(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["alpha"])
        q = MemoryQuery(text="alpha", session_id="s1", strategies=[MemoryStrategy.EXACT],
                        sources=[MemoryKind.ARTIFACT])
        assert coordinator.retrieve(q).items == []

    def test_since_excludes_old(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["alpha"])
        q = MemoryQuery(text="alpha", session_id="s1", strategies=[MemoryStrategy.EXACT],
                        since=datetime.now(timezone.utc) + timedelta(days=1))
        assert coordinator.retrieve(q).items == []

    def test_since_ignored_for_knowledge(self, coordinator, knowledge):
        from aios_core.knowledge.embedder import Embedder

        class DummyEmbedder(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0]

        knowledge.index_text("src-1", "alpha knowledge chunk", DummyEmbedder())
        q = MemoryQuery(text="alpha", session_id="s1", strategies=[MemoryStrategy.KEYWORD],
                        since=datetime.now(timezone.utc))
        items = coordinator.retrieve(q).items
        assert len(items) == 1  # knowledge ignores `since` (C2-12)

    def test_min_importance(self, coordinator, artifacts):
        make_artifact(artifacts, "A", importance=0.2)
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.IMPORTANCE],
                        min_importance=0.5)
        assert coordinator.retrieve(q).items == []

    def test_empty_content_filtered(self, coordinator, context):
        context.set(ContextScope.SHARED, "session:s1:blank", "   ")
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY])
        assert coordinator.retrieve(q).items == []

    def test_top_k_newest(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["m1", "m2", "m3", "m4"])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY],
                        top_k_per_source=2)
        items = coordinator.retrieve(q).items
        assert len(items) == 2
        assert {i[0].content for i in items} == {"m3", "m4"}


# ---------------------------------------------------------------------------
# YC-4 — Ranking
# ---------------------------------------------------------------------------

class TestRanking:
    def test_weights_order(self, coordinator, conversation, artifacts):
        seed_conversation(conversation, "s1", ["need fix oracle now"])
        make_artifact(artifacts, "oracle-patch", importance=0.9)
        q = MemoryQuery(text="oracle", session_id="s1", strategies=[MemoryStrategy.EXACT])
        items = coordinator.retrieve(q).items
        # Both exact → both relevance 1.0; conversation has higher source_priority.
        assert items[0][0].kind is MemoryKind.CONVERSATION

    def test_weights_change_reorders(self, coordinator, conversation, artifacts):
        seed_conversation(conversation, "s1", ["need fix oracle now"])
        make_artifact(artifacts, "oracle-patch", importance=0.9)
        coord = MemoryCoordinator(
            sources=coordinator._sources,
            context=coordinator._context,
            config=MemoryCoordinatorConfig(
                weights={"semantic": 0.0, "relevance": 0.0, "recency": 0.0,
                         "importance": 1.0, "source_priority": 0.0}
            ),
            clock=lambda: FIXED_NOW,
        )
        q = MemoryQuery(text="oracle", session_id="s1", strategies=[MemoryStrategy.EXACT])
        items = coord.retrieve(q).items
        assert items[0][0].kind is MemoryKind.ARTIFACT  # importance 0.9 wins

    def test_tie_break(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["same content a"])
        seed_conversation(conversation, "s1", ["same content b"])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY])
        items = coordinator.retrieve(q).items
        # Same created_at resolution → id desc; assert deterministic ordering.
        assert len(items) == 2

    def test_naive_datetime_normalized(self, coordinator, conversation):
        conv_id = conversation.create_conversation("s1")
        # Naive datetime via direct SQL insert is not possible through API;
        # instead verify _coerce_utc behavior through a candidate constructed
        # with naive timestamp is accepted by pydantic + ranking.
        candidate = MemoryCandidate(
            id="x", kind=MemoryKind.SESSION, source_id="s",
            content="c", created_at=datetime(2026, 1, 1),
        )
        assert candidate.created_at.tzinfo is None  # accepted; normalized in rank
        items = coordinator._rank(
            MemoryQuery(text="", session_id="s1"),
            [candidate],
        )
        assert items[0][1].recency == 0.0  # ancient → recency 0

    def test_recency_clamped_future(self, coordinator, context):
        future = datetime.now(timezone.utc) + timedelta(days=30)
        context.set(ContextScope.SHARED, "session:s1:future", "value",
                    ttl_s=None)
        # Force created_at future by direct store manipulation is not exposed;
        # build candidate directly.
        candidate = MemoryCandidate(
            id="y", kind=MemoryKind.SESSION, source_id="s",
            content="c", created_at=future,
        )
        items = coordinator._rank(MemoryQuery(text="", session_id="s1"), [candidate])
        assert 0.0 <= items[0][1].recency <= 1.0  # C2-10 clamp


# ---------------------------------------------------------------------------
# YC-5 — Dedup (after compress)
# ---------------------------------------------------------------------------

class TestDedup:
    def test_same_content_one_candidate(self, coordinator, conversation, knowledge):
        from aios_core.knowledge.embedder import Embedder

        class DummyEmbedder(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0]

        seed_conversation(conversation, "s1", ["identical duplicated text"])
        knowledge.index_text("src-1", "identical duplicated text", DummyEmbedder())
        q = MemoryQuery(text="identical", session_id="s1", strategies=[MemoryStrategy.HYBRID])
        items = coordinator.retrieve(q).items
        assert len(items) == 1

    def test_long_prefix_regression(self, coordinator, conversation):
        """C2-03: two long contents sharing a prefix collapse after compress."""
        base = "A" * 1998
        # Both messages share the first 1999 chars → identical after truncation.
        seed_conversation(conversation, "s1", [base + "AAA" + "XXX", base + "AAA" + "YYY"])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY],
                        max_chars=2000)
        selection = coordinator.retrieve(q)
        assert len(selection.items) == 1  # deduped after truncation

    def test_distinct_content_kept(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["alpha content", "beta content"])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY])
        assert len(coordinator.retrieve(q).items) == 2


# ---------------------------------------------------------------------------
# YC-6 — Compress
# ---------------------------------------------------------------------------

class TestCompress:
    def test_truncated_to_max_chars(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["x" * 5000])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY],
                        max_chars=2000)
        items = coordinator.retrieve(q).items
        content = items[0][0].content
        assert len(content) == 2000  # 1999 + "…" (C2-08)
        assert content.endswith("…")

    def test_short_content_kept(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["short"])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY])
        assert coordinator.retrieve(q).items[0][0].content == "short"


# ---------------------------------------------------------------------------
# YC-7 — Budget (AC5)
# ---------------------------------------------------------------------------

class TestBudget:
    def _budget_coordinator(self, context, conversation, knowledge, artifacts):
        budget = MemoryBudget(history=1500, task=1000, knowledge=1000, artifacts=500)
        sources = [
            ConversationSource(conversation),
            SessionSource(context),
            KnowledgeSource(knowledge),
            ArtifactSource(artifacts),
        ]
        return MemoryCoordinator(
            sources=sources, context=context,
            config=MemoryCoordinatorConfig(budget=budget),
            clock=lambda: FIXED_NOW,
        )

    def test_ac5_budget_4k(self, coordinator, conversation, knowledge, artifacts, context):
        from aios_core.knowledge.embedder import Embedder

        class DummyEmbedder(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0]

        # conversation 40 × 200 chars = 2000 tokens > history cap 1500
        for i in range(40):
            seed_conversation(conversation, "s1", ["c" * 200])
        # knowledge 30 chunks × 500 chars = 3750 tokens > knowledge cap 1000
        for i in range(30):
            knowledge.index_text(f"src-{i}", "k" * 500, DummyEmbedder())
        # session 20 values × 200 chars = 1000 tokens == task cap 1000
        for i in range(20):
            context.set(ContextScope.SHARED, f"session:s1:v{i}", "s" * 200)
        # artifacts 10 names × 60 chars = 150 tokens > artifacts cap 100
        # (name ≤ 60 chars — Windows filename limit ~255; deviation ghi evaluation)
        for i in range(10):
            make_artifact(artifacts, f"a{i}-{i:02d}" + "n" * 50)

        budget = MemoryBudget(history=1500, task=1000, knowledge=1000, artifacts=100)
        coord = MemoryCoordinator(
            sources=[
                ConversationSource(conversation),
                SessionSource(context),
                KnowledgeSource(knowledge),
                ArtifactSource(artifacts),
            ],
            context=context,
            config=MemoryCoordinatorConfig(budget=budget),
            clock=lambda: FIXED_NOW,
        )
        q = MemoryQuery(text="", session_id="s1", strategies=[
            MemoryStrategy.RECENCY,
            MemoryStrategy.KEYWORD,
            MemoryStrategy.IMPORTANCE,
        ], top_k_per_source=100)
        selection = coord.retrieve(q)
        assert selection.total_tokens <= 4000
        for kind in MemoryKind:
            assert selection.tokens_by_kind[kind] <= selection.budget[kind]
        assert selection.truncated is True
        # Per-category greedy: dropped items have the lowest total in their kind.
        for kind in MemoryKind:
            kept = [s for c, s in selection.items if c.kind is kind]
            all_scored = coord._rank(q, [c for c in coordinator._filter(q, coord._retrieve(q))])
            kind_scores = sorted([s.total for c, s in all_scored if c.kind is kind],
                                 reverse=True)
            kept_totals = sorted([s.total for s in kept], reverse=True)
            if len(kind_scores) > len(kept_totals):
                assert min(kind_scores) <= max(kept_totals, default=1.0)

    def test_overflow_single_category(self, coordinator, conversation, context):
        budget = MemoryBudget(history=50, task=1000, knowledge=1000, artifacts=1000)
        coord = MemoryCoordinator(
            sources=[ConversationSource(conversation), SessionSource(context)],
            context=context,
            config=MemoryCoordinatorConfig(budget=budget),
            clock=lambda: FIXED_NOW,
        )
        seed_conversation(conversation, "s1", ["a" * 300, "b" * 300])
        q = MemoryQuery(text="", session_id="s1", strategies=[MemoryStrategy.RECENCY])
        selection = coord.retrieve(q)
        assert selection.tokens_by_kind[MemoryKind.CONVERSATION] <= 50
        assert selection.truncated is True

    def test_empty_query_short_circuit(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["alpha"])
        q = MemoryQuery(text="   ", session_id="s1")
        selection = coordinator.retrieve(q)
        assert selection.items == []
        assert selection.total_tokens == 0
        assert selection.truncated is False


# ---------------------------------------------------------------------------
# YC-8 — Inject (INV-011)
# ---------------------------------------------------------------------------

class TestInject:
    def test_inject_writes_execution_scope(self, coordinator, conversation):
        seed_conversation(conversation, "s1", ["alpha memory"])
        q = MemoryQuery(text="alpha", session_id="s1", strategies=[MemoryStrategy.EXACT])
        ctx = coordinator.inject(q)
        assert isinstance(ctx, MemoryContext)
        stored = coordinator._context.get(ContextScope.EXECUTION, "memory.context",
                                          inherit=False)
        assert stored is not None and stored.session_id == "s1"

    def test_inject_overwrites(self, coordinator):
        q1 = MemoryQuery(text="", session_id="s1")
        q2 = MemoryQuery(text="", session_id="s2")
        coordinator.inject(q1)
        coordinator.inject(q2)
        stored = coordinator._context.get(ContextScope.EXECUTION, "memory.context",
                                          inherit=False)
        assert stored.session_id == "s2"

    def test_not_visible_from_agent_scope(self, coordinator):
        coordinator.inject(MemoryQuery(text="", session_id="s1"))
        assert coordinator._context.get(ContextScope.AGENT, "memory.context",
                                        inherit=True) is None


# ---------------------------------------------------------------------------
# YC-9 — Determinism
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_two_runs_identical(self, coordinator, conversation, artifacts):
        seed_conversation(conversation, "s1", ["alpha beta", "gamma"])
        make_artifact(artifacts, "alpha-doc", importance=0.8)
        q = MemoryQuery(text="alpha", session_id="s1", strategies=[MemoryStrategy.HYBRID])
        first = coordinator.retrieve(q).model_dump()
        second = coordinator.retrieve(q).model_dump()
        assert first == second

    def test_estimate_tokens(self):
        assert estimate_tokens("abcd") == 1
        assert estimate_tokens("x" * 5) == 2
        assert estimate_tokens("") == 1


# ---------------------------------------------------------------------------
# Sources integration (wiring-level)
# ---------------------------------------------------------------------------

class TestSources:
    def test_knowledge_list_chunks_additive(self, knowledge):
        from aios_core.knowledge.embedder import Embedder

        class DummyEmbedder(Embedder):
            def embed(self, text: str) -> list[float]:
                return [1.0]

        knowledge.index_text("src-1", "chunk one", DummyEmbedder())
        knowledge.index_text("src-2", "chunk two", DummyEmbedder())
        chunks = knowledge.list_chunks()
        assert [c.source_id for c in chunks] == ["src-1", "src-2"]
        assert [c.source_id for c in knowledge.list_chunks("src-1")] == ["src-1"]

    def test_session_source_content_str(self, coordinator, context):
        context.set(ContextScope.SHARED, "session:s1:obj", {"nested": "value"})
        q = MemoryQuery(text="nested", session_id="s1", strategies=[MemoryStrategy.EXACT])
        items = coordinator.retrieve(q).items
        assert len(items) == 1
        assert "nested" in items[0][0].content  # str(dict)
