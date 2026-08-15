# TASK-063 — Review (M10-F1, trước implement)

> Reviewer (tự — subagent không phản hồi, tiền lệ TASK-031). Review spec v2 sau critique ×2.

## Đánh giá spec v2 (M10-F1)

- Phạm vi rõ: docs-only, 6 file mới + cập nhật v2, không đụng code/PLAN. ✅
- AC đo được: AC3/AC4 script đối chiếu INV (34 invariant) với test_architecture.py — ngăn "invariant trên giấy". ✅
- Vai trò từng file tách bạch (C1-02): không lặp bảng milestone/task của v2. ✅
- Freeze tuyên bố rõ ràng + hệ quả (C2-03): Gate A + ADR + AIOS 2.0. ✅

## Yêu cầu khi implement

1. **R1**: Script test phải chạy THẬT (node/python) — không chỉ đọc tay; ghi kết quả vào test.md.
2. **R2**: Mọi nhãn INV trong constitution phải khớp nhãn enforcement thực tế (`test_inv0xx_*` / `test_m9_*`); nếu lệch → sửa tài liệu, không sửa test.
3. **R3**: Không tuyên bố tính năng chưa làm (conformance/release gates = planned TASK-073; kill switch = TASK-068; security baseline = TASK-070).
4. **R4**: Giữ markdown thuần (không ```mermaid) — đồng nhất v1.

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép tạo docs/architecture/* + constitution-1.0.md + cập nhật v2.
