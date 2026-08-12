# Review — TASK-007 (Pre-Implementation)

## Tổng quan
Spec pin rất kỹ (storage topology, re-index, SessionMemory ctor, search precedence — đều khớp code nền). **CHANGES REQUESTED: 1 R1 blocking (lỗi toán học AC5) + 2 R2 + 6 R3.**

## Vấn đề + Resolution

### R1 — AC5 "3 chunk đủ 500" bất khả thi với thuật toán đã pin (Blocking)
- Vấn đề: L=1000 với step 450 → chunk [0:500], [450:950], [900:1000] = **500/500/100** — chunk cuối luôn cụt; "3 chunk đủ 500" không tồn tại (cần L ≥ 1400 thì lại sinh chunk 4).
- **Resolution**: AC5 sửa: "text 1000 ký tự → 3 chunk: [0:500], [450:950], [900:1000]; chunk 1–2 len 500, chunk 3 len 100 (cụt — chấp nhận); assert overlap `chunks[i+1][:50] == chunks[i][-50:]` với chunk i len ≥ 500".

### R2-1 — Vector id == chunk id chưa pin
- **Resolution**: pin: "vector id = chunk id = `{source_id}:{chunk_index}` khi index_text/add" (bắt buộc — re-index/delete_source dựa trên đó).

### R2-2 — Default db_path ConversationMemory/SQLiteVectorStore chưa pin
- **Resolution**: `ConversationMemory(db_path="aios/data/conversations.db")`; `SQLiteVectorStore(db_path)` — **bắt buộc truyền (không default)** (hạ tầng chung).

### R3 — (áp khi implement)
1. KnowledgeMemory.search: tự mở 1 connection, query vectors + chunks `WHERE id IN (...)` rồi sắp xếp theo score (cùng FILE — không cần cùng connection object)
2. VectorStore/ChunksStore mkdir parent (pattern EventService)
3. `from . import memory, knowledge` đặt CUỐI aios_core/__init__ + thêm vào `__all__`; cấm absolute import trong memory/knowledge; thêm `models` vào `__all__` (thiếu từ TASK-006)
4. tasks.md ghi chú AC vào từng item
5. test_config an toàn (đã verify guard động)
6. ContextService SHARED + clock inject tồn tại (đã verify)

## Kết luận
- [x] **Resolve toàn bộ (1 R1 + 2 R2 + 6 R3)** — spec + tasks.md cập nhật, sẵn sàng implement.
