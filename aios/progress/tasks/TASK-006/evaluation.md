# Evaluation — TASK-006

## Kết quả đối chiếu tiêu chí chấp nhận
**13/13 AC PASS** — 233 tests, coverage 94.73%.

## Đánh giá hệ thống tổng thể
- Critique ×2: bắt registry không DI-safe (phải wire RuntimeKernel), OpenAI thiếu injection seam, Ollama chat không timeout, thứ tự check chat() với fake client, mâu thuẫn Yêu cầu #6 stale, patch target chưa pin.
- Reviewer: APPROVED có điều kiện — verify RuntimeKernel thêm ModelRegistry không phá TASK-005 (container/extra-forbid/import graph).
- Implement phát hiện 4 lỗi thật (monkeypatch 2-arg pattern, patch target module-level, fake client shape, fixed vs sequence).
- **Nền Simulation Mode hoàn chỉnh**: MockModel offline + ModelRegistry default "mock" — M2 sẽ dùng để chạy không LLM.

## Bài học (bổ sung STATS.md)
1. **Patch target phải là attribute module-level** — `from urllib.request import urlopen` rồi test `setattr(module, "urlopen", fake)`; 2-arg setattr khác 3-arg.
2. **Injection seam ngay từ spec** — `client: Any | None` + quy tắc bypass rõ (explicit client không cần is_available).
3. **"Fixed" vs "sequence" phải định nghĩa hành vi hết-danh-sách** — fixed lặp vô hạn, sequence raise exhausted.
4. **monkeypatch.delenv** cho env var provider (OPENAI_API_KEY) — determinism test trên máy có env.

## Kết luận
- [x] **ĐẠT spec (13/13 AC)** — TASK-006 done. Sẵn sàng TASK-007 (Memory 4 loại + Knowledge pipeline).
