# TASK-066 — Implementation

| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/kernel/durability.py` | ExecutionJournal (SQLite atomic, run_reason) + JournaledExecutor (topo order, verify-before-resume, skip done nodes, fail-closed) + IdempotencyClassifier (fail-closed default) + DurabilityPolicy (resume/rerun) |
| `backend/src/aios_core/config.py` + `config.yaml` | DurabilitySettings (enabled/db_path/policy) |
| `backend/tests/test_durability.py` | 10 tests |

Không sửa `kernel/services/execution.py` (R1) — journal opt-in qua node_runner wrapper.
