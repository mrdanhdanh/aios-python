# TASK-034 — M6-H5 Doctor & Readiness — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `harness/doctor/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/harness/doctor/contracts.py` — DoctorKind 13 + DoctorStatus 4 + DoctorResult/HardGate/ReadinessReport (extra=forbid)
- `backend/src/aios_core/harness/doctor/errors.py` — `DoctorError` + `ReadinessError`
- `backend/src/aios_core/harness/doctor/checks.py` — `DoctorChecks` register/run/run_all sorted + placeholder PASS + fn raise → ERROR + clamp score
- `backend/src/aios_core/harness/doctor/doctor.py` — `DoctorHarness` id=doctor kinds subset validate + persist TRƯỚC raise + strict + get_results
- `backend/src/aios_core/harness/doctor/readiness.py` — `ReadinessScorer` dimensions/overall mean UNKNOWN→0.0 + hard gates policy→overall + RELEASE BLOCKED summary + `ReadinessHarness` id=readiness persist trước raise + get_report
- `backend/src/aios_core/config.py` — `DoctorSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — shared DoctorChecks + register doctor + readiness

## Key behavior
- Doctor Architecture: Architecture · Runtime · Workflow · Agent · Capability · Tool · Memory · Model · Policy · Registry · Performance · Security · Evidence (13 kinds) → PASS · WARNING · ERROR · UNKNOWN
- Readiness Score: overall = mean (UNKNOWN→0.0); hard gate: policy violation > 0 → RELEASE BLOCKED dù overall 99%
- Shared DoctorChecks giữa doctor + readiness (không duplicate checks)

## Verification
- `pytest` full suite: **1521 passed, coverage 95.35%, 11/11 AC** (xem `test.md`)
