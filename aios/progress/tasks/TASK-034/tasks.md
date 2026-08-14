# Tasks + Review — TASK-034 (Doctor & Readiness)

## Tasks
- [ ] **T1** contracts.py — DoctorKind 13, DoctorStatus 4, DoctorResult, HardGate, ReadinessReport
- [ ] **T2** errors.py — DoctorError + ReadinessError(DoctorError)
- [ ] **T3** checks.py — DoctorChecks: register/run/run_all (None = tất cả, sorted enum); placeholder PASS; fn raise → ERROR
- [ ] **T4** doctor.py — DoctorHarness (id="doctor"): run (kinds validate), verify persist TRƯỚC raise, strict, get_results
- [ ] **T5** readiness.py — ReadinessScorer (dimensions, overall mean UNKNOWN→0.0, hard gates policy→overall, ready, RELEASE BLOCKED summary) + ReadinessHarness (id="readiness", persist trước raise, get_report)
- [ ] **T6** __init__ + config DoctorSettings + config.yaml + wiring register doctor + readiness (shared checks)
- [ ] **T7** tests/test_harness_doctor.py — ≥65 test (AC1..AC10): contracts 10, checks 10, doctor 15, scorer 18, readiness 12, config/wiring 5
- [ ] **T8** arch tests INV-022a..d (no kernel impl; 13 kinds; RELEASE BLOCKED literal; errors + persist-before-raise)
- [ ] **T9** Full suite ≥1520, coverage ≥90%; hồ sơ + LOG/PROGRESS + STATS + commit

## Review (tự — đối chiếu code thật)
- H1..H4 patterns đã chứng minh (persist trước raise, registry, strict flag) ✓
- Allow-list: doctor/ cần kernel.services.state + logging + harness intra ✓ KHÔNG MOD; external có sẵn ✓
- Observability/doctor.py M4 KHÔNG đụng — scope riêng harness/doctor/ ✓
- **Kết luận: APPROVED có điều kiện** — 0 R1; resolve P1/P2/P3 vào implement.
