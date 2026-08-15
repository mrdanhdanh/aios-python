# TASK-045 — Test + Evaluation

## Test
`tests/test_extension_contracts.py` (8 tests) + arch tests:
- Namespace 4 giá trị; extra=forbid; parse `*`/`^`/`>=`/exact/`~`; `^2.0` major pinned; missing contract fail-closed; `~` warning; namespace gate raise.

## Evaluation
Đạt đủ 6/6 AC. `check_requires` pure function fail-closed; `^` dùng `compare()` từ semver (VersionInfo không hỗ trợ `>=`). Nền cho TASK-046 registry (namespace filter).
**TASK-045 DONE**
