# TASK-061 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Reset window khi nào?
→ **Resolve**: `reset(goal_id)` xóa window (gọi khi replan thành công / recovery — bắt đầu đo mới). detect() không reset (chỉ đọc).

## C2-02 (P2) — Threshold nào mặc định?
→ **Resolve**: REPEATED_TOOL_CALLS: ≥ 3 cùng tool; REPEATED_ERRORS: ≥ 3 cùng fingerprint; NO_STATE_CHANGE: ≥ 5 STATE_CHANGE nhưng state không đổi (chỉ 1 state duy nhất); NO_PROGRESS: ≥ 5 bước và progress không đổi; OSCILLATION: pattern 4-state liên tiếp; BUDGET_BURN: ≥ 3 BUDGET + 0 PROGRESS; CONTRADICTORY: ≥ 3 REPLAN. Injectable.

## C2-03 (P3) — detect trả counts?
→ **Resolve**: StuckReport(signals: list[str], counts: dict[str,int], verdict: "stuck"/"normal", window_size).

## Kết luận
Resolve xong — spec đủ chặt.
