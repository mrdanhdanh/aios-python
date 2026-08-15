# TASK-033 — Pre-implementation Review

> File bổ sung hồi tố 2026-08-15 khi đóng hard gate (review ban đầu ghi trong LOG.md).

## Kết luận
**APPROVED có điều kiện** để implement Benchmark + Regression Gate (M6-H4).

## Kiểm tra
- Phạm vi đúng M6-H4 (Benchmark + Regression Gate), không kéo Doctor vào task.
- Tái dụng Harness Kernel (H1): `BenchmarkHarness` kế thừa runner/lifecycle/evidence chung — không xây hệ thống thứ hai.
- Deterministic: baseline==0 → delta 0; baseline rỗng → không block; epsilon boundary — tránh flaky.
- INV-021 Release Gate: gate fail → `GateBlockedError` persist TRƯỚC raise (evidence-first).
- 3 default rules hướng xấu đúng chiều (quality giảm = xấu; failure_rate/violations tăng = xấu) — % vs pp delta phân biệt rõ.

## Điều kiện bắt buộc khi implement
1. `BenchmarkRunner.run_fn` injectable (không gọi ExecutionService trực tiếp).
2. `RegressionGate.can_release` đúng với subset chung (scenario không trong baseline bỏ qua).
3. `GateBlockedError` phải kế thừa `BenchmarkError` để caller bắt 1 ngoại lệ.
4. strict=False → WARNING không raise (không phá harness chạy thăm dò).
5. Chạy full pytest trước khi đánh dấu done.

## Kết quả sau implement
- 1450 passed, coverage 95.31%, 11/11 AC — các điều kiện 1–5 đều thỏa (xem `test.md` + `evaluation.md`).
