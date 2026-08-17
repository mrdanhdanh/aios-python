# TASK-086 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-16 | Task: M12-P2 C3 Backward Compatibility (Issue #7)

## Đối chiếu 10 AC

| AC | Tiêu chí | Kết quả | Bằng chứng |
|----|----------|---------|-----------|
| AC1 | Suite đúng 9 check, 5 kind | ✅ | `test_suite_9_checks_5_kinds` (ids + kinds khớp) |
| AC2 | workflow-v0-parse: parse + compile | ✅ | check chạy OK ("parsed+compiled v0.1.0") |
| AC3 | plugin-v0-load: validate_manifest + check_compatibility | ✅ | check OK |
| AC4 | contract-v0-compat: is_compatible + check_upgrade | ✅ | check OK (minor bump) |
| AC5 | extension-v0-matrix: 2 chiều | ✅ | check OK ("extension PASS / internal gate FAIL") |
| AC6 | migrated-110-data: re-parse + round-trip compatible | ✅ | check OK + `test_plugin_manifest_v1_compatible_parses` |
| AC7 | fail-closed: Suite(checks) 1 raise → ok False, check khác vẫn chạy; bắt BaseException | ✅ | `test_fail_closed_one_check_raises` + `test_fail_closed_catches_base_exception` (SystemExit) |
| AC8 | CLI verify exit 0 + JSON thuần + passed=9; list/check không phá | ✅ | `test_cli_compat_verify` (json.loads OK) + `test_cli_compat_list_check_unchanged` |
| AC9 | AiosRange.compatible parse + min/max không đổi; 0 regression 2098 + test mới PASS; allow-list PASS | ✅ | `test_aios_range_compatible_field` + `test_aios_range_min_max_behavior_unchanged` + full suite **2109 PASS** + `test_architecture.py` PASS |
| AC10 | arch-health 0 violations; doctor healthy; không thêm invariant | ✅ | `arch-health: violations []` + doctor healthy |

**10/10 AC ĐẠT** ✅

## Điều kiện review (R1–R3) — đã đáp ứng

- R1: `_NullSink` nội bộ thay `io.StringIO()` (io không trong external allow-list) ✅
- R2: fail-closed bắt `BaseException` (SystemExit test) ✅
- R3: AC7 test bằng Suite(checks=...) inject; scenario 2 công thức `rc == 0 → (ok, detail)`; allow-list 7 module ✅

## Phát hiện quan trọng

1. **Lỗ hổng tương thích THẬT do TASK-085 tạo ra** (C1-01): `migrate_plugin_100_110` ghi `aios.compatible` nhưng `AiosRange` (extra=forbid) không có field — payload migrate KHÔNG parse lại được bằng `PluginManifest`. **ĐÃ FIX parse-only** (thêm `compatible: list[str] = Field(default_factory=list)`), check min/max không đổi — backward-compatible.
2. Fixture contract migrated thiếu `name`/`schema_ref` → test bắt được khi re-parse (validation thật có giá trị).

## Chất lượng

- `backward_compat.py`: 9 check pure (lazy import), fail-closed bắt BaseException, `_NullSink` redirect stdout scenario 2, YAML temp pathlib+uuid + finally unlink, audit db temp (code hiện có đã trỏ temp — reviewer xác nhận)
- Allow-list mở rộng 7 module có comment lý do từng cái (precedent TASK-084 C2-01)
- KHÔNG đổi hành vi runtime (chỉ parse-only fix)

## Bài học

1. **Migration ghi field mới phải kiểm tra model đọc lại** — TASK-085 ghi `aios.compatible` mà TASK-086 mới phát hiện model không chấp nhận; bộ verify chéo bắt được lỗi chính mình.
2. **External allow-list upgrade/ rất nghiêm** — `io` không có sẵn → dùng sink class nội bộ thay vì mở rộng allow-list tùy tiện.
3. **Fail-closed nên bắt BaseException** (SystemExit cũng là lỗi check).

## Kết luận

**TASK-086 DONE — 10/10 AC** — sẵn sàng C4 (TASK-087 conformance) + C5 (TASK-088 docs).
