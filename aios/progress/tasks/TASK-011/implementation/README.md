# TASK-011 — M1 Remediation (9 findings F-001..F-009) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in existing packages
> (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/workflow/cli.py` (F-001 CLI subcommands + F-007 DI qua `RuntimeKernel.create()`/`SystemCatalog()`)
- `backend/src/aios_core/kernel/services/resource.py` (F-003 FIFO queue: `acquire_slot_wait` + `pending()`)
- `backend/src/aios_core/kernel/services/context.py` (F-004 PARENT inheritance map)
- `backend/src/aios_core/kernel/services/execution.py` (F-005 `SNAPSHOT_SAVED` + `TOOL_STARTED`/`TOOL_FINISHED` emit)
- `backend/src/aios_core/catalog/catalog.py` (F-006 `rebuild()`/`_revision`/`is_stale()`)
- `docs/adr/0001-engine-independence.md`, `0002-capability-first.md`, `0003-policy-first.md` (F-008)
- `backend/tests/test_benchmark.py` (F-009 benchmark harness, marked skippable)
- `backend/tests/test_contracts.py` (F-002 field-evolution regression, pydantic dual-class)

## Key changes
- CLI: nested subparsers `doctor` / `catalog list` / `workflow validate` / `contract validate`; dùng DI không còn `ExecutionService(...)` trực tiếp
- Resource: `acquire_slot_wait` blocking chờ ngoài cond-lock; giữ `acquire_slot` non-blocking
- Context: default `inherit=False` (đúng thiết kế); PARENT map cho `get/get_context/get_all`
- Events: snapshot + tool started/finished emit từ ExecutionService (dedup snapshot)

## Verification
- `pytest` full suite: **428 passed, coverage 95.76%, 9/9 AC** (xem `test.md`)
