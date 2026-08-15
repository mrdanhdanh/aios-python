# TASK-061 — Implementation

- `backend/src/aios_core/autonomous/contracts.py` — `StuckSignal` (7), `StuckReport`
- `backend/src/aios_core/autonomous/stuck.py` — `StuckDetector` (window per goal deque bounded + record/detect/reset + 7 signals + oscillation O(n))
