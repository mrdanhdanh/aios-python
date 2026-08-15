# TASK-065 — Implementation

| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/kernel/hardening.py` | FailureKind (12) + FailureScenario (fault/detect/contain/recover/resume hooks) + FailureMatrix (trùng id raise) + ScenarioOutcome + HardeningRunner.run_all() |
| `backend/tests/test_hardening.py` | 18 tests — 12 scenario end-to-end thật |

Không sửa `kernel/services/*` — mọi fault qua hook/test double (R1).
