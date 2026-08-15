# TASK-074 — Implementation + Evaluation

## Implementation
| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/upgrade/migration.py` | MigrationStep + MigrationPlan (extra=forbid) + MigrationJournal (SQLite, idempotent) + MigrationEngine (dry_run không side effect / validate / apply backup→steps→journal / rollback ngược + auto-rollback khi fail) + MigrationFormats (config/workflow/plugin v0→v1) |
| `backend/src/aios_core/workflow/cli.py` | +`aiagent migrate <kind> <from> <to> --dry-run|--apply [--journal]` |
| `backend/tests/test_migration.py` | 13 tests |

## Evaluation — 9/9 AC ĐẠT
Migration engine release-grade: plan → backup → dry-run → validate → apply → rollback; journal audit trail; idempotent.

## Bài học
- BackupStore M4 dùng cho apply (inject) — không xây backup mới.
- Migration journal là audit trail cho conformance Gate D (upgrade scenario GS-014/015).
