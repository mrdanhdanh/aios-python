# TASK-050 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — `mark_step_completed` có validate step tồn tại không?
Nếu step không nằm trong `goal.steps`, engine có thể progress vượt 1.0 hoặc âm.
→ **Resolve**: `mark_step_completed` raise nếu step ∉ steps; progress = completed/len(steps), clamp [0,1]; completed > len → raise (invariant).

## C2-02 (P2) — Validate step có được phép ở mọi state?
`mark_step_completed` chỉ hợp lệ khi EXECUTING (hoặc RECOVERY).
→ **Resolve**: chỉ cho phép ở EXECUTING/REPLANNING/RECOVERY; state khác → raise `GoalLifecycleError`.

## C2-03 (P3) — transition reason bắt buộc?
→ **Resolve**: `transition(goal_id, target, reason)` — reason required (rỗng → mặc định "auto").

## C2-04 (P3) — `autonomy.level` validate bằng gì?
→ **Resolve**: enum `AutonomyLevel` (A0..A4) trong contracts — pydantic tự validate, không cần check tay.

## Kết luận
Resolve xong — spec đủ chặt để implement.
