# Evaluation — TASK-007

## Kết quả đối chiếu tiêu chí chấp nhận
**12/12 AC PASS** — 270 tests, coverage 94.90%.

## Đánh giá hệ thống tổng thể
- Critique ×2 bắt: chunk text không nơi lưu (tách knowledge/ package), get_messages limit tự mâu thuẫn, MockEmbedder hash() không cross-process, zero-vector crash, storage topology chưa pin (cùng file), overlap assertion sai toán học (chunk áp chót cắt cụt), re-index delete chưa pin.
- Reviewer bắt: AC5 "3 chunk đủ 500" bất khả thi toán học với step 450 (L=1000 → 500/500/100), vector id == chunk id chưa pin.
- Implement phát hiện: rowid không khả dụng, không score threshold (search luôn trả top_k), cancel test flaky từ TASK-005.
- **Memory 4 loại hoàn chỉnh**: Conversation (SQLite), Session (cache TTL), Knowledge (chunks + vectors cùng file), Artifact (đã có TASK-004). Knowledge pipeline offline-first với MockEmbedder sha256.

## Bài học (bổ sung STATS.md)
1. **Không có score threshold** trong vector search — semantics phải ghi rõ (trả top_k luôn); test không assert "search = []".
2. **rowid với TEXT PK** không dùng được trong ORDER BY — tie-break bằng (created_at, id).
3. **Overlap assertion phải tính trước toán học** — chunk step 450 → chunk cuối luôn cụt; assert theo len thực tế.
4. **Test cancel flaky cần runner giữ event** — đồng bộ hóa cửa sổ cancel giữa nodes.

## Kết luận
- [x] **ĐẠT spec (12/12 AC)** — P1 (Model + Memory + Knowledge) hoàn chỉnh. Sẵn sàng TASK-008 (Workflow Definition + Compilers) → P2.
