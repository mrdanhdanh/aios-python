# Test — TASK-007

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Kết quả | **270 passed** (37 mới) |
| Coverage | **94.90%** (ngưỡng 80%) |
| Git sạch | ✅ |

Test mới: test_conversation (8), test_session (5), test_vector (13), test_knowledge (9) + test_config/test_import.

## Lỗi phát hiện + fix (4)
1. **`rowid` không khả dụng** trong ORDER BY (bảng TEXT PK) → tie-break `(created_at, id)`
2. **Thứ tự chunk trong search không đảm bảo** (query "a"*30 vs chunks khác nhau) → assert set thay vì thứ tự
3. **Không có score threshold** — search trả kết quả kể cả score thấp → test delete_source assert "không chứa d1" thay vì `[]`
4. **test_cancel_between_nodes flaky** (TASK-005 — race node 2 chạy trước flag set) → runner node 1 giữ event chờ cancel (deterministic)

## Đối chiếu AC (12 AC)
**12/12 PASS** — AC1 conversation (limit/role/FK), AC2 session TTL fake clock, AC3 vector edge (norm/dim/rỗng/top_k/dup/delete), AC4 cosine, AC5 chunking 1000→3 (500/500/100 + overlap), AC6 search text, AC7 embedder sha256 cross-instance, AC8 ChunkResult fields, AC9 settings, AC10 imports, AC11 offline, AC12 delete_source.

## Kết luận
- [x] **TẤT CẢ PASS (12/12 AC)** — sẵn sàng đánh giá cuối.
