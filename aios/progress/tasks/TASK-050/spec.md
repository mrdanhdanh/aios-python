# TASK-050 — Autonomous Goal Engine (M9-P1)

## Mục tiêu
Nâng Goal Manager (M2) thành **Autonomous Goal Engine**: goal là contract đầy đủ (objective, success, constraints, permissions, autonomy level) với lifecycle vòng đời đầy đủ: `PROPOSED → VALIDATING → APPROVED → PLANNING → EXECUTING → EVALUATING → COMPLETED` + các nhánh phục hồi `EXECUTING → BLOCKED → RECOVERY → REPLANNING → EXECUTING` và `EXECUTING → ESCALATED → HUMAN` (terminal).

## Phạm vi
- `autonomous/contracts.py`: `GoalContract` (id, objective, success: dict[str,float], constraints: max_cost/max_duration_s, permissions: list[str], autonomy: level A0–A4), `GoalLifecycleState` (13 trạng thái), `AutonomyLevel` (A0..A4)
- `autonomous/goal.py`: `AutonomousGoalEngine` — state machine lifecycle + SQLite persist (autonomous.db) + progress + events `autonomy.goal_*`
- KHÔNG sửa GoalManager M2 (kế thừa khái niệm, persist riêng) — tránh đụng goals.db hiện hữu

## Input/Output
- In: `GoalContract` (propose); Out: goal state transitions + persisted rows
- Fail-closed: transition bất hợp lệ → raise `GoalLifecycleError`

## Tiêu chí chấp nhận (AC)
1. `GoalContract` đủ 7 trường (id, objective, success, constraints, permissions, autonomy, description) — `extra=forbid`
2. Lifecycle machine đủ 13 trạng thái + transitions hợp lệ; transition bất hợp lệ raise
3. Chuỗi chuẩn chạy được: propose → validate → approve → plan → execute → evaluate → complete
4. Nhánh phục hồi: execute → block → recover → replan → execute
5. Nhánh escalation: execute → escalate (terminal, cần human)
6. `progress` tính deterministic (task/step hoàn thành / tổng)
7. Persist SQLite: create → load lại đúng trạng thái (cross-instance)
8. Emit event `autonomy.goal_created` + `autonomy.goal_state` trên mỗi transition
9. Autonomy level A0–A4 validated (A0 ≤ level ≤ A4)
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique-1 resolve)
- **C1-01**: `success` = map `metric → min_value` — đạt khi observed ≥ min_value
- **C1-02**: row lưu state hiện tại + `history` (JSON: list {state, at, reason}) — audit chuỗi transition
- **C1-03**: `GoalContract.steps: list[str]` + `completed_steps: int`; `progress = completed_steps / len(steps)`; engine cung cấp `mark_step_completed(goal_id, step)`
- **C1-04**: ESCALATED là terminal v1 (human tạo goal mới nếu muốn tiếp tục)
- **C1-05**: event `autonomy.goal_state` payload = {goal_id, state, reason}

## Amend (critique-2 resolve)
- **C2-01**: `mark_step_completed` raise nếu step ∉ steps; progress = completed/len(steps) clamp [0,1]
- **C2-02**: `mark_step_completed` chỉ hợp lệ ở EXECUTING/REPLANNING/RECOVERY — state khác raise
- **C2-03**: `transition(goal_id, target, reason)` — reason required (mặc định "auto")
- **C2-04**: `AutonomyLevel` enum A0..A4 — pydantic tự validate
