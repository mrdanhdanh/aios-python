# TASK-052 — Test results

## Kết quả
- **10/10 AC đạt** (observe/get, freshness decay công thức, confidence clamp, scope key isolation, history bounded, snapshot 7 nhóm, latest wins)
- Tests: `tests/test_autonomous.py::test_w052_*` (8 tests)
- Arch: `test_m9_world_not_memory` (World ≠ Memory)
- Full suite: **1780 passed, coverage 94.46%**

## Lệnh chạy
```bash
cd backend && .venv/Scripts/python -m pytest tests/test_autonomous.py -k w052 -q --no-cov
```
→ 8 passed

## Ghi chú
- freshness = max(0, 1 - age/TTL); effective_confidence = confidence × freshness
- WorldModel là store thuần — không import memory/knowledge
