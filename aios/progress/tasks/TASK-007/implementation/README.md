# TASK-007 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Conversation memory | `backend/src/aios_core/memory/conversation.py` |
| Session memory | `memory/session.py` (wrapper ContextService) |
| Vector store | `memory/vector.py` (cosine pure Python, SQLite) |
| Chunks store | `knowledge/chunks.py` (cùng file knowledge.db) |
| Embedder | `knowledge/embedder.py` (MockEmbedder sha256 → [0,1] 32-dim) |
| Knowledge memory | `knowledge/knowledge.py` (index/re-index/search/delete) |
| Settings | `config.py` (+MemorySettings), `config.yaml` |
| Tests (4 file mới) | `test_conversation.py`, `test_session.py`, `test_vector.py`, `test_knowledge.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- **Storage topology**: chunks + vectors CÙNG file `knowledge.db` (2 bảng) — search join bằng id
- **Vector id == chunk id** = `{source_id}:{chunk_index}` (re-index/delete_source dựa trên)
- **Chunking**: `text[start:start+500]`, start += 450 (chunk cuối cụt chấp nhận)
- **Re-index**: đọc ids cũ → delete vectors → replace chunks → add vectors mới
- **get_messages**: luôn tăng dần (created_at, id); limit = N mới nhất xếp tăng dần
- **MockEmbedder**: sha256 digest → [b/255] (ổn định cross-process, khoảng [0,1])
- **Search precedence**: top_k ≤ 0 → zero-vector → rỗng → dim → scan; không score threshold (trả top_k luôn)
