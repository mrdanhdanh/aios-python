# TASK-092 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-18 | Task: M13-P3 Trust Separation (Issue #8)
> Spec v1.1 (tích hợp critique-1 P1 + critique-2 P1-P5)

## Đối chiếu AC

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC1 | Hai score độc lập: HarnessReadinessReport + MetaReport | ✅ | TestIndependentScores |
| AC2 | ReleaseGateEngine.evaluate() pure function (không I/O) | ✅ | TestEnginePure + TestDeterminism |
| AC3 | PASS yêu cầu CẢ readiness READY + meta PASS | ✅ | TestGatePass |
| AC4 | Fail-closed: NOT_READY → BLOCKED | ✅ | TestGateBlockedReadiness |
| AC5 | Fail-closed: FAIL → BLOCKED | ✅ | TestGateBlockedTrust |
| AC6 | ReleaseGateReport shape + no timestamp + extra="forbid" | ✅ | TestReportShape |
| AC7 | Harness id="release" + registry + lifecycle + round-trip | ✅ | TestHarness + TestWiring (10 harness) |
| AC8 | Fail-closed (INV-035): strict + BLOCKED → ReleaseGateError → DIAGNOSED | ✅ | TestHarness.test_full_runner_execute_diagnosed |
| AC9 | CLI exit 0 (PASS) / 1 (BLOCKED) + JSON | ✅ | TestCLI + CLI thật exit 0 |
| AC10 | Full suite + arch-health + doctor | ✅ | 2254 PASS; arch-health 0; doctor healthy |
| AC11 | Determinism: evaluate 2 lần identical | ✅ | TestDeterminism |
| AC12 | Tách biệt thật: 2 path BLOCKED độc lập (AC4+AC5) | ✅ | TestSeparationReal |

**12/12 AC đạt.**

## Đánh giá hệ thống

- **Release Gate pure combiner** (PLAN §M13-P3): engine chỉ nhận 2 report + AND → tách biệt thật giữa System Readiness và Harness Trust ✅
- **Fail-closed thật**: Bất kỳ score nào fail → BLOCKED → release blocked. Sub-harness fail → BLOCKED (không crash) ✅
- **Tách biệt thật (AC12)**: 2 path BLOCKED độc lập — readiness NOT_READY nhưng trust PASS → BLOCKED; trust FAIL nhưng readiness READY → BLOCKED → chứng minh 2 score thực sự independent ✅
- **4 invariant track giữ nguyên**: FAIL-CLOSED ✅ (fail-closed release gate) · INDEPENDENT VERIFICATION ✅ (meta independent + release combiner) · PERMISSION BOUNDARY — M14 · CERTIFIED BASELINE/ROLLBACK — M14

## Bài học

1. **Real coverage harness luôn READY** (code constants) → fake sub-harnesses cần thiết cho BLOCKED-path tests. Nếu dùng real harness với empty registry → vẫn READY → test sai.
2. **Pure combiner pattern** rất mạnh cho trust separation: engine không biết cách tính score, chỉ tổ hợp. → Dễ test, dễ thay thế, dễ reason về correctness.
3. **Sub-harness fail → BLOCKED** (fail-closed): release gate LUÔN ra verdict, không bao giờ crash. Try/except → coi như FAIL → BLOCKED.

## Đề xuất cải tiến

- TASK-093 (P4): Docs & ADR — ADR Harness Trust + behavioral spec + PLAN §M13
- M14: Human Approval + Permission Broker boundary (Certified Baseline + Rollback)
- M15: Autonomous Harness (autonomy policy + trust budget)
