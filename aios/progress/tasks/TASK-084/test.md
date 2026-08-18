# TASK-084 — Test results (thật)

> Ngày: 2026-08-16 | Môi trường: Windows, Python 3.13, `.venv` backend

## Targeted tests (9 file)

```
248 passed in 10.60s
```
(exit 1 chỉ do coverage gate khi chạy subset — không phải test fail; coverage 80% chỉ áp dụng full suite)

Files: `test_compatibility_matrix.py` (19 test mới) + `test_models.py` + `test_contracts_catalog.py` + `test_architecture.py` (allow-list) + `test_contracts.py` + `test_ecosystem_devkit.py` + `test_policy.py` + `test_ecosystem_marketplace.py` + `test_plugins.py`

## Full suite

```
2071 passed, 54 warnings in 95.08s
Required test coverage of 80% reached. Total coverage: 93.02%
```

- Baseline 2052 (M11) + 19 test mới = **2071 PASS / 0 FAIL** ✅ (AC9)
- Coverage 93.02% ≥ 80% ✅

## CLI thật (F3)

| Lệnh | Kết quả | exit |
|------|---------|------|
| `aiagent system status` | `"version": "1.1.0"` | 0 ✅ AC1 |
| `aiagent contract list` | 10 contract `1.1.0` (plugin deprecated) | 0 ✅ AC2 |
| `aiagent compat list` | 14 entries (10 contract + plugin + workflow + skill + sdk) | 0 ✅ AC5 |
| `aiagent compat check plugin demo 1.0.0` | `{"compatible": true, ...}` | 0 ✅ AC6 |
| `compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` | error max `1.1.x` | 1 ✅ AC6/AC8 |
| `compat check contract agent 1.0.0 --aios-version 0.9.0` | error min + warning version mismatch (R1) | 1 ✅ |
| `compat check contract unknown 1.0.0` | `no matrix entry` | 1 ✅ AC7 |
| `compat check workflow demo_flow 1.0.0 --aios-version 1.1.5` | compatible (patch accepted) | 0 ✅ AC6 |
| OpenAPI `create_app().openapi()['info']['version']` | `1.1.0` | — ✅ AC11 |
| `aiagent arch-health` | `{"healthy": true, "violations": []}` | — ✅ AC10 |
| `aiagent doctor` | `{"status": "healthy"}` | — ✅ AC10 |

## Kết luận

**19/19 test mới PASS + 2071/2071 full suite PASS** — đủ điều kiện đóng TASK-084 (chờ evaluation).
