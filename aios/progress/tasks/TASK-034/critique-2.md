# Critique-2 — TASK-034 (spec v2)

**Critic**: orchestrator tự phản biện vòng 2 (độc lập vòng 1 — ghi nhận)

## P1
- **P1-01 — 2 harnesses dùng chung `checks` instance** (wiring cùng DoctorChecks object — register check 1 lần, cả doctor + readiness thấy) ✓ chốt.
- **P1-02 — summary chứa "RELEASE BLOCKED" khi policy gate fail** (INV-022c behavioral) ✓ chốt.

## P2
- **P2-01 — scorer signature** `score(results, policy_violations=0)` ✓.
- **P2-02 — HardGate order deterministic**: policy → overall ✓.
- **P2-03 — min_overall default 0.0** ✓.

## P3
- P3-01 — DoctorHarness verify: ERROR status nào cũng raise (UNKNOWN/WARNING không raise).
- P3-02 — ReadinessReport.dimensions chỉ kinds đã chạy (không thêm kind chưa chạy với 0.0 — tránh hiểu nhầm).
- P3-03 — get_results/get_report dict (pattern H3/H4).

## Resolve → implement
