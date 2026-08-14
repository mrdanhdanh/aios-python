# Evaluation — TASK-034 (Doctor & Readiness, M6-H5)

## Tiêu chí chấp nhận (AC)
| AC | Yêu cầu | Kết quả |
|----|---------|---------|
| AC1 | Contracts: DoctorKind 13, DoctorStatus 4, DoctorResult, HardGate, ReadinessReport | ✅ extra=forbid |
| AC2 | DoctorChecks: register/run/run_all; placeholder PASS; raise → ERROR | ✅ clamp score |
| AC3 | DoctorHarness qua H1: kinds subset/all; ERROR → DoctorError; persist trước raise | ✅ |
| AC4 | strict=False → WARNING | ✅ |
| AC5 | ReadinessScorer: dimensions + overall mean (UNKNOWN → 0.0) | ✅ |
| AC6 | Hard gates: policy_violations > 0 → RELEASE BLOCKED; min_overall | ✅ PLAN hard gate |
| AC7 | ready = overall ∧ policy gates | ✅ |
| AC8 | ReadinessHarness qua H1: blocked → ReadinessError; persist trước raise | ✅ |
| AC9 | Deterministic repeat | ✅ |
| AC10 | Config + wiring register doctor + readiness (shared checks) | ✅ |
| AC11 | Arch INV-022a..d; ≥1520 tests; coverage ≥90% | ✅ 1521 tests, 95.35% |

## Critique resolution
- C1-01..03 (kinds validate; UNKNOWN → 0.0; placeholder counts) ✓
- C2-01..03 (run_all sorted; raise → ERROR; metrics counts) ✓
- P1-01..02 (shared checks instance; summary RELEASE BLOCKED) ✓
- P2-01..03 (scorer signature; gate order; min_overall default) ✓

## Metrics
- Tests: 1450 → **1521** (+71); coverage 95.31 → 95.35%
- Module mới: `harness/doctor/` 6 file (~600 LOC)
- **M6 HOÀN TẤT: 6 harnesses** — verification, test, evaluation, benchmark, doctor, readiness
- INV-017..021 (+ doctor arch INV-022) enforced

## Bài học
1. Early-return raise trước persist — arch test persist-before-raise phải dùng rfind
2. min_overall 0.0 + empty → ready True — semantics "chưa cấu hình không block"
3. Shared DoctorChecks instance — doctor/readiness nhất quán dữ liệu

## Kết luận
**TASK-034 HOÀN TẤT** — 11/11 AC, hard gate đầy đủ (spec v2 → critique ×2 → review → implement → test → evaluate). **M6 AIOS Harness: 6/6 TASK DONE (1521 tests, 95.35%).**
