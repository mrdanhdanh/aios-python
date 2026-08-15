# TASK-034 — Pre-implementation Review

> File bổ sung hồi tố 2026-08-15 khi đóng hard gate (review ban đầu ghi trong LOG.md).

## Kết luận
**APPROVED có điều kiện** để implement Doctor & Readiness (M6-H5).

## Kiểm tra
- Phạm vi đúng M6-H5, nâng cấp `aiagent doctor` + `arch-health` thành Doctor Harness — không tạo Doctor mới hoàn toàn.
- Tái dụng Harness Kernel (H1) + DoctorChecks shared giữa doctor và readiness (không duplicate checks).
- Readiness không chỉ 1 con số: dimensions + hard gate (policy violation > 0 → RELEASE BLOCKED).
- UNKNOWN → 0.0 khi tính overall (fail-closed, không lạc quan giả).
- INV-018 Evidence First: persist TRƯỚC raise.

## Điều kiện bắt buộc khi implement
1. `DoctorChecks` shared (một instance) — doctor và readiness cùng dùng.
2. `ReadinessScorer` clamp score [0,1] + mean bỏ UNKNOWN→0.0.
3. Hard gate policy → overall (không cho overall cao che lấp vi phạm policy).
4. `DoctorHarness.kinds` validate subset — kind lạ → lỗi rõ.
5. Chạy full pytest trước khi đánh dấu done.

## Kết quả sau implement
- 1521 passed, coverage 95.35%, 11/11 AC — các điều kiện 1–5 đều thỏa (xem `test.md` + `evaluation.md`).
