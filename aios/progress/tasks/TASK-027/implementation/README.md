# TASK-027 — M5 Execution Graph — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `kernel/graph/`
> subpackage (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/kernel/graph/` — 6 file:
  - `contracts.py` (8 status), `state_machine.py` (TRANSITIONS + is_ready/dead_end/outcome), `converter.py` (plan_to_graph), `executor.py` (wave loop + READY persist + worker start-guard + retries + failure policy + no-progress guard), `errors.py`, `__init__.py`
- `backend/src/aios_core/config.py` — `GraphSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring (SAU register services — shared StateService)

## Key behavior
- DAG: nodes + edges + dependency + condition + join policy + failure policy (INV-015 acyclicity 3 lớp: contracts + validator + executor)
- Graph state: PENDING · READY · RUNNING · SUCCEEDED · FAILED · SKIPPED · CANCELLED · BLOCKED (state namespace `graph:{id}`)
- Executor: wave loop (chạy node READY song song có giới hạn), retries per-node, failure policy ở ranh giới wave, no-progress guard chống livelock

## Verification
- `pytest` full suite: **1055 passed, coverage 95.09%, 13/13 AC** (xem `test.md`)
