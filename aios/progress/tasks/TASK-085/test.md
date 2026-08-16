# TASK-085 — Test results (thật)

> Ngày: 2026-08-16 | Môi trường: Windows, Python 3.13, `.venv` backend

## Targeted tests (4 file)

```
149 passed in 3.02s
```
`test_migration_110.py` (27 test mới) + `test_migration.py` + `test_upgrade_cli.py` + `test_architecture.py` (allow-list)

## Full suite

```
2098 passed, 69 warnings in 68.46s
Required test coverage of 80% reached. Total coverage: 92.98%
```

- Baseline 2071 (TASK-084) + 27 test mới = **2098 PASS / 0 FAIL** ✅ (AC10)

## CLI thật (migrate 1.0.0 → 1.1.0, --journal tmp)

| Lệnh | Kết quả | exit |
|------|---------|------|
| `migrate contract 1.0.0 1.1.0 --apply` | `applied: true`, `backup_id: 1`, `journal: completed`, matrix pre/post ok, payload `version: 1.1.0` | 0 ✅ |
| `migrate plugin 1.0.0 1.1.0 --apply` | `backup_id: 2`, `compatible: ["1.0.0","1.1.0"]`, matrix ok | 0 ✅ |
| `migrate plugin 1.0.0 1.1.0 --dry-run` | `dry_run: true`, steps `[plugin-100-to-110]`, matrix pre ok/post skipped | 0 ✅ |
| `migrate workflow 1.0.0 1.1.0 --apply --input p.json` (id lạ) | `FAILED: ...` | 1 ✅ fail-closed |
| `migrate bogus 1.0.0 1.1.0` | `FAILED: kind không hỗ trợ` | 1 ✅ |

## Health (AC12)

- `arch-health`: `{"healthy": true, "violations": []}`
- `doctor`: `{"status": "healthy", "kernel": "ok"}`
- KHÔNG thêm invariant mới; INV-001..035 giữ nguyên

## Kết luận

**27/27 test mới + 149/149 targeted + 2098/2098 full suite PASS** — đủ điều kiện đóng TASK-085 (chờ evaluation).
