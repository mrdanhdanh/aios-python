# TASK-085 — Implementation artifacts

## Deliverables

| File | Nội dung |
|------|----------|
| `backend/src/aios_core/upgrade/migration_110.py` | **MỚI** — Migration 1.0→1.1: 4 transforms pure (config marker / workflow bump version / plugin append "1.1.0" compatible / contract bump) + rollback guard + `get_plan(kind, component_id)` (migration_id per component) + `Aios110Migrator` (matrix pre/post check fail-closed, backup trước apply) + `Aios110Result` |
| `backend/src/aios_core/upgrade/migration.py` | **SỬA BUG** — `MigrationEngine.apply` bỏ call backup sai signature (caller chịu trách nhiệm) |
| `backend/src/aios_core/workflow/cli.py` | CLI `migrate`: `--input default=None`; rẽ nhánh `1.0.0→1.1.0` (stub khớp matrix / đọc file / kind guard không dùng argparse choices) |
| `backend/tests/test_migration_110.py` | **MỚI** — 27 test (transforms idempotent/deep-copy/rollback, matrix gate, post-check fail, CLI, journal isolation) |
| `backend/tests/test_migration.py` | (không đổi — hồi quy PASS) |

## Kết quả

- Full suite: **2098 PASS / 0 FAIL** (2071 + 27 mới), coverage 92.98%
- CLI thật: contract/plugin apply (backup_id + journal completed + matrix pre/post ok), dry-run, fail-closed id lạ → exit 1
- arch-health 0 violations · doctor healthy

## Lưu ý thiết kế (từ critique ×2 + review)

- Matrix check dùng **component_id thật** của payload (không hardcode entry id)
- Plugin compatible: append/remove `"1.1.0"` (tương thích dữ liệu v0→v1 `[min]`)
- `migration_id` per component → idempotent đúng, migrate nhiều component cùng kind được
- Mọi unit test inject journal `:memory:`/tmp + BackupStore tmp (không ghi DB thật)
