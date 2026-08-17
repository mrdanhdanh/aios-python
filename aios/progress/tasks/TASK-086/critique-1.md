# Critique vòng 1 — TASK-086 (M12-P2: Backward Compatibility v0→v1 trên 1.1)

> Đối chiếu code thật: `workflow/definition.py` + `compiler.py`, `plugins/contracts.py` + `compat.py`, `ecosystem/marketplace.py`, `contracts/catalog.py` + `compatibility.py`, `extension/matrix.py`, `upgrade/migration_110.py` + `migration.py`, `upgrade/compatibility.py`, `tests/test_architecture.py:1145-1183`.

## Đánh giá chung

Mức sẵn sàng v1: **2/5**. 2 P1 (dữ liệu migrate không parse được bằng PluginManifest — lỗ hổng THẬT do TASK-085 tạo ra), 4 P2.

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C1-01 | P1 | Scenario 8 bất khả thi: `migrate_plugin_100_110` append `"1.1.0"` vào `aios.compatible` nhưng `AiosRange` (extra=forbid) không có field `compatible` → `PluginManifest` raise ValidationError — lỗ hổng tương thích THẬT do TASK-085 tạo ra | **RESOLVED** — **THÊM `compatible: list[str] = Field(default_factory=list)` vào `AiosRange`** (plugins/contracts.py — parse-only, KHÔNG đổi hành vi check min/max; `validate_manifest` không đổi); Mục tiêu 3 sửa: cho phép thay đổi **parse-only** để đảm bảo tương thích + test riêng `test_aios_range_compatible_field` |
| C1-02 | P1 | Scenario 9 cùng lỗi (MigrationFormats.plugin_v0_to_v1 sinh compatible); "hợp lệ" không định nghĩa validator | **RESOLVED** — Định nghĩa validator per kind: config → dict-check `max_duration_seconds`; workflow → `WorkflowDefinition.model_validate` PASS; plugin → `PluginManifest.model_validate` PASS (sau fix C1-01) |
| C1-03 | P2 | Allow-list cần 7 module mới (không chỉ 2) | **RESOLVED** — Thêm 7 module vào `_UPGRADE_ALLOWED_AIOS` kèm comment: `workflow.definition`, `workflow.compiler`, `plugins.contracts`, `contracts.catalog`, `contracts.compatibility`, `extension.matrix` (+ `ecosystem.marketplace` NẾU giữ scenario 4 — xem C1-04: KHÔNG cần nữa) |
| C1-04 | P2 | Scenario 4 `TrustChain.run()` fail ở bước trước compatibility (signature/permission/cert); `_in_range` private | **RESOLVED** — BỎ scenario 4 (TrustChain); THAY bằng `plugin-v1-compatible-field`: `PluginManifest` v1 (có `aios.compatible`) parse OK (kiểm chứng fix C1-01) — không kéo `ecosystem.marketplace` vào control plane |
| C1-05 | P2 | Scenario 2: "0.x" không parse được (cần semver thật); `run --simulate` chạy kernel thật; "không lỗi" mơ hồ | **RESOLVED** — Scenario 2: workflow v0 version `"0.1.0"` cụ thể + nodes task; định nghĩa "không lỗi" = `_run_simulate` trả exit 0 (completed) với YAML temp; cập nhật bảng rủi ro: scenario 2 chấp nhận kernel-sim 1 lần dữ liệu nhỏ |
| C1-06 | P2 | Scenario 7: "M8 namespace allow-list" không tồn tại trong runtime (caller truyền allow-list) | **RESOLVED** — Test 2 CHIỀU: namespace hợp lệ (`"extension"` — theo 4 namespace M8) PASS + namespace `"internal"` → `CompatibilityViolation` → check FAIL (kiểm chứng gate thật; allow-list do check định nghĩa theo PLAN §M8-E3) |
| C1-07 | P3 | Mâu thuẫn "check KHÔNG raise" vs "runner bắt exception" | **RESOLVED** — Check ĐƯỢC PHÉP raise; runner bắt mọi exception → `(False, str(exc))` |
| C1-08 | P3 | AC4/AC6 thiếu args + thiếu fixture chuẩn | **RESOLVED** — AC4 = `check_upgrade("1.0.0","1.1.0").compatible is True`; thêm fixture chuẩn v0 cho 4 loại trong spec §3.4; scenario 3 = `PluginManifest.validate_manifest(**v0)` + `check_compatibility("1.0.0","*","1.1.0")` (không chạy resolve/DB) |
| C1-09 | P3 | AC9 thiếu nguồn baseline; AC1 "≥8" mềm | **RESOLVED** — AC9 dẫn nguồn: PROGRESS.md TASK-085 (full suite 2098); AC1 = đúng **9 check, 5 kind** (danh sách cố định) |

**Kết quả: 9/9 RESOLVED — spec nâng v2. Đủ điều kiện critique vòng 2.**
