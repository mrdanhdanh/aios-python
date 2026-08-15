# TASK-061 — Advanced Stuck Detection (M9-P2)

## Mục tiêu
Nâng stuck detection M4 (ExecutionSupervisor) thành **Advanced Stuck Detection** (PLAN §M9-27): 7 signals — repeated tool calls · repeated errors · no state change · no progress · oscillation · budget burn · contradictory plans. VD `A → B → A → B` → oscillation detected → stop/replan.

## Phạm vi
- `autonomous/stuck.py`: `StuckDetector` — window tracking (tool_calls, errors, states, progress, decisions, budget), detect → `StuckReport` (signals[], verdict STUCK/NORMAL)
- `contracts.py`: `StuckSignal` enum (7), `StuckReport`

## Input/Output
- In: `record(event_type, detail)` từng bước; `detect(goal_id)`; Out: StuckReport
- Fail-closed: window quá ít dữ liệu → NORMAL (không false-positive)

## Tiêu chí chấp nhận (AC)
1. 7 signal enum: REPEATED_TOOL_CALLS / REPEATED_ERRORS / NO_STATE_CHANGE / NO_PROGRESS / OSCILLATION / BUDGET_BURN / CONTRADICTORY_PLANS
2. Repeated tool calls: cùng tool > threshold trong window → signal
3. Repeated errors: cùng error fingerprint > threshold → signal
4. No state change: N bước không đổi state → signal
5. No progress: N bước không tăng progress → signal
6. **Oscillation**: chuỗi A→B→A→B (2 chu kỳ liên tiếp trở lên) → signal
7. Budget burn: cost/steps tăng nhanh không progress → signal (cần rate)
8. Contradictory plans: replan > 2 lần trong window với reasons trái ngược (VD "world changed" rồi "revert") → signal
9. `detect()` trả verdict STUCK nếu ≥ 1 signal (P1 signals: OSCILLATION/REPEATED_ERRORS) — NORMAL nếu không
10. Window size injectable; unit tests coverage ≥ 90%

## Amend (critique ×2 resolve)
- C1-01: window = deque bounded per goal_id (mặc định 20); record(event_type, goal_id, detail)
- C1-02: oscillation: tồn tại i sao cho states[i]==states[i+2] and states[i+1]==states[i+3]
- C1-03: BUDGET_BURN: ≥ 3 BUDGET + 0 PROGRESS trong window
- C1-04: CONTRADICTORY_PLANS: ≥ 3 REPLAN trong window (v1)
- C2-01: `reset(goal_id)` xóa window (replan/recovery thành công); detect() chỉ đọc
- C2-02: thresholds mặc định: tool ≥3, error ≥3, no-state ≥5, no-progress ≥5, oscillation 4-state, budget ≥3, replan ≥3 (injectable)
- C2-03: StuckReport(signals, counts, verdict, window_size)
