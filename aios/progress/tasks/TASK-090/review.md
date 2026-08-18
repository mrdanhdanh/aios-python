# Review — TASK-090 (M13-P1: Harness Coverage) — Pre-implementation Review

> Review trước implement — 2026-08-17
> Spec v3 (19 AC — tích hợp resolution critique-1 3 P1/6 P2/3 P3 + critique-2 2 P1/8 P2/10 P3) + tasks.md breakdown.

## Đánh giá tổng quan

Task xây dựng **Harness Coverage model** — 9 chiều (Component/Contract/State/Transition/Event/Failure-mode/Scenario/Verification-path/Artifact) + 8 negative-path + **Harness Readiness scorer** (7 dimensions + hard gates). Auto-collect từ code thật (registry/lifecycle/verdict/faults/GOLDEN_SCENARIOS) + declared lists có evidence kiểm chứng tồn tại (anchored backend root — cwd-independent). **Fail-closed thật**: v1 trả NOT_READY (replay gate 0.5 < 0.75) cho tới khi TASK-091 cover đủ.

## Kiểm tra spec

- **Mục tiêu khớp PLAN §M13-5b/6**: coverage model 9 chiều + negative-path + readiness scoring (Structural/Contract/Behavioral/Failure/Replay/Scenario/Production) ✅
- **Auto-collect đối chiếu code thật**: VerificationState 8 ✅ · TRANSITIONS 12 edges ✅ · GOLDEN_SCENARIOS 20 ✅ · HarnessRunStatus 8 ✅ · Verdict 4 ✅ · FaultType 3 ✅ · registry 7 harness ✅ · runner emit 6 phase ✅ · artifact events/report ✅
- **Evidence cwd-independent** (P1-A): module evidence + path anchored `aios_core.__file__.parents[2]` ✅
- **Fail-closed**: replay gate 0.5 < 0.75 → NOT_READY; production 0.0 + conditional; verify raise → DIAGNOSED (P1-B) ✅
- **Không phá kiến trúc**: KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant; INV-020b (os cấm — importlib/pathlib OK) ✅

## Điểm cần lưu ý khi implement

1. **R1 (review)**: Evidence anchored — `Path(aios_core.__file__).resolve().parents[2] / "tests"` — phải đúng backend root (parents: aios_core→src→backend).
2. **R2 (review)**: Transition total = 12 (edges) — đếm từ TRANSITIONS dict.
3. **R3 (review)**: Failure-mode = 8 (3 fault + 5 errors) — include cả 5 HarnessError subclasses.
4. **R4 (review)**: Event = 6 phase emit thật (preparing/validating/running/verifying/completed/failed) — KHÔNG dùng hook names.
5. **R5 (review)**: Artifact = events/report (2 kind thật) — KHÔNG dùng evidence/verdict.
6. **R6 (review)**: HarnessReadinessScorer param validation (0,1] → ValueError; production_tests_available bool).
7. **R7 (review)**: verify() persist TRƯỚC raise (pattern các harness khác); hard_gates dùng HardGate typed (doctor/contracts).
8. **R8 (review)**: AC11 — DIAGNOSED (default) / FAILED (diagnose_on_failure=False) — test cả 2 nhánh.

## Kết luận

- [x] **APPROVED** — spec v3 đủ chặt, tasks.md đủ chi tiết, không còn P1/P2 chưa resolve. Được phép implement.