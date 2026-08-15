# TASK-050 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `GoalContract`, `GoalConstraints`, `GoalLifecycleState` (13), `AutonomyLevel`, `_GOAL_TRANSITIONS`
- `backend/src/aios_core/autonomous/goal.py` — `AutonomousGoalEngine` (propose/transition/helpers/mark_step_completed/progress + SQLite persist + history + events)
- `backend/src/aios_core/autonomous/errors.py` — `GoalLifecycleError`
- `backend/src/aios_core/kernel/events.py` — `AUTONOMY_GOAL_CREATED/STATE`
