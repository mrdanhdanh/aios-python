# TASK-051 — Autonomous Planner (M9-P1)

## Mục tiêu
Từ `Request → Execution Plan` (M5 PlanningEngine) thành **Autonomous Planner**: `Goal → World State → Constraints → Available Capabilities → History → Plan`. Plan có `assumptions · steps · success_conditions · rollback`. Hỗ trợ **Dynamic Replanning** khi thế giới thay đổi bất ngờ (plan không bất biến).

## Phạm vi
- `autonomous/planner.py`: `AutonomousPlanner` — deterministic v1 (offline-first, KHÔNG LLM mặc định): phân rã goal objective thành steps dựa trên capabilities có sẵn + constraints
- Plan contract trong `contracts.py`: `AutonomyPlan` (id, goal_id, assumptions, steps[], success_conditions[], rollback{enabled, strategy}, reasons[], created_at)
- `replan(goal, world, plan, reason)` → Plan mới (giữ goal_id, đánh dấu reasons)

## Input/Output
- In: goal (GoalContract), world (WorldState), constraints, capabilities (list[str]), history; Out: `AutonomyPlan`
- Fail-closed: thiếu objective hoặc capabilities rỗng → raise `PlanError`

## Tiêu chí chấp nhận (AC)
1. `plan()` trả `AutonomyPlan` có đủ assumptions/steps/success_conditions/rollback
2. Mỗi step có: id, description, capability (thuộc capabilities đầu vào), dependencies (list)
3. Steps sinh deterministic (cùng input → cùng output, sorted)
4. success_conditions suy từ `goal.success` (key nào có threshold)
5. rollback.enabled = False khi risk chứa hành động không rollback được (delete)
6. `replan()` trả Plan mới có `reasons` chứa lý do replan, steps sinh lại từ world mới
7. Constraint max_duration_s được phản ánh (estimate tổng ≤ max_duration → không vượt)
8. Plan validation: objective rỗng / steps rỗng → raise
9. Contract `extra=forbid`
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique-1 resolve)
- **C1-01**: giữ fail-closed — capabilities rỗng → raise `PlanError` (goal luôn hướng hành động)
- **C1-02**: steps sinh **keyword-based**: `ACTION_KEYWORDS = {fix: [python, filesystem], test: [python], docs: [filesystem], review: [filesystem], deploy: [docker], analyze: [python, filesystem]}` — mỗi keyword trong objective → 1 step (description = objective + keyword); deterministic, sorted
- **C1-03**: dependencies = [] mọi step v1 (trường tồn tại cho tương lai + test replan)
- **C1-04**: planner nhận `risk_table` injectable (mặc định constants chung trong contracts.py — dùng chung với governor)
- **C1-05**: mỗi step có `estimated_duration_s` (mặc định 60); tổng > max_duration_s → `over_budget: true` (KHÔNG raise)

## Amend (critique-2 resolve)
- **C2-01**: objective không khớp keyword → 1 step mặc định `capability="python"` (mô tả = objective); raise chỉ khi capabilities rỗng
- **C2-02**: filter — step chỉ sinh nếu ≥1 capability của map ∈ capabilities input; map rỗng sau filter → capability đầu tiên của input
- **C2-03**: `replan()` nhận `completed_step_ids` — steps mới đánh dấu đã hoàn thành
