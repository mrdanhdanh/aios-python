# TASK-058 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `Hypothesis`, `Experiment`, `ExperimentVerdict`
- `backend/src/aios_core/autonomous/experimentation.py` — `ExperimentationEngine` (sandbox_fn → evaluate_fn required → compare direction → verdict + deploy canary + SQLite persist + events `autonomy.experiment` — INV-033 evidence-first)
