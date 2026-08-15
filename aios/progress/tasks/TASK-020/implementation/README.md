# TASK-020 — M4-P7 Upgrade Pipeline — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `upgrade/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/upgrade/dependency.py` — `ComponentSpec`/`DependencyResolver` (topo + cycle/missing/conflict)
- `backend/src/aios_core/upgrade/backup.py` — `BackupStore` (SQLite)
- `backend/src/aios_core/upgrade/migrator.py` — `Protocol` + `DictMigrator` + `SkillMigrator` (wrap SkillManager)
- `backend/src/aios_core/upgrade/pipeline.py` — 6 bước + dry-run + rollback best-effort + 9 events
- `backend/src/aios_core/upgrade/errors.py`
- `backend/src/aios_core/kernel/events.py` (+8 EventType members)
- `backend/src/aios_core/workflow/cli.py` (subcommand `upgrade`, exit codes)

## Key behavior
- Pipeline: STARTED → COMPATIBILITY_OK → DEPENDENCIES_OK → BACKUP_CREATED → MIGRATED → HEALTH_OK → COMPLETED
- Fail sớm: compatibility (major breaking) dừng bước 1; dependency missing dừng bước 2; health fail → rollback + `UPGRADE_ROLLED_BACK`
- Chỉ migrate ROOT, dependency chỉ resolve (quyết định critique-2)
- `dry_run=True` → chạy bước 0→2, trả plan, không side effect

## Verification
- `pytest` full suite: **730 passed, coverage 95.00%, 10/10 AC** (xem `test.md`)
