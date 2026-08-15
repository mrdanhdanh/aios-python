# TASK-051 — Tasks breakdown

- [x] Spec + critique ×2 (resolved) + review
- [ ] `contracts.py`: AutonomyPlan + PlanStep + RollbackSpec (dùng chung contracts.py với TASK-050)
- [ ] `planner.py`: AutonomousPlanner — ACTION_KEYWORDS map + plan() + replan() + over_budget + completed_step_ids
- [ ] `errors.py`: PlanError
- [ ] Tests: deterministic plan, keyword không khớp → default step, capabilities rỗng → raise, replan, over_budget, success_conditions
- [ ] Evaluate + cập nhật PROGRESS/LOG
