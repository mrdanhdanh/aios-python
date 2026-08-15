# TASK-062 — Test results

## Kết quả
- **10/10 AC đạt** (INTERVAL due/not-due, DAILY hour + same-day skip + next-day run, disabled, fn raise → FAILED, persist restart, overdue chạy 1 lần, duplicate raise, validate interval/hour, empty, unregister)
- Tests: `tests/test_autonomous.py::test_sch062_*` (12 tests)
- Full suite: **1780 passed, coverage 94.46%**

## Lệnh chạy
```bash
cd backend && .venv/Scripts/python -m pytest tests/test_autonomous.py -k sch062 -q --no-cov
```
→ 12 passed

## Ghi chú
- sentinel last_run_at = -1 (phân biệt "chưa chạy" vs "chạy lúc epoch 0")
- last_run cập nhật atomic với insert run history
