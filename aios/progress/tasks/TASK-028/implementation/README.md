# TASK-028 — M5 Parallel Scheduler — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `kernel/scheduler/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/kernel/scheduler/` — 5 file:
  - `contracts.py` (`NodeResourceMetrics`/`ScheduledGraphResult`), `scheduler.py` (gated runner WRAP GraphExecutor + acquire_slot_wait/release + peak/queue metrics + schedule_plan resolve default_failure_policy + cancel delegate), `execution_runner.py` (adapter 1-node plan literal execution_service.execute), `errors.py`, `__init__.py`
- `backend/src/aios_core/config.py` — `SchedulerSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring (graph_settings=settings.graph)

## Key behavior
- Scheduler KHÔNG sở hữu Resource/Execution implementation (INV-016): Graph Scheduler (dependency) → Scheduler Service (thời điểm) → Resource Service (resource) → Execution Service (execution) → State Service (state)
- Gated runner: node chạy khi `acquire_slot_wait` cấp slot; peak/queue metrics
- Execution runner adapter: 1-node plan literal → `execution_service.execute`

## Verification
- `pytest` full suite: **1086 passed, coverage 95.22%, 12/12 AC** (xem `test.md`)
