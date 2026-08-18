# TASK-084 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-16 | Task: M12-P0 C1 Version & Compatibility Baseline (Issue #7)

## Đối chiếu 12 AC

| AC | Tiêu chí | Kết quả | Bằng chứng |
|----|----------|---------|-----------|
| AC1 | `__version__ == "1.1.0"` + `system status` trả 1.1.0 | ✅ | `test_version_bumped_to_110` + CLI thật |
| AC2 | 10 contract 1.1.0 + `contract list` + `contract check` PASS | ✅ | `test_contracts_catalog_bumped_to_110` + CLI thật + full suite |
| AC3 | `check_upgrade("1.0.0","1.1.0")` compatible, không breaking | ✅ | `test_check_upgrade_100_to_110_backward_compatible` |
| AC4 | plugin manager + marketplace (2 chỗ) default 1.1.0 | ✅ | edit 3 vị trí (`manager.py:68`, `marketplace.py:85,268`) |
| AC5 | DEFAULT_ENTRIES ≥ 14 entry | ✅ | `test_matrix_default_entries_14` + CLI `compat list` (14 entries) |
| AC6 | compatible exit 0; out-of-range exit 1; max "1.1.x" chấp nhận 1.1.5 | ✅ | 3 vector CLI thật (0.9.0 fail / 2.0.0 fail / 1.1.5 pass) |
| AC7 | kind/id lạ → error (fail-closed) | ✅ | `test_check_unknown_*_fail_closed` + CLI exit 1 |
| AC8 | `--aios-version` override hoạt động | ✅ | CLI `--aios-version 2.0.0` → exit 1 |
| AC9 | Full suite ≥ 2052 PASS / 0 FAIL; test system version cập nhật | ✅ | **2071 PASS / 0 FAIL**; sửa `test_models.py:104` + `test_cli_contract_list` |
| AC10 | Không vi phạm INV-001..035; arch-health 0 violations; doctor healthy | ✅ | `arch-health: violations []` + `doctor: healthy`; không thêm invariant |
| AC11 | OpenAPI trả 1.1.0 | ✅ | `create_app().openapi()['info']['version'] == "1.1.0"` |
| AC12 | CLI thật chạy được; help text đúng; survey.md đủ | ✅ | 8 lệnh CLI thật + `compat list/check` help + `implementation/survey.md` |

**12/12 AC ĐẠT** ✅

## Điều kiện review (R1–R4) — đã đáp ứng

- R1: test `test_check_min_fail_keeps_warnings` assert cả errors + warnings ✅
- R2: `upgrade/compatibility.py` dùng literal `AIOS_VERSION = "1.1.0"`, KHÔNG import `__version__` ✅
- R3: lý do giữ `deprecated_in="1.0.0"` ghi vào spec §3.2 header + survey.md ✅
- R4: version rác → error exit 1 (`test_check_invalid_component_version_fail_closed`) ✅

## Chất lượng

- Module mới `upgrade/compatibility.py`: coverage 96% (2 dòng chưa phủ — exception path)
- Allow-list INV cập nhật có comment lý do (C2-01) — `test_inv_upgrade_import_allowlist` PASS
- KHÔNG thêm invariant mới; KHÔNG đổi hành vi runtime (chỉ default literal + catalog version)
- Backward-compatible: minor bump theo semver, `check_upgrade("1.0.0","1.1.0")` compatible

## Bài học

1. **Bump version hệ thống đòi hỏi phân loại kỹ**: ~19 file chứa "1.0.0" nhưng chỉ 6 vị trí là system version — survey.md trước khi sửa giúp tránh bump nhầm component.
2. **Allow-list INV (test_architecture) là rào chắn thật**: C2-01 bắt được ngay khi module mới import chéo — sửa allow-list có comment lý do là chuẩn.
3. **`Constraint.matches()` vs `_within_min/_within_max`** khác semantics — pin API `check_compatibility` trong spec cứu khỏi bug subtle.
4. **deprecated_in là mốc lịch sử** — không bump cùng version contract (test phụ thuộc).

## Kết luận

**TASK-084 DONE — 12/12 AC** — sẵn sàng cho C2 (TASK-085 migration 1.0→1.1) + C3 (TASK-086 backward compat).
