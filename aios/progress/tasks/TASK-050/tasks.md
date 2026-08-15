# TASK-050 — Tasks breakdown

- [x] Spec + critique ×2 (resolved) + review
- [ ] `contracts.py`: GoalContract + GoalLifecycleState (13) + AutonomyLevel (A0..A4) + transitions map
- [ ] `goal.py`: AutonomousGoalEngine — propose/validate/approve/transition/mark_step_completed/progress + SQLite persist (autonomous.db) + history JSON + events
- [ ] `errors.py`: GoalLifecycleError
- [ ] Tests: lifecycle chuẩn + recovery chain + escalate + persist reload + events + progress
- [ ] Evaluate + cập nhật PROGRESS/LOG
