# TASK-085 — Tasks breakdown (checklist)

> Spec v3 (12 AC). Hard gate: spec ✅ + critique-1 (15/15) ✅ + critique-2 (9/9) ✅

## A. Sửa bug MigrationEngine (C1-01 + C2-08)
- [ ] A1. `upgrade/migration.py` — bỏ dòng `self._backup.backup(f"migration:...")` trong `MigrationEngine.apply` (sai signature); giữ param `backup_store` (compat, ghi chú dead)
- [ ] A2. Test hồi quy trong `test_migration.py`: inject backup fake → `engine.apply` KHÔNG gọi backup, journal completed

## B. Module `upgrade/migration_110.py`
- [ ] B1. Constants: `AIOS_100 = "1.0.0"` + import `AIOS_VERSION` từ `.compatibility` (C1-14); `_deep()` = json round-trip (không import copy)
- [ ] B2. Transforms 4 kind + rollbacks (guard C2-03/C1-07): config (migration marker), workflow (bump version top-level), plugin (append/xóa "1.1.0" trong aios.compatible), contract (bump version) — deep-copy, idempotent
- [ ] B3. `build_110_plan(kind, component_id)` → MigrationPlan với migration_id gồm component_id (C2-04); `PLANS_110` registry helper `get_plan(kind, component_id)`
- [ ] B4. `Aios110Result` dataclass: payload, backup_id, journal_status, matrix {pre, post, warnings} (C2-09)
- [ ] B5. `Aios110Migrator`: component_id mapping (C1-11), `_pre_check` (range chỉ plugin/workflow/contract C2-01 + matrix kind có entry, config skip), `_post_check` (assertion per-kind C1-06/C2-03 + matrix), dry_run/apply (backup trước C1-01)/rollback (plan, RESULT C2-06)

## C. CLI `migrate` mở rộng
- [ ] C1. Parser: choices thêm `contract`; `--input default=None` (C2-02)
- [ ] C2. Rẽ nhánh `from=1.0.0 and to=1.1.0`: `PLANS_110.get` guard (C1-12), đọc `--input` hoặc stub khớp matrix (C1-03), file lỗi → exit 1
- [ ] C3. Output: + `matrix: pre/post` + `backup_id:` + `journal:` (+ warnings C2-09)

## D. Tests `tests/test_migration_110.py`
- [ ] D1. Unit transforms: idempotent, deep-copy (input không mutate), rollback guard — kể cả case `compatible=["1.0.0"]` (C2-03)
- [ ] D2. Matrix gate: pre-check fail (id lạ) journal không start; config qua pre-check (C2-01); post-check fail → rollback payload == gốc + journal rolled_back + backup giữ (C2-06)
- [ ] D3. CLI: apply contract/plugin (--journal tmp) exit 0 + backup + journal; dry-run không side effect; --input file lỗi exit 1; cùng kind apply lần 2 component khác không bị chặn (C2-04); id lạ exit 1
- [ ] D4. MỌI unit test inject journal `:memory:`/tmp + BackupStore tmp (C2-05)

## E. Verify & đóng task
- [ ] E1. Targeted: `pytest tests/test_migration_110.py tests/test_migration.py tests/test_upgrade_cli.py tests/test_architecture.py` — PASS
- [ ] E2. Full suite pytest — ≥ 2071 PASS / 0 FAIL (verify baseline trước — C1-15)
- [ ] E3. CLI thật: migrate plugin/contract 1.0.0 1.1.0 --apply (--journal tmp) + dry-run + fail case
- [ ] E4. `aiagent arch-health` 0 violations + `doctor` healthy
- [ ] E5. Viết test.md + evaluation.md + implementation/README.md; LOG/PROGRESS; commit — KHÔNG push
