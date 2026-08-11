# Evaluation — TASK-005

## Kết quả đối chiếu tiêu chí chấp nhận
**15/15 AC PASS** — 207 tests pass, coverage 95.32%.

## Đánh giá hệ thống tổng thể
- Critique ×2 bắt: DI xung đột (`Path | str` không resolve), `timeout_s: int` mâu thuẫn test, resume thiếu plan, runner contract thiếu định nghĩa, stale cancel flag, `_safe_deepcopy` fallback sai phạm vi.
- Reviewer verify DI-safe từng service với container thật + bắt 2 R1 clarification (cancel check order, thiếu register EventBus).
- Implement phát hiện 5 lỗi thật, quan trọng nhất: **string annotations (future import) phá DI container** — fix `get_type_hints`; **exception trong timeout-thread bị nuốt** → sai kết quả thành công.
- **Runtime Kernel HOÀN CHỈNH 9 services + RuntimeKernel wiring** — ExecutionService end-to-end chạy plan với policy + resources + events + snapshot/resume.

## Bài học (bổ sung STATS.md)
1. **`from __future__ import annotations` biến annotation thành string** — DI container phải dùng `typing.get_type_hints` để resolve (không dùng `param.annotation` thô)
2. **Exception trong thread bị nuốt im** — thread target phải capture error vào box, re-raise ở main thread
3. **Runner contract phải định nghĩa từ spec** — signature, lỗi, số lần gọi — tránh 5 kiểu implement khác nhau
4. **Cancel-before-execute cần pending flag đăng ký sẵn** — không thể no-op cho unknown id
5. **Deepcopy fallback per-value** — fallback cả container biến dict thành string

## Kết luận
- [x] **ĐẠT spec (15/15 AC)** — P0.5 Runtime Kernel hoàn chỉnh. Sẵn sàng TASK-006 (Models) + TASK-007 (Memory + Knowledge) → P1.
