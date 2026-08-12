# TASK-007 — Breakdown checklist

## H1 — Memory package
- [ ] H1.1 `memory/conversation.py` — ConversationMemory (SQLite, FK, role CHECK, limit semantics)
- [ ] H1.2 `memory/session.py` — SessionMemory (wrapper ContextService)
- [ ] H1.3 `memory/vector.py` — VectorStore + SQLiteVectorStore (cosine, edge cases)
- [ ] H1.4 `memory/__init__.py` exports

## H2 — Knowledge package + Settings
- [ ] H2.1 `knowledge/chunks.py` — ChunksStore (cùng file knowledge.db)
- [ ] H2.2 `knowledge/embedder.py` — Embedder + MockEmbedder (sha256)
- [ ] H2.3 `knowledge/knowledge.py` — KnowledgeMemory + ChunkResult (index/re-index/search/delete)
- [ ] H2.4 `knowledge/__init__.py` + aios_core/__init__ + MemorySettings + config.yaml
- [ ] H2.5 test_import cập nhật

## H3 — Tests + Verify
- [ ] H3.1 test_conversation, test_session, test_vector, test_knowledge + test_config
- [ ] H3.2 pytest pass, coverage ≥ 80%, git sạch
- [ ] H3.3 Commit code + progress files + commit cuối
