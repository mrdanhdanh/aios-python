# TASK-055 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `FailureEvent`, `RecoveryStrategy` (4), `STRATEGY_SCORES`, `RecoveryOutcome`
- `backend/src/aios_core/autonomous/recovery.py` — `fingerprint_of` (sha256), `CircuitBreaker` (per-fingerprint + cooldown), `AutonomousRecovery` (pipeline + tried-set + policy + verify + escalate + events `autonomy.recovery`)
