# Evaluation — TASK-009

## Kết quả đối chiếu tiêu chí chấp nhận
**9/9 AC PASS** — 346 tests, coverage 95.30%.

## Đánh giá hệ thống tổng thể
- Critique ×2 bắt: Prompt regex {{}} false positive + format spec miss, duplicate overwrite phá versioning, evaluate write-only, mâu thuẫn PLAN (SQLite/populate), neighbors self-loop, validation algorithm brace.
- Implement phát hiện 5 lỗi thật (fixture conflict, self-loop unpack, in-index đảo biến, integration relation, thread id trùng).
- **M1 HOÀN TẤT**: 9 tasks, 346 tests, coverage 95.3%, deliverable `aiagent run workflow.yaml --simulate` chạy được. Toàn bộ nền Core Runtime: kernel 9 services + contracts + models + memory + knowledge + workflow + capability + prompt + catalog + knowledge graph.

## Bài học (bổ sung STATS.md)
1. **Tên biến unpack phải khớp ngữ nghĩa index** — in-index lưu (rel, source_kind, source_id): đặt tên `_sk, source_id`, không dùng tk/ti chung.
2. **Fixture tên ngắn dễ conflict** — g/cat thiếu tham số → FixtureFunctionDefinition; tên rõ + tham số tường minh.
3. **Thread-safe test: id phải unique theo thread** — agent-{i} × 2 thread = 50 unique không phải 100.
4. **Regex lookaround + scan escape-first** — validate template lúc construct (object hỏng không tồn tại).

## Kết luận
- [x] **ĐẠT spec (9/9 AC)** — **M1 Core Runtime HOÀN THÀNH.** Sẵn sàng M2 (Developer Edition: Orchestrator v1 + Assistants).
