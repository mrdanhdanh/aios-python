# Evaluation — TASK-020 (Upgrade Pipeline)

> 2026-08-13 | đối chiếu spec v4 (10 AC) với kết quả thực tế.

## Kết quả kiểm chứng

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|------------|
| AC1 | DependencyResolver: topo (dep trước, sort name/version), missing/cycle/conflict, deterministic | ✅ | test_upgrade_dependency.py 10 test (topo, stable sort, deterministic, missing, cycle, self-cycle, conflict pin-vs-installed, diamond, frozen) |
| AC2 | BackupStore: backup/restore/list + persist 2 instance + payload fidelity | ✅ | test_upgrade_backup.py 6 test (roundtrip, missing raise, filters, persist, nested payload, schema) |
| AC3 | Pipeline ok: sequence events đúng + status=ok + backup_id + plan | ✅ | test_success_sequence_and_events — 7 event đúng thứ tự |
| AC4 | Compatibility fail (1.0.0→2.0.0 major breaking) → dừng, không backup/migrate | ✅ | test_compatibility_fail_major_break — chỉ 1 event STARTED, store không đổi |
| AC5 | Dependency fail (missing) → dừng bước 2 | ✅ | test_dependency_missing_fails_before_backup |
| AC6 | Health fail → rollback + UPGRADE_ROLLED_BACK | ✅ | test_health_fail_triggers_rollback + test_validate_hook_failure_rolls_back |
| AC7 | Migrate raise → rollback; rollback lỗi best-effort | ✅ | test_migrate_raise_triggers_rollback_via_write_current + test_rollback_error_best_effort |
| AC8 | Same/older → skipped (step=None); not-found → failed sớm | ✅ | test_skip_same_or_older_version + test_component_not_found_fails_early |
| AC9 | dry-run 0→2 không backup/migrate; CLI exit codes; v1 chỉ wire skill | ✅ | test_dry_run_no_changes + test_dry_run_incompatible + test_upgrade_cli.py 7 test (success=0, skipped=0, fail=1, invalid=1, not-found=1, not-wired=1) |
| AC10 | Allow-list AST + toàn bộ pytest + coverage | ✅ | test_inv_upgrade_import_allowlist pass; full suite 730 pass, coverage 95.00%; upgrade/ 95-100% |

## Thống kê
- **Tests**: 41 mới (dependency 10, backup 6, pipeline 18, cli 7) — full suite **689 → 730**, coverage 95.00%
- **Files mới**: upgrade/ (errors, dependency, backup, migrator, pipeline, __init__) + 5 test files
- **Files sửa**: kernel/events.py (+8 EventType), workflow/cli.py (subcommand upgrade), test_architecture.py (+allow-list)

## Hard gate
- Spec v1 → critique-1 (15 vấn đề, 5 P1) → v2 → critique-2 (16 vấn đề, 4 P1) → v3 → review (CHANGES REQUESTED: 1 R1 + 3 R2 + 6 R3) → v4 → implement → test → evaluate → commit

## Kết luận
**TASK-020 DONE** — 10/10 AC pass, P7 Upgrade Pipeline hoàn tất (Compatibility → Dependencies → Backup → Migration → Health Check → Rollback).
