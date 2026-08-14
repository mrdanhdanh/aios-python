"""Source adapters: bridge the coordinator to the four memory stores.

Duck-typed (structural Protocol): adapters receive store instances typed as
``Any`` so ``memory/`` never imports store packages (allow-list + cycle guard).
KnowledgeMemory is matched structurally — it must expose ``list_chunks()``
and optionally ``search(query, embedder, top_k)``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

from ..kernel.services import ContextScope, ContextService
from .contracts import MemoryCandidate, MemoryKind, MemoryQuery, MemoryStrategy

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_SESSION_PREFIX = "session:"


def _tokenize(text: str) -> set[str]:
    return set(text.lower().split())


def _overlap_ratio(query_text: str, content: str) -> float:
    """Keyword relevance: shared-term ratio over query terms (0..1)."""
    query_terms = _tokenize(query_text)
    if not query_terms:
        return 0.0
    content_terms = _tokenize(content)
    return len(query_terms & content_terms) / len(query_terms)


def _coerce_utc(value: datetime) -> datetime:
    """Normalize to tz-aware UTC; naive datetimes are assumed UTC (C2-06)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return _coerce_utc(parsed)


class MemorySource(Protocol):
    """Structural contract every store adapter implements."""

    kind: MemoryKind
    supported_strategies: frozenset[MemoryStrategy]

    def retrieve(
        self, query: MemoryQuery, strategy: MemoryStrategy
    ) -> list[MemoryCandidate]: ...


class ConversationSource:
    """Conversation memory (SQLite): exact / keyword / recency."""

    kind = MemoryKind.CONVERSATION
    supported_strategies = frozenset(
        {MemoryStrategy.EXACT, MemoryStrategy.KEYWORD, MemoryStrategy.RECENCY}
    )

    def __init__(self, conversation: Any) -> None:
        self._conversation = conversation

    def retrieve(
        self, query: MemoryQuery, strategy: MemoryStrategy
    ) -> list[MemoryCandidate]:
        candidates: list[MemoryCandidate] = []
        for conversation_id in self._conversation.list_conversations(query.session_id):
            for message in self._conversation.get_messages(conversation_id):
                content: str = message["content"]
                if strategy is MemoryStrategy.EXACT:
                    if query.text.lower() not in content.lower():
                        continue
                elif strategy is MemoryStrategy.KEYWORD:
                    if _overlap_ratio(query.text, content) <= 0:
                        continue
                # RECENCY keeps everything; filter/top_k happen upstream.
                candidates.append(
                    MemoryCandidate(
                        id=f"{self.kind.value}:{conversation_id}:{message['id']}",
                        kind=self.kind,
                        source_id=conversation_id,
                        content=content,
                        created_at=_parse_iso(message["created_at"]),
                        strategy_hits=[strategy],
                    )
                )
        return candidates


class SessionSource:
    """Session memory (ContextService SHARED + namespace prefix)."""

    kind = MemoryKind.SESSION
    supported_strategies = frozenset({MemoryStrategy.EXACT, MemoryStrategy.RECENCY})

    def __init__(self, context: ContextService) -> None:
        self._context = context

    def retrieve(
        self, query: MemoryQuery, strategy: MemoryStrategy
    ) -> list[MemoryCandidate]:
        prefix = f"{_SESSION_PREFIX}{query.session_id}:"
        candidates: list[MemoryCandidate] = []
        for key, value in self._context.get_all(ContextScope.SHARED).items():
            if not key.startswith(prefix):
                continue
            content = str(value)
            if strategy is MemoryStrategy.EXACT:
                if query.text.lower() not in content.lower():
                    continue
            entry = self._context.get_context(ContextScope.SHARED, key)
            created = entry.created if entry is not None else _EPOCH
            candidates.append(
                MemoryCandidate(
                    id=f"{self.kind.value}:{query.session_id}:{key}",
                    kind=self.kind,
                    source_id=query.session_id,
                    content=content,
                    created_at=created,
                    strategy_hits=[strategy],
                )
            )
        return candidates


class KnowledgeSource:
    """Knowledge memory (chunks + vectors): keyword / semantic.

    ``created_at`` is fixed at epoch (chunks carry no timestamp — C2-02), so
    recency is deterministically 0 and the ``since`` filter is skipped for
    knowledge (C2-12).
    """

    kind = MemoryKind.KNOWLEDGE
    supported_strategies = frozenset(
        {MemoryStrategy.KEYWORD, MemoryStrategy.SEMANTIC}
    )

    def __init__(self, knowledge: Any, embedder: Any = None) -> None:
        self._knowledge = knowledge
        self._embedder = embedder

    def retrieve(
        self, query: MemoryQuery, strategy: MemoryStrategy
    ) -> list[MemoryCandidate]:
        if strategy is MemoryStrategy.KEYWORD:
            candidates: list[MemoryCandidate] = []
            for chunk in self._knowledge.list_chunks():
                if _overlap_ratio(query.text, chunk.text) <= 0:
                    continue
                candidates.append(
                    MemoryCandidate(
                        id=f"{self.kind.value}:{chunk.source_id}:{chunk.id}",
                        kind=self.kind,
                        source_id=chunk.source_id,
                        content=chunk.text,
                        created_at=_EPOCH,
                        strategy_hits=[strategy],
                    )
                )
            return candidates
        if strategy is MemoryStrategy.SEMANTIC:
            if self._embedder is None:
                return []  # deterministic empty (no embedder wired)
            results = self._knowledge.search(
                query.text, self._embedder, top_k=query.top_k_per_source
            )
            return [
                MemoryCandidate(
                    id=f"{self.kind.value}:{hit.source_id}:{hit.chunk_index}",
                    kind=self.kind,
                    source_id=hit.source_id,
                    content=hit.text,
                    created_at=_EPOCH,
                    metadata={"semantic_score": (hit.score + 1.0) / 2.0},
                    strategy_hits=[strategy],
                )
                for hit in results
            ]
        return []


class ArtifactSource:
    """Artifact service (metadata only): exact / keyword / metadata / recency / importance."""

    kind = MemoryKind.ARTIFACT
    supported_strategies = frozenset(
        {
            MemoryStrategy.EXACT,
            MemoryStrategy.KEYWORD,
            MemoryStrategy.METADATA,
            MemoryStrategy.RECENCY,
            MemoryStrategy.IMPORTANCE,
        }
    )

    def __init__(self, artifacts: Any) -> None:
        self._artifacts = artifacts

    def retrieve(
        self, query: MemoryQuery, strategy: MemoryStrategy
    ) -> list[MemoryCandidate]:
        candidates: list[MemoryCandidate] = []
        for contract in self._artifacts.list():
            content = contract.name
            if strategy is MemoryStrategy.EXACT:
                if query.text.lower() not in content.lower():
                    continue
            elif strategy is MemoryStrategy.KEYWORD:
                if _overlap_ratio(query.text, content) <= 0:
                    continue
            elif strategy is MemoryStrategy.METADATA:
                haystack = json.dumps(
                    {**(contract.metadata or {}), "type": contract.type.value},
                    default=str,
                ).lower()
                if query.text.lower() not in haystack:
                    continue
            metadata = dict(contract.metadata or {})
            importance = float(metadata.get("importance", 0.5))
            candidates.append(
                MemoryCandidate(
                    id=f"{self.kind.value}:{contract.id}:{contract.name}",
                    kind=self.kind,
                    source_id=contract.id,
                    content=content,
                    created_at=_coerce_utc(contract.created),
                    importance=importance,
                    metadata=metadata,
                    strategy_hits=[strategy],
                )
            )
        return candidates
