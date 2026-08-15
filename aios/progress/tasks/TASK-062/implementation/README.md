# TASK-062 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `TriggerKind` (2), `ScheduleTrigger`, `TriggerRun`
- `backend/src/aios_core/autonomous/scheduler.py` — `AutonomousScheduler` (register/unregister + persist last_run sentinel -1 + run_due deterministic + fn raise → FAILED + events `autonomy.schedule`)
