# TASK-078 — Evaluation (M11-P0: R2 INV-035 Verification Fail-Closed)

> Ngày: 2026-08-16 | Task: TASK-078 | Milestone: M11-P0 (Issue #4)

## Đối chiếu tiêu chí chấp nhận

| AC | Mô tả | Kết quả | Bằng chứng |
|----|-------|---------|------------|
| AC1 | 8 trạng thái + is_terminal_success chỉ PASS | ✅ | `test_state_model_has_8_states` + `test_terminal_success_only_pass` |
| AC2 | is_non_terminal/is_failure đúng | ✅ | 2 test classification |
| AC3 | normalize bảng 8×8 + cấm SKIPPED/UNKNOWN/MISSING→PASS | ✅ | 8 parametrize + 6 forbidden transitions |
| AC4 | Gate chặn non-terminal→PASS + exception→BLOCKED + default mechanisms đủ | ✅ | 4 gate tests + 2 default mechanisms tests |
| AC5 | CheckResult skipped/error → không PASS | ✅ | 4 tests + `effectively_passed` |
| AC6 | Conformance area `verification` | ✅ | conformance thật: `verification ✓ INV-035: gate chặn non-terminal→PASS` |
| AC7 | Conformance gate `gate_f_verification` PASS | ✅ | conformance thật: 6/6 gates ✓, exit=0, AIOS READY |
| AC8 | Security skip/error → không PASS | ✅ | `test_security_checker_exception_is_skipped_not_pass` + CLI security-check (0 skipped) |
| AC9 | Contract check skip/error không tính PASS | ✅ | contract check thật: breaking=0, warnings=1 |
| AC10 | CLI `verify-state` | ✅ | chạy thật: bảng 8 state + FAIL-CLOSED: YES |
| AC11 | Retroactive audit | ✅ | `implementation/audit.md` (F1–F7) |
| AC12 | Full suite xanh | ✅ | **1969 passed / 0 failed** |

**12/12 AC — TASK-078 DONE** ✅

## Đánh giá hệ thống (sau P0)

- **Verification Kernel** là nền tảng cho cả M11: R3 (P1) sẽ dùng `VerificationState` làm
  verdict cho render replay; R1/R10 (P2) sẽ dùng gate để chặn visual regression false-positive.
- **Fail-closed đã lan tỏa** tới 4 điểm: harness-execution (H2), security-check, contract-check,
  conformance (area + gate). Đây chính là yêu cầu "áp dụng đồng nhất" của proposal R2.
- **Conformance giờ có 10 areas + 6 gates** — tăng từ 9+5 của M10, không phá gate cũ.

## Bài học

1. **Test là người thầy tốt nhất**: 2 bug thật bị bắt ngay bởi unit test (thiếu ngoặc trong
   `is_terminal_success`; detect violation sau normalize). Không có test → 2 lỗi này âm thầm
   phá INV-035 ngay tại "hệ thống chống false-positive".
2. **Detect violation phải dùng raw claim, normalize phải tách khỏi detect** — trộn 2 việc
   làm mất thông tin vi phạm (C1-02/C2-01 thực sự có giá trị).
3. **Audit retroactive tốn ít nhưng giá trị cao**: 7 findings (F1–F7) đều trỏ về đúng các
   phase P1–P4 của M11 — xác nhận roadmap proposal là chính xác.

## Đề xuất cải tiến (ghi nhận — ngoài scope P0)

1. CI fail-closed gate cho visual test (R2 mở rộng) — chặn `toHaveScreenshot` skip → P4/R7
2. Missing-reference detector trong test framework → P2/R1
3. Vendor bundle hash → `aiagent security-check` → P3c/R8 (đã trong roadmap)
4. `docs/architecture/AIOS-1.0.md` + Constitution amendment INV-035 → phase compliance M11
   cuối (khi đủ các invariant P1–P4 để viết amendment tổng)

## Checklist đóng

- [x] spec.md + critique-1 (resolved) + critique-2 (resolved) + tasks.md + review.md (APPROVED)
- [x] implementation/ (verification/ package + 14 files code + audit.md + README)
- [x] test.md (30 unit + CLI thật + full suite 1969)
- [x] evaluation.md
- [x] LOG.md + PROGRESS.md cập nhật + commit
