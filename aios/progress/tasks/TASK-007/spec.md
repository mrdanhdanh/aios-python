# TASK-007 — M1/P1b: Memory 4 loại + Knowledge pipeline

## Mục tiêu
Xây hệ thống Memory theo PLAN (4 loại): Conversation (SQLite), Knowledge (vector store SQLite-backed), Session (in-memory cache), Artifact (filesystem — đã có ArtifactService TASK-004, tích hợp ref). Kèm Knowledge pipeline: indexer → chunks → embeddings → store → retriever. Offline-first: vector store thuần Python (cosine similarity), embeddings pluggable (Mock embedder mặc định).

## Phạm vi
- **In**:
  - `aios_core/memory/` (4 loại + hạ tầng vector):
    1. `conversation.py` — `ConversationMemory(db_path="aios/data/conversations.db")`: SQLite (id uuid4, conversation_id FK enforced `PRAGMA foreign_keys=ON`, role CHECK, created_at ISO-8601 UTC); `create_conversation(session_id) -> id`, `add_message(conversation_id, role, content)` (conversation lạ → ValueError; tie-break rowid), `get_messages(conversation_id, limit=None)` — **luôn tăng dần; limit = N message mới nhất xếp tăng dần (subquery DESC LIMIT → outer ASC)**, `list_conversations(session_id)`; connection-per-call + busy_timeout + mkdir
    2. `session.py` — `SessionMemory(context: ContextService, session_id: str)` — thuần wrapper (không tự tạo ContextService; clock thuộc ContextService); scope=SHARED, key `session:{session_id}:{key}` (namespace riêng); `set(key, value, ttl_s=None)` pass-through, `get/delete`, `clear_session()` (quét prefix O(n) chấp nhận v1)
    3. `vector.py` — `VectorStore` interface + `SQLiteVectorStore(db_path)` (**bắt buộc truyền db_path — không default; hạ tầng chung**; table `vectors`: id PK, vector JSON, metadata JSON): `add` (validate dim so store chuẩn; **norm==0 → ValueError; id trùng → ValueError rõ — không upsert, không để IntegrityError lọt**; metadata JSON-serializable default=str; mkdir parent), `search` (**precedence: 1) top_k ≤ 0 → ValueError; 2) zero-vector/norm==0 → ValueError; 3) store rỗng → []; 4) dim mismatch → ValueError; 5) scan**; cosine = dot/(norm_a*norm_b); tie-break (-score, id); scan O(n) v1), `delete` (idempotent), `count()`
  - `aios_core/knowledge/` (đúng PLAN — pipeline):
    4. `chunks.py` — `ChunksStore(db_path: str = "aios/data/knowledge.db")`; table `chunks(id PK = f"{source_id}:{chunk_index}", source_id, chunk_index, text)`; add/get/replace/delete_by_source (**xóa theo cột `WHERE source_id = ?` — KHÔNG LIKE, tránh wildcard `_`/`%`**)
    5. `embedder.py` — `Embedder` protocol: `embed(text) -> list[float]`; `MockEmbedder`: **`hashlib.sha256(text.encode()).digest()` → 32 bytes → `[b/255 for b in digest]` (khoảng [0,1]) — ổn định mọi process**
    6. `knowledge.py` — `KnowledgeMemory(db_path)`: khởi tạo `SQLiteVectorStore(db_path)` + `ChunksStore(db_path)` — **CÙNG file knowledge.db (2 bảng vectors + chunks)**; **vector id = chunk id = `{source_id}:{chunk_index}` (bắt buộc — re-index/delete_source dựa trên đó)**; `index_text(source_id, text, embedder)` — chunk **`text[start:start+500]`, start += 450, dừng khi start >= len(text)`** (text rỗng → 0 chunk; chunk cuối < size chấp nhận); **re-index: (1) SELECT id FROM chunks WHERE source_id=? → (2) vector_store.delete(id) từng cái → (3) xóa + insert chunks → (4) add vectors mới**; `search(query, embedder, top_k=5) -> list[ChunkResult(source_id, chunk_index, text, score)]` (**tự mở 1 connection: query vectors + chunks `WHERE id IN (...)` rồi sắp xếp lại theo score**); `delete_source(source_id)` (đọc ids → xóa vectors → xóa chunks); **`ChunkResult` dataclass khai báo ở knowledge.py, re-export qua knowledge/__init__**
    7. `__init__.py` exports (memory: 4 class — ConversationMemory, SessionMemory, VectorStore, SQLiteVectorStore; knowledge: 3 class — KnowledgeMemory, MockEmbedder, ChunkResult; tổng 7) + `from . import memory, knowledge` trong aios_core/__init__
    8. Settings: `MemorySettings(conversation_db_path="aios/data/conversations.db", knowledge_db_path="aios/data/knowledge.db")` + config.yaml `memory:` (relative resolve CWD)
    9. Tests: test_conversation, test_session, test_vector, test_knowledge (4 file)
- **Out (không làm)**: ChromaDB/FAISS (interface swap sau), real embeddings API (M2), memory pruning/compaction, RAG prompt integration (M2), conversation pointer ("conversation hiện tại" → M2 Memory Coordinator), **memory services không emit event (M2)**, **v1 không wire memory vào RuntimeKernel (M2 Orchestrator dùng)**, **file parser/indexer theo loại file (PDF/web/docs) → M2**

## Yêu cầu chi tiết
1. **ConversationMemory**: id uuid4; created_at `datetime.now(timezone.utc).isoformat()`; **role ∈ {"system", "user", "assistant"} — ngoài → ValueError sớm + CHECK constraint cùng danh sách (defense-in-depth)**; FK enforced; get_messages semantics đã pin (tăng dần, limit = N mới nhất)
2. **SessionMemory**: wrapper ContextService scope=SHARED + prefix `session:`; `set(key, value, ttl_s=None)` (None = không hết hạn — nhất quán TASK-004); clock inject truyền xuống
3. **VectorStore**: như Phạm vi #3 (norm==0 validate cả 2 chiều; dim check add + search sớm; search edge cases)
4. **Knowledge pipeline**: chunk size 500/overlap 50; text rỗng → 0 chunk; re-index replace (chunks + vectors xóa prefix trước); chunk id `{source_id}:{chunk_index}`; MockEmbedder sha256 → [0,1]
5. Mọi service nhận db_path/clock qua constructor (test tmp_path); mọi test offline; coverage ≥ 80%
6. Settings: `MemorySettings` + config.yaml (pattern TASK-004/006); relative resolve CWD

## Input / Output
- Input: TASK-002 (Settings pattern), TASK-004 (ContextService, SQLite pattern), TASK-006 (metadata)
- Output: memory/ + knowledge/ packages + tests + Settings + commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: ConversationMemory: create/add/get/list; **get_messages limit (N mới nhất, tăng dần; limit > count → hết)**; role sai → ValueError; **conversation lạ → ValueError**; id unique; db auto-create (có test)
- [ ] AC2: SessionMemory: set/get/delete + clear_session; TTL với fake clock (có test)
- [ ] AC3: VectorStore: add/search/delete/count; search top_k đúng thứ tự; **vector rỗng + zero-vector → ValueError (cả add lẫn search)**; dim mismatch add → ValueError sớm; **search rỗng → []; top_k > count → min; top_k ≤ 0 → ValueError**; delete idempotent (có test)
- [ ] AC4: Cosine: giống nhau → 1.0; trực giao → ~0 (có test)
- [ ] AC5: index_text: text 1000 ký tự → 3 chunk [0:500], [450:950], [900:1000] (chunk 1–2 len 500, chunk 3 len 100 cụt — chấp nhận; assert overlap `chunks[i+1][:50] == chunks[i][-50:]` với chunk i len ≥ 500); ngắn → 1; **re-index cùng source → count = lần sau (replace)**; text rỗng → 0 chunk (có test)
- [ ] AC6: search: query khớp chunk (text unique tránh tie) → top 1; top_k đúng; **ChunkResult có text đúng** (có test)
- [ ] AC7: MockEmbedder: **2 instance cùng text → cùng vector (sha256, [0,1])**; dim 32; text khác → vector khác (có test)
- [ ] AC8: ChunkResult đủ field (source_id, chunk_index, text, score) (có test)
- [ ] AC9: Settings.memory: conversation_db_path + knowledge_db_path load từ config.yaml + default (test_config)
- [ ] AC10: pytest pass + coverage ≥ 80%; test_import: `from aios_core.memory import ConversationMemory, SessionMemory, VectorStore, SQLiteVectorStore` + `from aios_core.knowledge import KnowledgeMemory, MockEmbedder, ChunkResult` pass
- [ ] AC11: Mọi test tmp_path + offline — git sạch
- [ ] AC12: delete_source(source_id) xóa cả chunks + vectors (có test)

## Phụ thuộc
- TASK-002 (Settings), TASK-004 (ContextService, SQLite pattern), TASK-006 (metadata)
- Không dep mới (stdlib sqlite3/math/hashlib)

## Rủi ro
- R1: Cosine scan O(n) chậm với data lớn → v1 local nhỏ, interface để swap FAISS sau (ghi chú)
- R2: JSON vector trong SQLite lớn → dim nhỏ v1 (32), document
- R3: Chunking đơn giản (ký tự) có thể cắt giữa câu → M2 nâng cấp chunker (ghi chú)
