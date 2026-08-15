# TASK-029 — M6-H1 Harness Kernel — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `harness/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/harness/contracts.py` — 6 model + `safe_run_id`
- `backend/src/aios_core/harness/errors.py` — `HarnessError`
- `backend/src/aios_core/harness/lifecycle.py` — 8-state + COMPLETED→FAILED + CREATED→FAILED
- `backend/src/aios_core/harness/context.py` — `HarnessContext` (PrivateAttr sink + emit wrap)
- `backend/src/aios_core/harness/registry.py` — ABC abstract + RLock
- `backend/src/aios_core/harness/runner.py` — try/except/finally evidence + catch-all + sanitize + `_evidence_contract` 9 field + get_evidence restart fallback + persist model_dump JSON
- `backend/src/aios_core/config.py` — `HarnessSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring

## Key behavior
- Harness Contract lifecycle: CREATED → PREPARING → VALIDATING → RUNNING → VERIFYING → COMPLETED; lỗi: RUNNING → FAILED → DIAGNOSED
- HarnessRun: run_id deterministic + evidence persist TRƯỚC raise (INV-018 Evidence First)
- Registry: 6 harnesses (kernel/test/evaluation/benchmark/doctor/readiness) — ghi nhận ở TASK-034

## Verification
- `pytest` full suite: **1124 passed, coverage 95.20%, 10/10 AC** (xem `test.md`)
