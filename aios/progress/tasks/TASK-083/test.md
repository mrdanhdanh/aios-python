# TASK-083 — Test results (M11-P4a/b: R5 SkillDistiller + R7 Static Deploy)

> **Ngày**: 2026-08-16 | **Runner**: pytest (backend/.venv)

## Unit tests — `tests/test_m11_p4.py` (18 tests)

| # | Test | Kết quả |
|---|------|---------|
| 1 | test_r5_distill_report (AC1) | ✅ PASS |
| 2 | test_r5_manifest_valid (AC4) | ✅ PASS |
| 3 | test_r5_capability_extraction_deterministic (AC5) | ✅ PASS |
| 4 | test_r5_different_url_different_skill (AC5) | ✅ PASS |
| 5 | test_r5_license_ok_when_mit (AC2) | ✅ PASS |
| 6 | test_r5_license_warn_when_missing (AC2) | ✅ PASS |
| 7 | test_r5_fetch_fail_fail_closed (AC3) | ✅ PASS |
| 8 | test_r5_empty_tree_fail_closed (AC3) | ✅ PASS |
| 9 | test_r5_no_overwrite (AC3) | ✅ PASS |
| 10 | test_r5_stub_deterministic (AC5) | ✅ PASS |
| 11 | test_r7_verify_ok (AC7) | ✅ PASS |
| 12 | test_r7_verify_missing_dir_blocked (AC7) | ✅ PASS |
| 13 | test_r7_verify_empty_dir_blocked (AC7) | ✅ PASS |
| 14 | test_r7_manifest_deterministic (AC8) | ✅ PASS |
| 15 | test_r7_deploy_dry_run_no_files (AC9) | ✅ PASS |
| 16 | test_r7_deploy_apply_writes_marker (AC9) | ✅ PASS |
| 17 | test_r7_deploy_apply_merge_no_overwrite (AC9) | ✅ PASS |
| 18 | test_r7_deploy_blocked_when_invalid (AC9) | ✅ PASS |

**18/18 PASS**

## CLI thật

| Lệnh | Kết quả |
|------|---------|
| `aiagent skill distill <url> --out <dir>` (AC6) | ✅ Distilled OK — license warn + capabilities (animation, sprite) + manifest hợp lệ |
| `aiagent deploy --static <dir>` (AC10) | ✅ dry-run — files/bytes/sha256, không tạo file |
| `aiagent deploy --static <dir> --apply` (AC10) | ✅ marker `.aios/deploy.json` tạo đúng |

## Regression (AC11)

- Full suite: **2052 passed / 0 failed** (baseline 2034 + 18 mới)
- Fix arch rule: `ecosystem/distiller.py` bỏ import `skills.base` (allow-list M8 chỉ cho semver/metadata) — dùng `semver.parse_version` + mirror validation

## Health check phase P4

- `aiagent doctor` → healthy · `aiagent arch-health` → 0 violations
- `aiagent conformance` → **AIOS 1.0 READY** (10 areas + 20/20 GS + 6 gates ✓ — có verification INV-035 + gate_f_verification)
