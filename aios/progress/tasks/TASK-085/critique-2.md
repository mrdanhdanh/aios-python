# Critique vòng 2 — TASK-085 (M12-P1: Migration 1.0→1.1 thật)

> Đối chiếu: spec v2 + resolution 15/15 (critique-1) + code thật (`upgrade/migration.py`, `upgrade/compatibility.py`, `upgrade/backup.py`, `workflow/cli.py`, `tests/test_migration.py`, `tests/test_architecture.py:1145-1183`, `tests/test_upgrade_cli.py`).

## Đánh giá chung

Spec v2 khắc phục phần lớn lỗ hổng vòng 1; **15/15 resolution vòng 1 đều khả thi trên code thật** (xác minh: C1-01 bug `migration.py:143` thật + không test nào inject backup_store; C1-02b config fail-closed đúng; C1-05 `test_migration.py:169` giữ format cũ bắt buộc). Mức sẵn sàng v2: **3/5** — còn 1 P1 + 5 P2.

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C2-03 | P1 | Transform/rollback plugin mâu thuẫn với dữ liệu đã qua v0→v1 (`compatible=["1.0.0"]`): "thiếu → thêm" no-op thì post-check fail; "append" thì rollback guard `== [min,"1.1.0"]` không khớp | **RESOLVED** — Transform: nếu `"1.1.0" ∉ compatible` → **append** `"1.1.0"` (giữ phần tử gốc; `aios` thiếu → setdefault + min default "1.0.0"). Rollback: **xóa `"1.1.0"` khỏi compatible** (khôi phục đúng trạng thái trước transform). Post-check: `"1.1.0" in compatible`. Test: `compatible=["1.0.0"]` → migrate → rollback → `["1.0.0"]` |
| C2-01 | P2 | Pre-check range không áp dụng được cho config (payload không version) | **RESOLVED** — Config skip CẢ range lẫn matrix (chỉ transform + post-check marker); range check chỉ cho plugin/workflow/contract; test tường minh `migrate config ... --apply` payload tùy ý vẫn qua |
| C2-02 | P2 | `--input` default `"-i.json"` → không phân biệt cấp file vs default | **RESOLVED** — Đổi parser migrate `--input default=None` (kiểm tra test cũ an toàn — `test_migration.py:184-193` không truyền --input); None → stub; có giá trị → đọc JSON, file lỗi → exit 1 rõ ràng |
| C2-04 | P2 | `migration_id` cố định per-kind chặn migrate lần 2 cùng kind (idempotent) | **RESOLVED** — `migration_id = f"aios-1.0-to-1.1-{kind}-{component_id}"` (component_id theo C1-11); config singleton `"config"` chấp nhận 1 lần |
| C2-05 | P2 | Unit test `Aios110Migrator()` mặc định ghi journal/backup DB thật | **RESOLVED** — Bắt buộc inject: `MigrationJournal(":memory:")` hoặc tmp + `BackupStore(tmp)` trong MỌI unit test; không đổi default engine (tránh phá test cũ) |
| C2-06 | P2 | Rollback sau post-check fail: payload truyền vào không xác định | **RESOLVED** — Gọi `engine.rollback(plan, result)` với result = payload đã transform từ `engine.apply`; Aios110Result case fail = payload đã rollback + `journal_status="rolled_back"` + backup_id GIỮ LẠI (audit — có chủ đích, không xóa); test: post-check fail → payload == bản gốc |
| C2-07 | P3 | AC6 "payload version 1.1.0" sai cho plugin (version không đổi) | **RESOLVED** — AC6 per-kind: plugin → `"1.1.0" in aios.compatible` (version giữ nguyên); workflow/contract → `version == "1.1.0"`; config → migration marker |
| C2-08 | P3 | Test hồi quy C1-01 yếu (không test inject backup_store) | **RESOLVED** — Thêm test: inject backup fake (ghi nhận call) → `engine.apply` KHÔNG gọi backup, journal completed; giữ param `backup_store` (compat, không dùng — ghi chú) |
| C2-09 | P3 | "matrix post ok" khi có warning chưa định nghĩa | **RESOLVED** — `ok` = compatible=True (warning không chặn — đúng fail-closed); CLI in kèm warnings nếu có; `Aios110Result.matrix` thêm field `warnings` |

**Kết quả: 9/9 RESOLVED — spec nâng v3. Đủ điều kiện tasks.md + review.**
