# TASK-053 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Bước Decide (governor) gọi 1 lần hay 2 lần mỗi vòng?
Loop vừa có bước Decide vừa "trước Act gọi governor" — 2 lần check/vòng?
→ **Resolve**: 1 lần/vòng: bước Decide = gọi `governor.check_action(...)`; kết quả quyết định có Act không. Không check thứ 2. Act chỉ chạy khi decision=CONTINUE. (AC2 đúng tinh thần — check trước Act.)

## C2-02 (P2) — Understand bước làm gì (deterministic)?
→ **Resolve**: understand = callable nhận (world snapshot, goal) → `dict` (analysis) — mặc định: đếm fact + trả `{fact_count, changed: bool}`. Deterministic.

## C2-03 (P3) — Plan bước trong loop có trùng AutonomousPlanner?
→ **Resolve**: loop nhận `planner` callable (mặc định = AutonomousPlanner từ TASK-051); mỗi vòng gọi plan() chỉ khi chưa có plan hoặc decision=REPLAN (tránh replan mỗi vòng).

## C2-04 (P3) — Learn chạy cả khi fail?
→ **Resolve**: learn luôn chạy cuối vòng (nhận VerificationResult — cả success lẫn fail); learner mặc định = noop (ghi vào AutonomousMemory TASK-057 sau).

## Kết luận
Resolve xong — spec đủ chặt để implement.
