# TASK-078 — Test (M11-P0: INV-035 Verification Fail-Closed)

> Ngày: 2026-08-16 | Chạy trên nhánh `feature/ISSUE-4-m11-deterministic-runtime`

## Unit tests

| Suite | Kết quả | Ghi chú |
|-------|---------|---------|
| `tests/test_verification.py` (30 tests) | ✅ **30/30 PASS** | AC1–AC5 + AC8 + mechanism thật (AC4b) |
| Regression: `test_harness_execution.py` + `test_security.py` + `test_certification.py` | ✅ **127/127 PASS** | AC12 subset; `test_gate_definitions` cập nhật +gate_f_verification |

## CLI thật (AC6–AC10)

| Lệnh | Kết quả | AC |
|------|---------|-----|
| `aiagent verify-state` | Bảng 8 state đúng; 3 mechanism thật PASS; **FAIL-CLOSED: YES** | AC10 ✓ |
| `aiagent conformance` | 10/10 areas (có `verification` — chặn mock non-terminal→PASS); 20/20 GS; **6/6 gates** (có `gate_f_verification`); **AIOS 1.0 READY**; exit=0 | AC6, AC7 ✓ |
| `aiagent security-check` | 9/11 pass · 2 warn · 0 fail · **0 skipped** → SECURE | AC8 ✓ |
| `aiagent contract check` | Breaking changes: 0 · Warnings: 1 | AC9 ✓ |

## Full suite (AC12)

- [x] **1969 passed / 0 failed** (62.84s) — baseline M10 1939 + 30 test mới `test_verification.py`; không regression

## Bugs phát hiện trong quá trình implement (đã fix)

1. `is_terminal_success()` thiếu ngoặc — trả string thay vì bool (test bắt được)
2. `VerificationGate.check_all()` normalize TRƯỚC detect → violation không bao giờ xuất hiện;
   fix: detect trên raw claim (state non-terminal + verdict PASS) trước normalize
