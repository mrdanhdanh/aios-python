# TASK-078 — Implementation artifacts

## Code (backend)

| File | Vai trò |
|------|---------|
| `backend/src/aios_core/verification/__init__.py` | Package Verification Kernel (INV-035) facade |
| `backend/src/aios_core/verification/state.py` | VerificationState (8 states) + classification helpers |
| `backend/src/aios_core/verification/normalize.py` | `fail_closed_normalize()` bảng 8×8 + transition table CLI |
| `backend/src/aios_core/verification/contracts.py` | VerificationOutcome (pydantic extra=forbid) + VerificationMechanism protocol |
| `backend/src/aios_core/verification/gate.py` | VerificationGate (violation detect + exception→BLOCKED) + format |
| `backend/src/aios_core/verification/mechanisms.py` | 3 default mechanisms (security/contract/harness-execution) |
| `backend/src/aios_core/harness/execution/contracts.py` | CheckResult: +`error` field + `effectively_passed` (INV-035) |
| `backend/src/aios_core/harness/execution/pipeline.py` | `run_checks` exception→error; `compute_verdict` skipped/error→INCONCLUSIVE |
| `backend/src/aios_core/security/contracts.py` | SecurityReport +`skipped` list; summary INCONCLUSIVE khi skipped |
| `backend/src/aios_core/security/checks.py` | SecurityChecker exception→skipped (fail-closed) |
| `backend/src/aios_core/harness/certification/checks.py` | Area `verification` (INV-035 — gate chặn mock non-terminal→PASS) |
| `backend/src/aios_core/harness/certification/conformance.py` | Release gate `gate_f_verification` (default mechanisms thật) |
| `backend/src/aios_core/workflow/cli.py` | CLI `aiagent verify-state` + conformance help update |
| `backend/tests/test_verification.py` | 30 tests INV-035 (state/normalize/gate/CheckResult/security/default mechanisms) |
| `backend/tests/test_certification.py` | Update `test_gate_definitions` (+gate_f_verification) |

## Docs / audit

| File | Vai trò |
|------|---------|
| `aios/progress/tasks/TASK-078/implementation/audit.md` | Retroactive audit — commit webgame/visual đối chiếu INV-035 (F1–F7) |
