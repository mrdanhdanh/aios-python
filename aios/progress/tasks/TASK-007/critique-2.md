# Critique vòng 2 — TASK-007

## Đánh giá chung
4 P1 + 8 P2 vòng 1 áp đúng hướng. Nhưng 1 P1 mới (storage topology chưa pin — chunks/vectors cùng file?) + 4 P2 (overlap assertion sai toán học; re-index delete chưa pin; SessionMemory constructor; role list) + 5 P3. **Sẵn sàng: 3/5 — sửa trước khi implement.**

## Vấn đề + Resolution

### P1 — Storage topology: chunks + vectors phải CÙNG file
- **Resolution**: `KnowledgeMemory(db_path)` khởi tạo `SQLiteVectorStore(db_path)` + `ChunksStore(db_path)` — cùng file `knowledge.db` (2 bảng `vectors` + `chunks`); `ChunksStore(db_path)` default `"aios/data/knowledge.db"` khớp MemorySettings; search join `WHERE id IN (...)` cùng connection.

### P2-1 — AC5 overlap assertion sai tổng quát (chunk áp chót cắt cụt)
- **Resolution**: pin thuật toán: chunk = `text[start:start+500]`, `start += 450`, dừng khi `start >= len(text)`; AC5 dùng text 1000 ký tự (L mod 450 = 100 ≥ 50 → 3 chunk đủ 500) + ghi chú: chunk áp chót cắt cụt → overlap containment, chấp nhận v1.

### P2-2 — Re-index: cơ chế xóa vectors + add trùng id
- **Resolution**: quy trình `index_text` re-index: (1) `SELECT id FROM chunks WHERE source_id=?` → (2) `vector_store.delete(id)` từng id cũ (idempotent) → (3) xóa + insert chunks → (4) add vectors mới; `add` id trùng → ValueError rõ (không upsert, không để IntegrityError lọt).

### P2-3 — SessionMemory constructor
- **Resolution**: pin `SessionMemory(context: ContextService, session_id: str)` — thuần wrapper, không tự tạo ContextService; bỏ "clock inject" ở SessionMemory (clock thuộc ContextService); test TTL dùng `ContextService(clock=fake)` truyền vào.

### P2-4 — Danh sách role
- **Resolution**: `role ∈ {"system", "user", "assistant"}` — ngoài → ValueError sớm; CHECK constraint cùng danh sách.

### P3 — (áp)
1. Search precedence: (1) top_k ≤ 0 → ValueError; (2) zero-vector → ValueError; (3) store rỗng → []; (4) dim mismatch → ValueError; (5) scan
2. Export: memory 4 class + knowledge 3 class = 7; `ChunkResult` dataclass ở `knowledge/knowledge.py`, re-export qua `knowledge/__init__.py`
3. Xóa theo cột: `DELETE FROM chunks WHERE source_id = ?` (không LIKE — tránh wildcard `_`/`%`); thứ tự: đọc ids → xóa vectors → xóa chunks
4. Out thêm: file parser/indexer theo loại file (PDF/web/docs) → M2

## Kết luận
- [x] **Resolve toàn bộ (1 P1 + 4 P2 + 5 P3)** — cập nhật spec, sẵn sàng implement.
