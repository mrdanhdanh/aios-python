# TASK-056 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `ExecutionSession`, `SessionStatus`, `Checkpoint`
- `backend/src/aios_core/autonomous/long_horizon.py` — `LongHorizonManager` (session SQLite + checkpoint atomic + resume INV-032 + compact_note + history bounded 50 + events `autonomy.checkpoint`)
