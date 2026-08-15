# TASK-061 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Window cấu trúc thế nào?
→ **Resolve**: `record(event_type, goal_id, detail)` — event_type ∈ {TOOL_CALL, ERROR, STATE_CHANGE, PROGRESS, REPLAN, BUDGET}; detail dict (tool_id/error_fp/state/progress/reason). Window = deque bounded (window_size injectable, mặc định 20) per goal_id.

## C1-02 (P2) — Oscillation detect thuật toán?
→ **Resolve**: chỉ xét STATE_CHANGE events: chuỗi state ids; pattern A→B→A→B: duyệt window tìm 2 cặp đối xứng liên tiếp (i,i+1) == (i+2,i+3) → OSCILLATION. Cụ thể: tồn tại i sao cho states[i]==states[i+2] and states[i+1]==states[i+3].

## C1-03 (P2) — Budget burn rate?
→ **Resolve**: BUDGET events ghi (cost, steps); burn = cost tăng trong window mà PROGRESS không tăng → signal. V1: nếu window chứa ≥ 3 BUDGET và 0 PROGRESS → BUDGET_BURN.

## C1-04 (P3) — Contradictory plans?
→ **Resolve**: REPLAN events ghi reason; window có ≥ 2 replan mà reason đối nghịch (VD "world changed" và "rollback" cùng cặp) → CONTRADICTORY_PLANS. V1 đơn giản: ≥ 3 replan trong window → signal (đủ để test).

## C1-05 (P3) — Verdict mức độ?
→ **Resolve**: STUCK nếu ≥1 signal; nếu chỉ signal nhẹ (NO_PROGRESS) → STUCK vẫn (v1 binary); report liệt kê đủ signals + counts.

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
