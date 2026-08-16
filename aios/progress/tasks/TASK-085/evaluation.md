# TASK-085 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-16 | Task: M12-P1 C2 Migration 1.0→1.1 thật (Issue #7)

## Đối chiếu 12 AC

| AC | Tiêu chí | Kết quả | Bằng chứng |
|----|----------|---------|-----------|
| AC1 | `get_plan(kind, component_id)` đủ 4 kind; migration_id gồm component_id; from/to/backup/rollback | ✅ | `test_get_plan_4_kinds_and_id_per_component` |
| AC2 | Plugin append "1.1.0" giữ phần tử gốc; idempotent; rollback xóa; no mutate | ✅ | `test_plugin_migrate_appends_110` + `test_plugin_migrate_keeps_existing_entries` + `test_plugin_rollback_restores` (C2-03) |
| AC3 | Workflow bump version top-level; no-op khác; rollback guard | ✅ | `test_workflow_migrate_bumps_top_level_version` + `test_workflow_migrate_noop_other_version` |
| AC4 | Contract bump; config marker; 4 transform deep-copy | ✅ | `test_contract_migrate_bumps_version` + `test_config_migrate_marker_and_rollback` (assert payload gốc không mutate) |
| AC5 | Pre-check fail (id lạ) → từ chối, journal không start | ✅ | `test_pre_check_unknown_entry_blocked` (plugin/p — dùng component_id thật) |
| AC6 | Apply thành công → journal completed + backup_id + per-kind assertion + matrix ok | ✅ | `test_apply_plugin_success` + `test_apply_workflow_success` + `test_config_skips_range_and_matrix` |
| AC7 | Step fail → auto-rollback; post-check fail → payload == gốc + rolled_back | ✅ | `test_post_check_fail_rolls_back` (monkeypatch transform no-op → MigrationError "post-check fail", payload không đổi) |
| AC8 | CLI contract apply exit 0 + backup + journal; dry-run không side effect; --input lỗi exit 1; config qua pre-check | ✅ | `test_cli_migrate_110_contract_apply` + `test_cli_migrate_110_dry_run_no_side_effect` (journal null) + `test_cli_migrate_110_input_missing_file` + `test_config_skips_range_and_matrix` |
| AC9 | Matrix post ok (CompatibilityMatrix thật); id lạ exit 1; apply lần 2 component khác không bị chặn | ✅ | `test_cli_migrate_110_plugin_apply` + `test_cli_migrate_110_unknown_entry_exit_1` + `test_apply_contract_twice_different_components` (C2-04) |
| AC10 | Full suite ≥ 2071; test cũ vẫn PASS | ✅ | **2098 PASS / 0 FAIL**; `test_migration.py` + `test_upgrade_cli.py` PASS |
| AC11 | Allow-list không vi phạm | ✅ | `test_architecture.py` PASS (module mới chỉ import upgrade/* + semver + plugins.compat + contracts; json round-trip — không import copy) |
| AC12 | arch-health 0 violations; doctor healthy; không thêm invariant | ✅ | `arch-health: violations []` + `doctor: healthy` |

**12/12 AC ĐẠT** ✅

## Điều kiện review (R1–R5) — đã đáp ứng

- R1: kind giữ free-form, validate trong `_migrate` → `test_cli_migrate_110_bogus_kind` exit 1 (không SystemExit) ✅
- R2: `PLANS_110` = template registry + `get_plan(kind, component_id)` — migration_id per component ✅
- R3: AC7 ghi `failed`/`rolled_back` ✅
- R4: plugin compatible thiếu → seed `[min]` rồi append ✅
- R5: thiếu key → MigrationError rõ (`test_cli` case workflow --input p.json: "payload thiếu 'name'"); test lần 2 dùng contract agent→capability ✅

## Bug phát hiện & sửa trong lúc implement

1. **Bug `MigrationEngine.apply`** (migration.py:152 — `self._backup.backup(f"migration:...")` sai signature 1 arg vs 4 arg → TypeError khi inject backup). **ĐÃ SỬA** (bỏ call — caller chịu trách nhiệm backup) + test hồi quy (không test cũ nào inject backup_store → an toàn).
2. **Thiết kế `_matrix_id` hardcode "demo"** — matrix check phải dùng **component_id thật** (plugin/p → no entry → block đúng; test bắt được ngay).

## Chất lượng

- Module mới `upgrade/migration_110.py`: transforms pure + deep-copy + guard rollback; `Aios110Migrator` matrix-gated fail-closed 2 tầng; dataclass `Aios110Result` rõ ràng
- CLI: nhánh cũ (v0→v1) giữ nguyên — `test_cli_migrate_old_path_still_works` PASS
- Journal isolation: mọi test inject `:memory:`/tmp (C2-05)

## Bài học

1. **Template registry capture reference tại import-time** — monkeypatch transform sau import không ăn; phải patch template entry (hoặc dùng factory).
2. **Matrix check phải dùng identity thật của payload** — hardcode entry id tạo "check giả" (C2-03 ở TASK-084 nói warning ≠ block; nhưng id sai = sai hoàn toàn).
3. **Sửa bug trong engine cũ an toàn khi đã xác minh không test phụ thuộc** — luôn grep trước.

## Kết luận

**TASK-085 DONE — 12/12 AC** — sẵn sàng cho C3 (TASK-086 backward compat) + C4 (TASK-087 conformance).
