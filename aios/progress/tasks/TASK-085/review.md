# Review — TASK-085 (M12-P1: Migration 1.0→1.1 thật — SPEC v3)

> Reviewer: AIOS Reviewer | Ngày: 2026-08-16 | Nhánh: `feature/ISSUE-7-aios-1-1-compatibility`

## Tổng quan

Task triển khai luồng migration THẬT 1.0.0→1.1.0 end-to-end (plan → backup → dry-run → validate → apply → rollback) trên dữ liệu demo: module mới `upgrade/migration_110.py` (4 transforms + `Aios110Migrator` matrix-gated), sửa bug `MigrationEngine.apply` (call backup sai signature), mở rộng CLI `migrate` (thêm `contract`, rẽ nhánh 1.0.0→1.1.0), test mới `test_migration_110.py`.

## Xác minh code thật

- **Bug C1-01 THẬT**: `migration.py:152` `self._backup.backup(f"migration:...")` (1 tham số) vs `backup.py:51` (4 tham số) → TypeError khi inject. KHÔNG test nào inject `backup_store` → bỏ dòng an toàn.
- **`--input default=None` KHÔNG phá test cũ**: `_migrate` (cli.py:721-768) không bao giờ đọc `input_file`; `test_migration.py:184-193` không truyền `--input`; `test_plugin_format` chỉ đụng `plugin_v0_to_v1` cũ.
- **Matrix khớp stub**: plugin/demo ✓; workflow/demo_flow aios_max `1.1.x` → check True ✓; contract pre-check warning (không chặn — C2-09) ✓.
- **Allow-list OK**: upgrade/* internal; `semver`/`plugins.compat`/`contracts` trong aios allow; external có `json`/`dataclasses`/`typing`/`pydantic`; KHÔNG `copy` → json round-trip đúng.

## Đối chiếu AC

12/12 AC đo được (assert cụ thể) — chi tiết trong bảng; không mâu thuẫn thiết kế chặn đường.

## Vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| R1 | Blocking (tài liệu) | "choices thêm contract" trong tasks.md C1 nếu hiểu là argparse `choices=` → `parser.error()` → `SystemExit(2)`; `main()` không bắt SystemExit → `test_cli_migrate_invalid_kind` (assert == 1) vỡ | **RESOLVED** — Spec §3.3 + tasks.md: kind giữ free-form; validate TRONG `_migrate` bằng `PLANS_110.get(kind)`/kind set → None → in lỗi + return 1. TUYỆT ĐỐI không dùng argparse choices |
| R2 | Major (tài liệu) | Spec §3.1 `PLANS_110 = {k: build_110_plan(k)}` gọi 1 tham số vs signature 2 tham số; plan không chứa component_id → vi phạm C2-04/AC9 | **RESOLVED** — `PLANS_110` = registry kind → **template** (steps + kind) dùng để validate kind + sinh plan; plan thật luôn qua `build_110_plan(kind, component_id)` (migration_id = `aios-1.0-to-1.1-{kind}-{component_id}`) |
| R3 | Minor | AC7 ghi "journal failed" nhưng hành vi thật cuối là `rolled_back` (engine.apply finish failed rồi rollback finish rolled_back) | **RESOLVED** — AC7 ghi `failed`/`rolled_back` |
| R4 | Minor | Case `aios` có nhưng `compatible` thiếu (stub 1.1) chưa rõ: seed gì trước khi append | **RESOLVED** — `compatible` thiếu → seed `[aios.get("min","1.0.0")]` rồi append `"1.1.0"` (nhất quán v0→v1) |
| R5 | Minor | `component_id` thiếu key → KeyError trần; AC9 lần 2 cùng kind chỉ contract có 2+ entry | **RESOLVED** — Thiếu key → `MigrationError` rõ; test lần 2 dùng contract (agent → capability); nhắc lại C2-05 inject journal/backup mọi unit test |

## Kết luận

- [x] **APPROVED CÓ ĐIỀU KIỆN** — R1 + R2 (sửa tài liệu, không blocking code), R3–R5 minor đã resolve.
- Không còn vấn đề blocking — sẵn sàng implement theo tasks.md (A→B→C→D→E).
