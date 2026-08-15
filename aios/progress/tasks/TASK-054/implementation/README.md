# TASK-054 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `AutonomyDecision` (6), `AutonomyBudget` (7), `RiskClass` (5), `UsageSnapshot`, `GovernorDecision`, `DEFAULT_RISK_TABLE`
- `backend/src/aios_core/autonomous/governor.py` — `AutonomyGovernor` (check_action + budget 7 limits INV-031 + risk + parallel PAUSE + lazy-init/end_goal + REPLAN world_changed)
