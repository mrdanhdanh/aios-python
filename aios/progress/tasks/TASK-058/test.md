# TASK-058 — Test results

## Kết quả
- **10/10 AC đạt** (ACCEPTED higher, REJECTED, INCONCLUSIVE no evidence/between, direction lower, evaluate_fn required, deploy only accepted, deploy rejected raise, persist cross-instance, sandbox used)
- Tests: `tests/test_autonomous.py::test_exp058_*` (11 tests)
- Arch: `test_inv033_experiment_via_evidence` (evidence-first literals)
- Full suite: **1780 passed, coverage 94.46%**

## Lệnh chạy
```bash
cd backend && .venv/Scripts/python -m pytest tests/test_autonomous.py -k exp058 -q --no-cov
```
→ 11 passed

## Ghi chú
- evaluate_fn positional call `(hypothesis, evidence_hint)` — tránh keyword mismatch
- Schema cột `hypothesis_id` (fix bug hypothesis_json)
