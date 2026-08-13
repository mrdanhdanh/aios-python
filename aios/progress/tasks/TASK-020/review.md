# Review — TASK-020 (reviewer subagent)

> 2026-08-13 | reviewer review spec v3: **CHANGES REQUESTED** (1 R1 + 3 R2 + 6 R3) → resolve → spec v4 → implement → verify.

## Findings & Resolution

### R1 (blocking): 1
- **R1-1**: SkillMigrator cần catch `SkillError`/`SkillStateError` (skills/errors.py) nhưng allow-list AC10 thiếu `aios_core.skills.errors` → test arch fail ngay → **Resolve**: thêm vào allow-list; implement catch đúng 2 loại exception, wrap thành `UpgradeError` (migrator.py).

### R2 (major): 3
- **R2-1**: AC4 case "downgrade major" không thể xảy ra (skip-check chặn trước) → **Resolve**: đổi case thành upgrade major breaking (1.0.0 → 2.0.0); test xác nhận.
- **R2-2**: component-not-found chưa định nghĩa ở bước 0.5 (compare(new, None) crash) → **Resolve**: bước 0.1 read current 1 lần; None → failed sớm step=compatibility reason "component not found"; test.
- **R2-3**: CLI lookup hook + conversion dependency chưa spec → **Resolve**: CLI v1 wire skill — lookup qua `SkillManager.get`; parse dep `"id@>=1.2"` → `Dependency(name, version="1.2")`; conflict check chỉ so pin khai báo.

### R3 (minor): 6
- **R3-1**: EventType lookup bằng NAME vs value → Resolve: type_str = member name; value pattern "upgrade.<snake>".
- **R3-2**: wiring wrapper vị trí → Resolve: test-only helper (không module production); CLI emit=None.
- **R3-3**: SkillMigrator read_current None → Resolve: trả None.
- **R3-4**: exception type module → Resolve: `upgrade/errors.py` `UpgradeError`.
- **R3-5**: aios_core.metadata thừa → Resolve: bỏ khỏi allow-list.
- **R3-6**: skipped step value, exports, coverage gate → Resolve: skipped → step=None; `__init__.py` exports 12 symbols; coverage `--cov=aios_core.upgrade`.

## Verify thực tế (sau implement)
- **pytest full: 730 passed, coverage 95.00%** (trước: 689) — 41 test mới
- upgrade/ riêng: dependency 100%, backup 100%, errors 100%, pipeline 95%, migrator ~95% (sau 3 test bổ sung)
- allow-list `test_inv_upgrade_import_allowlist` pass (AST — không import runtime)
- CLI `aiagent upgrade` 7 test (success/dry-run/skipped/fail/invalid/not-found/not-wired)

## Kết luận
**APPROVED** — toàn bộ R1/R2/R3 resolved, verify bằng test thật + full suite xanh.
