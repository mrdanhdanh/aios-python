# Critique vòng 1 — TASK-007

## Đánh giá chung
Khung tốt, bám pattern TASK-004/006. Nhưng 4 P1 (chunk text không nơi lưu; get_messages limit tự mâu thuẫn; MockEmbedder hash() không cross-process; zero-vector ZeroDivisionError) + 8 P2 + 17 P3. **Sẵn sàng: 2.5/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — Chunk text không có nơi lưu → ChunkResult.text bất khả thi
- **Resolution**: tách `aios_core/knowledge/` (đúng PLAN): `chunks` table riêng (id PK, source_id, chunk_index, text) + VectorStore để trong memory (hạ tầng). search: vector search → join chunks table → ChunkResult.text. AC: search trả text đúng chunk.

### P1-2 — get_messages limit tự mâu thuẫn
- **Resolution**: ngữ nghĩa duy nhất: **luôn trả thứ tự tăng dần (created_at, rowid); limit set → limit message MỚI NHẤT rồi xếp tăng dần** (subquery DESC LIMIT → outer ASC). AC1 thêm test limit (kể cả limit > count → trả hết).

### P1-3 — MockEmbedder builtin hash() không ổn định cross-process
- **Resolution**: **bắt buộc `hashlib.sha256(text.encode("utf-8")).digest()`** → 32 bytes → vector 32 dim `[b/255 for b in digest]` (khoảng [0,1], ghi công thức). AC7: 2 instance khác nhau → cùng text → cùng vector.

### P1-4 — Zero-vector → ZeroDivisionError
- **Resolution**: validate **norm == 0 ở cả add lẫn search → ValueError** (không chỉ vector rỗng). AC3 thêm case zero-vector.

### P2 — (đặc tả)
1. **Re-index replace**: index_text cùng source_id → xóa chunks cũ (prefix `{source_id}:%`) trước khi insert; AC: index 2 lần → count = lần sau
2. **Chunk id scheme**: `id = f"{source_id}:{chunk_index}"` (deterministic, delete theo prefix)
3. **FK enforce**: `PRAGMA foreign_keys=ON` trong _connect; add_message conversation lạ → ValueError rõ (check trước); tie-break `ORDER BY created_at, rowid`
4. **Dim validate**: add check dim so store chuẩn → ValueError sớm; search check dim query vs store trước scan
5. **Search edge**: store rỗng → []; top_k > count → min(top_k, count); top_k ≤ 0 → ValueError
6. **Settings**: thêm `memory.knowledge_db_path: str = "aios/data/knowledge.db"` + config.yaml `memory:` (test cả 2 field)
7. **SessionMemory**: `set(key, value, ttl_s=None)` pass-through; nhận `clock` inject truyền xuống ContextService; default None (không hết hạn) ghi rõ
8. **Package**: tách `aios_core/knowledge/` (chunks, embedder, retriever) — đúng PLAN; VectorStore ở memory (hạ tầng)

### P3 — (áp)
1. id = uuid4() cho conversation/message; test unique
2. created_at = `datetime.now(timezone.utc).isoformat()`
3. clear_session namespace `session:` document; O(n) chấp nhận v1
4. wrapper nhận clock → test TTL không sleep
5. search tie-break `(-score, id)`
6. metadata JSON-serializable (default=str)
7. chunking: text rỗng → 0 chunk; chunk cuối < size chấp nhận (document)
8. delete id idempotent no-op
9. AC bổ sung: limit, zero-vector, search rỗng/top_k, re-index, conversation lạ, delete idempotent
10. AC6 query text unique (tránh tie 1.0)
11. AC5 thêm assert overlap chunks
12. AC7 vector khoảng [0,1]
13. `memory/__init__.py` export 6 class + `from . import memory` trong aios_core/__init__ + ChunkResult trong AC10
14. Out ghi: memory services không emit event (M2 Memory Coordinator)
15. Out ghi: v1 không wire memory vào RuntimeKernel (M2 dùng)
16. db_path relative resolve CWD
17. Out ghi: "conversation hiện tại" pointer → M2

## Kết luận
- [x] **Resolve toàn bộ (4 P1 + 8 P2 + 17 P3)** — cập nhật spec, chuyển critique vòng 2.
