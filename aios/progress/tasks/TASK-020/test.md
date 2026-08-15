# TASK-020 — Test Results (Upgrade Pipeline, M4-P7)

**Ngày**: 2026-08-13 | **Runner**: pytest (backend/.venv) — file bổ sung hồi tố 2026-08-15 khi đóng hard gate

## Kết quả tổng
- **Full suite**: `730 passed, 0 failed` (baseline M3: 689 → +41 test mới)
- **Coverage**: 95.00% (threshold ≥80% cứng — pass)
- **Arch tests**: `test_inv_upgrade_import_allowlist` pass (internal: contracts, semver, kernel.events, skills.errors; external: sqlite3/pathlib/contextlib/json/dataclasses/typing/datetime/uuid/collections/logging)

## Test mới (41)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_upgrade_dependency.py` | ~12 | topo đúng (dep trước, sort (name, version)); missing → fail tên dep; cycle → fail kèm path; conflict (cùng name khác version) → fail; deterministic |
| `tests/test_upgrade_backup.py` | ~7 | backup/restore/list đúng; persist 2 instance; list lọc kind/component_id |
| `tests/test_upgrade_pipeline.py` | ~15 | event sequence STARTED → COMPATIBILITY_OK → DEPENDENCIES_OK → BACKUP_CREATED → MIGRATED → HEALTH_OK → COMPLETED; compatibility fail dừng bước 1 (major breaking 1.0.0→2.0.0); dependency fail dừng bước 2; health fail → rollback + UPGRADE_ROLLED_BACK; migrate raise → rollback (rollback lỗi → ghi reason không raise); same/older version → skipped; dry_run không backup/migrate/health |
| `tests/test_upgrade_migrator.py` | ~5 | DictMigrator + SkillMigrator wrap SkillManager |
| `tests/test_architecture.py` | +1 | allow-list upgrade/ |
| `tests/test_cli.py` | +1 | CLI `aiagent upgrade <kind> <id>` (exit codes) |

## Kiểm chứng AC (10/10)
- **AC1** ✅ DependencyResolver — topo + missing + cycle + conflict + deterministic
- **AC2** ✅ BackupStore — backup/restore/list + persist + filter
- **AC3** ✅ Pipeline thành công — đủ 7 event đúng thứ tự; backup_id set; plan = topo order
- **AC4** ✅ Compatibility fail (major breaking) → dừng bước 1, không backup/migrate, reason rõ
- **AC5** ✅ Dependency fail (missing) → dừng bước 2
- **AC6** ✅ Health fail → rollback, status=failed, event UPGRADE_ROLLED_BACK
- **AC7** ✅ Migrate raise → rollback; rollback lỗi → reason không raise
- **AC8** ✅ Same/older version → skipped; component không tồn tại → failed sớm "component not found"
- **AC9** ✅ dry_run → bước 0→2, trả plan, không side effect; CLI hoạt động
- **AC10** ✅ Allow-list AST + full pytest pass + coverage ≥80%

## Kết luận
- [x] Tất cả 10 AC pass
- [x] Full suite 730 pass, coverage 95.00%
