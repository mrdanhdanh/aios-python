# Evaluation — TASK-008

## Kết quả đối chiếu tiêu chí chấp nhận
**10/10 AC PASS** — 300 tests, coverage 94.92%. **Deliverable M1 đạt**: `aiagent run workflow.yaml --simulate` chạy thật.

## Đánh giá hệ thống tổng thể
- Critique ×2: bắt deliverable M1 không chủ (YAML/CLI), định danh không nhất quán (canonical name), "retries=0 = vô hạn" SAI engine, type/extra chưa pin, CLI test pattern.
- Reviewer: APPROVED — verify 270 baseline + policy + merge khớp engine + refactor an toàn (không test assert full message).
- Implement phát hiện **bug ẩn thật**: rò connection SQLite từ TASK-004/007 (pattern `with conn` không đóng) — WinError 32; fix 16 chỗ bằng `contextlib.closing`.
- **Workflow Definition declarative + MockCompiler + Library + CLI** — engine-agnostic đúng PLAN; LangGraph stub sẵn chỗ cắm M2.

## Bài học (bổ sung STATS.md)
1. **`with sqlite3.connect() as conn` KHÔNG đóng connection** — chỉ commit/rollback; phải `contextlib.closing` + `, conn` — bug ẩn gây WinError khi xóa file.
2. **Deliverable milestone phải có chủ trong spec** — YAML loader + CLI bị bỏ quên (ai cũng nghĩ người khác làm) — critique bắt kịp.
3. **Semantics phải đối chiếu engine code** — "retries=0 vô hạn" nghe hợp lý nhưng engine `attempts = 1 + retries`.
4. **CLI test gọi main() trực tiếp + monkeypatch sys.argv** — deterministic hơn subprocess.

## Kết luận
- [x] **ĐẠT spec (10/10 AC)** — sẵn sàng TASK-009 (Capability + Prompt Registry + Catalog + Knowledge Graph) → hết M1.
