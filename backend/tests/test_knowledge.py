"""Knowledge memory tests: chunking, indexing, search, re-index."""

import pytest

from aios_core.knowledge import ChunkResult, KnowledgeMemory, MockEmbedder


@pytest.fixture
def km(tmp_path):
    return KnowledgeMemory(str(tmp_path / "knowledge.db"))


@pytest.fixture
def embedder():
    return MockEmbedder()


def test_mock_embedder_deterministic_and_dim():
    e1 = MockEmbedder()
    e2 = MockEmbedder()
    v1, v2 = e1.embed("hello"), e2.embed("hello")
    assert v1 == v2  # cross-instance deterministic
    assert len(v1) == 32
    assert all(0.0 <= b <= 1.0 for b in v1)
    assert e1.embed("hello") != e1.embed("world")


def test_chunking_1000_chars(km, embedder):
    text = "a" * 1000
    n = km.index_text("src1", text, embedder)
    assert n == 3  # [0:500], [450:950], [900:1000]
    results = km.search("a" * 30, embedder, top_k=3)
    assert len(results) == 3
    assert set(r.chunk_index for r in results) == {0, 1, 2}
    # overlap: chunk[i+1][:50] == chunk[i][-50:] for chunks of len >= 500
    chunks = [r.text for r in sorted(results, key=lambda r: r.chunk_index)]
    assert chunks[1][:50] == chunks[0][-50:]
    assert len(chunks[0]) == 500
    assert len(chunks[1]) == 500
    assert len(chunks[2]) == 100  # last chunk truncated — accepted


def test_short_text_one_chunk(km, embedder):
    assert km.index_text("s", "short text", embedder) == 1


def test_empty_text_zero_chunks(km, embedder):
    assert km.index_text("s", "", embedder) == 0
    assert km.count() == 0


def test_reindex_replaces(km, embedder):
    text = "b" * 1000
    assert km.index_text("src1", text, embedder) == 3
    assert km.index_text("src1", "shorter", embedder) == 1
    assert km.count() == 1  # replaced, not duplicated


def test_search_returns_matching_chunk(km, embedder):
    km.index_text("doc", "apple banana cherry unique-phrase-xyz", embedder)
    results = km.search("unique-phrase-xyz", embedder, top_k=1)
    assert len(results) == 1
    assert results[0].source_id == "doc"
    assert "unique-phrase-xyz" in results[0].text
    assert isinstance(results[0], ChunkResult)
    assert results[0].score > 0


def test_search_top_k(km, embedder):
    km.index_text("d1", "one two three", embedder)
    km.index_text("d2", "four five six", embedder)
    results = km.search("one", embedder, top_k=1)
    assert len(results) == 1


def test_delete_source(km, embedder):
    km.index_text("d1", "aaaa bbbb", embedder)
    km.index_text("d2", "cccc dddd", embedder)
    assert km.count() == 2
    km.delete_source("d1")
    assert km.count() == 1
    # d1 gone: no result references it (results may still include d2 with low score)
    results = km.search("aaaa", embedder, top_k=5)
    assert all(r.source_id != "d1" for r in results)


def test_chunk_result_fields(km, embedder):
    km.index_text("doc", "hello world", embedder)
    result = km.search("hello world", embedder, top_k=1)[0]
    assert result.source_id == "doc"
    assert result.chunk_index == 0
    assert result.text == "hello world"
    assert isinstance(result.score, float)
