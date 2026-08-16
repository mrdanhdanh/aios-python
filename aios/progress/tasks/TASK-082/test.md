# TASK-082 — Test results (M11-P3b/c/d: R6 + R8 + R12)

> **Ngày**: 2026-08-16 | **Runner**: pytest (backend/.venv)

## Unit tests — `tests/test_m11_p3bcd.py` (16 tests)

| # | Test | Kết quả |
|---|------|---------|
| 1 | test_r6_creative_pre_route_build_game (AC1) | ✅ PASS |
| 2 | test_r6_creative_pre_route_pixel_art (AC1) | ✅ PASS |
| 3 | test_r6_no_creative_matcher_falls_through (AC2) | ✅ PASS |
| 4 | test_r6_backend_request_unchanged (AC2) | ✅ PASS |
| 5 | test_r6_creative_matcher_empty_suggestion_no_match (AC2) | ✅ PASS |
| 6 | test_r6_workflows_registered_and_compile (AC3) | ✅ PASS |
| 7 | test_r8_vendor_integrity_hash_match_pass (AC4) | ✅ PASS |
| 8 | test_r8_vendor_integrity_hash_mismatch_fail (AC4) | ✅ PASS |
| 9 | test_r8_vendor_integrity_missing_file_fail (AC4) | ✅ PASS |
| 10 | test_r8_no_config_is_pass (AC5) | ✅ PASS |
| 11 | test_r8_twelve_checks_total (AC5) | ✅ PASS |
| 12 | test_r12_ingest_full_description (AC7) | ✅ PASS |
| 13 | test_r12_mock_deterministic (AC8) | ✅ PASS |
| 14 | test_r12_different_image_different_description (AC8) | ✅ PASS |
| 15 | test_r12_missing_image_fail_closed (AC9) | ✅ PASS |
| 16 | test_r12_merge_params_no_overwrite (AC8) | ✅ PASS |

**16/16 PASS**

## CLI thật

| Lệnh | Kết quả |
|------|---------|
| `aiagent security-check` (AC5/AC6) | ✅ 12 checks — `vendor_integrity` hiển thị "no vendor bundles pinned → PASS" |
| `aiagent reference describe <image>` (AC10) | ✅ Mock vision trả description (scene/style/objects/palette/raw) |
| `aiagent reference describe <missing>` (AC9) | ✅ ERROR "reference image not found" + exit 1 (fail-closed INV-035) |

## Regression (AC11)

- Fix 1 test cũ `test_security.py::test_has_11_items` (11 → 12 items — R8 có chủ đích)
- Full suite: **2034 passed / 0 failed** (baseline 2018 + 16 mới)

## Health check phase

- `aiagent doctor` → `status: healthy, kernel: ok`
- `aiagent arch-health` → `healthy: true, violations: []`
