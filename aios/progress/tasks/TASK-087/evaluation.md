# TASK-087 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-16 | Task: M12-P3 C4 Compatibility Conformance (Issue #7)

## Đối chiếu 8 AC

| AC | Tiêu chí | Kết quả | Bằng chứng |
|----|----------|---------|-----------|
| AC1 | `AreaChecks.compatibility()` string "compatibility" (KHÔNG đổi enum — `test_9_areas` vẫn PASS) | ✅ | `test_area_compatibility_exists_in_run_all` (11 areas) + test_9_areas PASS |
| AC2 | Area PASS khi matrix ≥ 14 + verify 9/9 + version 1.1.0 (evidence cả 3) | ✅ | `test_area_compatibility_pass` (evidence: `matrix=14 entries, verify=9/9, version=1.1.0`) |
| AC3 | Area FAIL fail-closed khi verify fail (monkeypatch Suite) | ✅ | `test_area_compatibility_fail_closed` (status FAIL + evidence) |
| AC4 | `release_gates(areas=None)`: reuse precomputed (không double-run) + None → chạy thật + exception → False | ✅ | `test_gate_g_reuses_precomputed_areas` + `test_gate_g_standalone` + `test_gate_g_exception_fail_closed` |
| AC5 | Conformance 11 areas + 7 gates; test_gate_definitions cập nhật; 10/6 cũ không regression | ✅ | `test_conformance_11_areas_7_gates` + test_gate_definitions (7 gates, all PASS) + full suite |
| AC6 | CLI exit 0 + header "AIOS Conformance 1.1" + "AIOS 1.1 READY" + area hiển thị + help 11/7 | ✅ | `test_cli_conformance_compat` + CLI thật (7 gates, READY, exit 0) + help |
| AC7 | Full suite ≥ 2109, 0 regression + test mới PASS; test_certification cập nhật PASS | ✅ | **2118 PASS / 0 FAIL** (2109+9) |
| AC8 | arch-health 0 violations; doctor healthy; không thêm invariant | ✅ | arch-health violations=0 (fix import root — layer rule) |

**8/8 AC ĐẠT** ✅

## Điều kiện review (R2-1, R3-1, R3-2) — đã đáp ứng

- R2-1: docstring `cli.py:842` + `contracts.py:66` → 1.1 ✅
- R3-1: monkeypatch đúng module `aios_core.upgrade.backward_compat` ✅
- R3-2: docstring module conformance "5 release gates" → 7 ✅

## Bug/phát hiện trong lúc implement

1. **Layer rule cấm import root `aios_core` từ harness** — `from ... import __version__` trong `compatibility()` tạo violation arch-health (C2-01 reviewer cảnh báo "relative an toàn" nhưng arch_health runtime scanner vẫn bắt root import). **ĐÃ FIX**: dùng `from ...upgrade.compatibility import AIOS_VERSION` (không import root; upgrade import hợp lệ).
2. Evidence fail-closed là exception message (không phải tên exception) — test assert đúng chuỗi.

## Chất lượng

- `release_gates(areas=None)` reuse kết quả precomputed → compat verify chạy ĐÚNG 1 lần mỗi conformance (C2-02)
- Header + result → "AIOS Conformance 1.1 / AIOS 1.1 READY" nhất quán
- KHÔNG đổi enum CertificationArea (giữ precedent M11); `test_9_areas` nguyên vẹn

## Bài học

1. **"Relative import an toàn" cần kiểm chứng bằng arch-health thật** — allow-list test (AST) và runtime scanner (arch_health) có thể khác nhau; luôn chạy cả 2.
2. **Reuse kết quả precomputed** tránh double-run side-effect (simulate chạy 2 lần).
3. Conformance version hiển thị phải đồng bộ (header + result).

## Kết luận

**TASK-087 DONE — 8/8 AC** — sẵn sàng C5 (TASK-088 docs & ADR).
