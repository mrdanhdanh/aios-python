# TASK-054 — Autonomy Governor (M9-P1)

## Mục tiêu
Governor là architecture invariant (INV-030): **không autonomous action nào thực hiện ngoài Governor**. Quyết định: `CONTINUE · PAUSE · ASK_HUMAN · REPLAN · ROLLBACK · STOP`. Enforce **Autonomy Budget** (INV-031): steps / llm_calls / cost / duration / tool_calls / retries / parallel agents. **Risk Budget**: read → autonomous, edit → autonomous, commit → approval, push → approval, delete → impossible.

## Phạm vi
- `autonomous/governor.py`: `AutonomyGovernor` — decision + budget + risk
- `contracts.py`: `AutonomyDecision` (6 giá trị), `AutonomyBudget` (7 giới hạn), `RiskClass` (5 cấp)
- Injectable: clock, budget (từ settings), risk table

## Input/Output
- In: `check_action(goal_id, action, risk_class, usage)`; Out: `AutonomyDecision` kèm reason
- Fail-closed: thiếu usage → STOP (không mạo hiểm)

## Tiêu chí chấp nhận (AC)
1. `AutonomyDecision` đủ 6 giá trị (CONTINUE/PAUSE/ASK_HUMAN/REPLAN/ROLLBACK/STOP)
2. **INV-031**: vượt budget steps → STOP; vượt cost → STOP; vượt duration → STOP; vượt tool_calls → STOP; vượt llm_calls → STOP; vượt retries → STOP (mỗi cái test riêng)
3. Risk `approval` → ASK_HUMAN; risk `impossible` → STOP; risk `autonomous` → CONTINUE (nếu budget OK)
4. Budget tracking theo goal_id: `start_goal(goal_id)` reset counter; usage cộng dồn mỗi check
5. `max_parallel_agents` enforce khi action là delegate (risk class DELEGATE) — vượt → PAUSE
6. Reason kèm mọi decision (STOP: "budget.steps exceeded" etc.)
7. **INV-030**: arch test — `governor.check_action(` literal trong loop.py; governor là nơi duy nhất trả AutonomyDecision
8. Contract `extra=forbid`
9. Clock + budget injectable (deterministic test)
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique-1 resolve)
- **C1-01**: `check_action(goal_id, ...)` lazy-init budget entry (now = clock()) nếu chưa có; `start_goal(goal_id)` idempotent (không reset nếu đã tồn tại)
- **C1-02**: `RiskClass` 5 cấp: READ / EDIT / COMMIT / DEPLOY / DELETE (delete = impossible); delegate dùng risk của hành động thật; max_parallel_agents check theo `usage.parallel_agents`
- **C1-03**: STOP = terminal cho goal (budget cạn); PAUSE = tạm dừng (parallel đầy — có thể chờ)
- **C1-04**: governor trả REPLAN/ROLLBACK khi `world.changed()` predicate (injectable) hoặc verify fail lặp; loop thực thi — governor chỉ quyết định
- **C1-05**: reason = `f"{category}.{limit} exceeded (used {used}/{limit})"` — deterministic

## Amend (critique-2 resolve)
- **C2-01**: `end_goal(goal_id)` xóa budget entry; loop gọi khi goal kết thúc; check_action sau end_goal → lazy-init fresh
- **C2-02**: `UsageSnapshot(steps, llm_calls, cost, duration_s, tool_calls, retries, parallel_agents)` — extra=forbid; actor trả usage delta → loop cộng dồn
- **C2-03**: `risk_table` injectable, mặc định từ `AutonomousRiskSettings`; constants chung trong contracts.py cho planner (cùng nguồn)
- **C2-04**: `world.changed()` mặc định `lambda: False`
