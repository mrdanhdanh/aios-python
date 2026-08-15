# TASK-053 — Autonomous Loop (M9-P1)

## Mục tiêu
Trái tim M9: vòng lặp `Observe ↓ Understand ↓ Decide ↓ Plan ↓ Policy ↓ Act ↓ Verify ↓ Learn (→ Observe)`. Loop KHÔNG được `while True: agent.run()` — mọi hành động đi qua **Autonomy Governor** (INV-030) và bounded bởi budget (INV-031).

## Phạm vi
- `autonomous/loop.py`: `AutonomousLoop` — 8 bước, mỗi bước là callable injectable (offline-first, deterministic mặc định)
- Vòng lặp: `run_goal(goal)` chạy tối đa budget.max_steps vòng; mỗi vòng gọi governor trước Act

## Input/Output
- In: goal (GoalContract) + injectables (observer, understander, governor, planner, policy_check, actor, verifier, learner); Out: `LoopResult` (iterations, decisions[], final_state, success)
- Fail-closed: governor trả STOP → loop dừng ngay (không Act tiếp)

## Tiêu chí chấp nhận (AC)
1. `run_goal()` chạy đủ 8 bước đúng thứ tự mỗi vòng (Observe→Understand→Decide→Plan→Policy→Act→Verify→Learn)
2. **INV-030**: trước mỗi Act, loop PHẢI gọi `governor.check_action(...)` — governor STOP → không Act (arch test literal `governor.check_action(` trong loop.py)
3. Policy check trước Act: policy deny → loop dừng + ghi decision ASK_HUMAN/STOP
4. Loop bounded: iterations ≤ budget.max_steps (INV-031)
5. `LoopResult` có iterations đếm được, decisions (danh sách AutonomyDecision), final_state, success
6. Mỗi vòng emit event `autonomy.loop_step`
7. Các bước injectable — mặc định deterministic (không LLM)
8. Learn nhận verdict từ verify (đóng vòng lặp)
9. Loop dừng sớm khi goal COMPLETED (success_conditions đạt)
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique-1 resolve)
- **C1-01**: verifier trả `VerificationResult(success: bool, evidence: dict, score: float)`; learner nhận result; loop dừng khi success=True
- **C1-02**: policy deny → governor trả ASK_HUMAN (risk=approval) hoặc STOP (deny cứng); loop dừng khi decision ∈ {STOP, ASK_HUMAN} — ASK_HUMAN → `final_state="awaiting_human"`
- **C1-03**: act = callable nhận (plan_step, context) → kết quả; autonomous/ KHÔNG import aios_core.tools/agents (INV-002/030 tinh thần); act thật qua Orchestrator (wiring)
- **C1-04**: event `autonomy.loop_step` payload = {goal_id, iteration, decision, step_id}
- **C1-05**: `LoopFinalState`: COMPLETED / STOPPED / AWAITING_HUMAN / ERROR / BUDGET_EXCEEDED

## Amend (critique-2 resolve)
- **C2-01**: Decide = gọi governor 1 lần/vòng; Act chỉ chạy khi decision=CONTINUE
- **C2-02**: understand mặc định deterministic: trả {fact_count, changed} từ world snapshot
- **C2-03**: planner callable (mặc định AutonomousPlanner); plan() chỉ khi chưa có plan hoặc decision=REPLAN
- **C2-04**: learn luôn chạy cuối vòng (nhận VerificationResult — cả success/fail); learner mặc định noop
