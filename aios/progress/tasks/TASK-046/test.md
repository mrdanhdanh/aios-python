# TASK-046 — Test + Evaluation

## Test
`tests/test_ecosystem_registry.py` (7 tests): entry validation (extra=forbid, semver), index/get/update/persist qua restart, search deterministic + kind filter + publisher match, remove, list_by_kind, model-direct index.

## Evaluation
Đạt 8/8 AC. Registry thuần index/search (upsert ON CONFLICT, sort (kind,id), search 5 trường). MCP là adapter — ghi chú trong docstring discovery pipeline. Sẵn sàng cho TASK-047/049/048 cùng package ecosystem/.
**TASK-046 DONE**
