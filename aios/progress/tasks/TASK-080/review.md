# TASK-080 — Review (trước implement)

> Đánh giá spec + critique đã resolve, sắp xếp thứ tự implement.

## Kết quả review
- **Spec**: rõ mục tiêu, phạm vi, AC (AC1–AC6). ✅
- **Critique ×2**: vòng 1 (5 issue, 3 P1) + vòng 2 (3 issue, 0 P1) — tất cả đã resolve. ✅
- **Thứ tự implement**: T3 (agent-sprite-forge) → T4 (pixel-game-dev) → T5 (catalog) → T6 (README) → T7 (test) → T8/T9 (log/commit).

## Ghi chú
- Giữ script `generate2dsprite.py` **deterministic & cô đọng** (không copy nguyên bộ upstream ~1000 dòng). Đủ để minh họa AC3.
- Không thay đổi code backend; chỉ thêm artifact file-based.

## Quyết định
**APPROVED** — được phép implement.
