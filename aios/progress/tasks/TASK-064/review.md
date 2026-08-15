# TASK-064 — Review (trước implement)

> Reviewer (tự). Review spec v2 sau critique ×2.

## Đánh giá spec v2

- Freeze 10 contract — phạm vi đúng PLAN §M10-7 (task quan trọng nhất M10). ✅
- Data-driven, additive, không breaking M1–M9 (AC9). ✅
- AC đo được: import thật (C1-01), source_version (C1-02), deprecated_reason (C1-03), blocking (C1-04), detector input rõ (C2-01). ✅

## Yêu cầu khi implement

1. **R1**: schema_ref PHẢI import được trong test (importlib) — không cho phép tên ảo.
2. **R2**: Không sửa contract hiện có; nếu phát hiện lệch giữa catalog và code → sửa catalog (data), không sửa code M1–M9.
3. **R3**: CLI output ổn định (dễ test string): padding cột cố định, status ký tự đơn (✓/⚠/✗).
4. **R4**: Full suite regression bắt buộc trước khi đánh dấu done.

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép implement.
