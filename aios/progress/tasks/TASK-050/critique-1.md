# TASK-050 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Success thresholds không rõ ngữ nghĩa
`goal.success: dict[str, float]` — không nói rõ đây là "giá trị mục tiêu" hay "threshold so sánh ≥". Nếu chỉ là threshold ≥ thì hợp lý v1, nhưng phải ghi rõ.
→ **Resolve**: spec làm rõ — `success` = map `metric → min_value` (đạt khi observed ≥ min_value). Ghi vào spec.

## C1-02 (P2) — Persist: lifecycle state machine có cần lưu transition history?
Nếu chỉ lưu state hiện tại thì không audit được chuỗi BLOCKED→RECOVERY→REPLANNING.
→ **Resolve**: v1 lưu state hiện tại + `history` (list state changes kèm timestamp) trong cùng row (JSON). Đủ để test chuỗi, không cần bảng riêng.

## C1-03 (P2) — Progress nguồn từ đâu?
GoalEngine không có khái niệm "task con" trong contract — progress tính thế nào?
→ **Resolve**: GoalContract có `steps: list[str]` (danh sách bước kế hoạch) + `completed_steps: int`; progress = completed_steps / len(steps). Engine cung cấp `mark_step_completed()`.

## C1-04 (P3) — ESCALATED → HUMAN: có quay lại được không?
Spec ghi ESCALATED là terminal. Một số hệ thống cho phép human approve → quay lại EXECUTING.
→ **Resolve**: giữ terminal v1 (human tạo goal mới nếu muốn tiếp tục — đơn giản, an toàn). Ghi chú trong spec.

## C1-05 (P3) — Event payload cần gì?
`autonomy.goal_state` cần payload đủ để observer biết trạng thái mới.
→ **Resolve**: payload = {goal_id, state, reason} (reason từ transition).

## Kết luận
3 P1/P2 chính đã resolve. Spec đủ để implement. Vòng 2 kiểm tra lại.
