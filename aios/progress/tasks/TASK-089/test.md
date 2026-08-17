# TASK-089 — Test results (thật)

> Ngày: 2026-08-17 | Task: M13-P0 Behavioral Conformance (Issue #9)
> Môi trường: Windows, Python venv backend/.venv, pytest + coverage

## Test file mới: `backend/tests/test_harness_behavioral.py` — 54 test

| Class | Số test | Nội dung | AC |
|-------|---------|----------|----|
| TestContracts | 13 | Profile enum, PROFILE_ITERATIONS, status enum, config defaults/validators (iterations>=1, fault_iterations 1-based + dedup + requires faults), iteration summary defaults, report defaults, extra="forbid" | — |
| TestEngine | 20 | Profile resolution + override (AC1), soak duration/cap (AC2), deterministic (AC3), evidence digest (AC4), repeat + cap (AC5), fault recovery rate + fault_iterations subset (AC6), out-of-range raise (P2-3), non-recoverable → ERROR (AC11), MISMATCH → FAIL (AC13), gate expose/blocked finding (AC7), report fields (AC8), cross-run (AC15), build_baseline (AC16), scenario từ yaml (AC14) | AC1-8, 11, 13-16 |
| TestHarness | 13 | id/name/version, registry, run/verify pass, verify fail raise + persist (AC17a), not-strict (AC17b), get_report (AC9), full runner execute pass/fail-closed | AC9, 17 |
| TestWiring | 2 | Registry có behavioral + resolvable (AC9) | AC9 |
| TestCLI | 8 | PASS exit 0, FAIL exit 1, save-baseline (AC16), faults JSON, faults not list, baseline file, missing scenario file | AC10, 16 |

## Kết quả chạy thật

- **Test file mới: 54/54 PASS** (lần đầu 48 pass + 6 fail do `report.strict` không tồn tại → sửa harness.verify dùng `ctx.config.get("strict", True)` → 54/54)
- **Full suite: 2172 PASS / 0 FAIL** (baseline 2118 + 54 mới; coverage 92.93% ≥ 80%) — 0 regression (AC12)
- **5 test cũ cần cập nhật** (do thêm harness id="behavioral"):
  - `test_architecture.py::test_inv017_harness_import_allowlist` — thêm `hashlib` vào `_HARNESS_ALLOWED_EXTERNAL` (evidence digest sha256)
  - 4 test `test_harness_{benchmark,doctor,evaluation,testing}.py::TestConfigWiring::test_harness_registry_all_m6` — thêm `"behavioral"` vào set kỳ vọng
- **arch-health**: `healthy: true, violations: []` (AC12)
- **doctor**: `status: healthy` (AC12)
- **CLI thật**: `aiagent harness behavioral --scenario-file <yaml> --iterations 5` → status pass, JSON đúng, **exit 0** (AC10); scenario expect sai → status fail, exit 1

## Ghi chú

- `Fault.recoverable` mặc định True — backward-compatible, không phá `test_timeout_fault_recovers`/`test_inject_once_then_none` (đã verify trong full suite)
- Soak v1 = loop-stability test (runner thuần) — leak/latency thật thuộc M13.1
- Gate chỉ expose (finding) — gate-as-blocker thuộc M14 (deviation ghi PLAN §M13 P0)