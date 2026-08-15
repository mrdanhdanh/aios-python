# TASK-066 — Review (trước implement)

> Reviewer (tự). Review spec v2.

## Đánh giá
- Durable Execution đúng PLAN §M10-13/14 (journal + verify-before-resume + idempotency). ✅
- Fail-closed (verify, non-idempotent) — an toàn cho autonomous. ✅
- Đo bằng event count (C1-01) — chống pass giả. ✅

## Yêu cầu
1. **R1**: KHÔNG sửa `kernel/services/execution.py` — journal là lớp tăng cường opt-in (wrapper qua node_runner).
2. **R2**: Mọi resume đều verify journal ↔ snapshot trước; lệch → JournalError.
3. **R3**: Idempotency fail-closed — op không khai báo = non_idempotent (không tự retry).
4. **R4**: Test crash-resume dùng event count (node 1–2 không chạy lại) + config test.

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép implement.
