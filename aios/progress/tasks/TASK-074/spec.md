# TASK-074 — M10-F8: Upgrade & Migration 1.0

## Mục tiêu
PLAN §M10-34: hỗ trợ `0.x→1.0 · 1.0→1.1 · plugin v0→v1 · contract v0→v1 · workflow v0→v1` với `migration plan · backup · dry-run · validation · rollback`. Biến Upgrade Pipeline (M4) thành **release-grade migration engine**.

## Phạm vi
- `upgrade/migration.py`:
  - `MigrationStep` (kind: config/plugin/contract/workflow, id, fn, rollback_fn)
  - `MigrationPlan` (from_version, to_version, steps, backup_required, extra=forbid)
  - `MigrationEngine`: `plan(...)` → `dry_run(plan)` (không thay đổi) → `validate(plan)` → `apply(plan)` (backup trước → từng step → validate sau) → `rollback(plan)` (ngược steps, best-effort)
  - `MigrationFormats`: config v0→v1 (rename field: `models.routing` → giữ nguyên; ví dụ chuẩn: `autonomous.budget.max_duration_s`), workflow v0→v1 (depends_on), plugin v0→v1 (aios range)
  - `MigrationJournal` (SQLite: migration id, status, steps done)
- CLI: `aiagent migrate <kind> <from> <to> --dry-run|--apply`
- Tái dùng BackupStore (M4) cho backup

## Ngoài phạm vi
- Không thay đổi upgrade pipeline M4 (MigrationEngine là tầng mới gọi qua API)
- Không migration thật dữ liệu lớn (demo formats + framework)

## Input
- `upgrade/backup.py` (BackupStore), `upgrade/pipeline.py`, `upgrade/dependency.py`, `plugins/compat.py`, `contracts/catalog.py`

## Output
- `backend/src/aios_core/upgrade/migration.py` + CLI + `tests/test_migration.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | MigrationPlan validation: steps non-empty, version semver, backup_required mặc định True | Test |
| AC2 | `dry_run` không thay đổi gì (không side effect) | Test |
| AC3 | `apply`: backup trước → steps theo thứ tự → journal ghi status | Test |
| AC4 | `rollback`: chạy ngược rollback_fn các step đã apply (best-effort, không crash) | Test |
| AC5 | Step fail giữa chừng → apply raise + journal FAILED + rollback tự động | Test |
| AC6 | MigrationFormats: config v0→v1 (rename field chuẩn) + workflow v0→v1 (depends_on) + plugin v0→v1 (aios range) — deterministic | Test |
| AC7 | CLI `aiagent migrate config 0.9.0 1.0.0 --dry-run` + `--apply` chạy thật | Test CLI |
| AC8 | Regression full suite | pytest |
| AC9 | Đóng DoD | checklist |

## Ghi chú
- Rollback sau fail = engine tự gọi (fail-safe); rollback thủ công qua `--rollback` (optional).
- Migration journal = audit trail (migration_id, from, to, status, steps).
