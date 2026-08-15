# TASK-071 — Review (trước implement)

> Reviewer (tự). Review spec v2.

## Đánh giá
- Doctor 18 hạng mục đúng PLAN §M10-28; check thật (C1-01). ✅
- Score ổn định; không tạo DB rác (C2-01). ✅
- Additive — không phá CLI cũ. ✅

## Yêu cầu
1. **R1**: Mỗi hạng mục check thật (connect/query/instantiate) — không hard-code PASS.
2. **R2**: Không tạo DB file mới khi check (dùng settings paths; thiếu → WARN).
3. **R3**: `aiagent doctor` giữ output JSON cũ (thêm `first_class` field) — test cũ không vỡ.
4. **R4**: Score = round(100*pass/total).

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép implement.
