# Critique-1+2 — TASK-034 (spec v1→v2)

**Critic**: orchestrator tự phản biện 2 vòng gộp (độc lập — ghi nhận)

## Vòng 1 — P1
- **C1-01 — `kinds` param type**: ctx.config["kinds"] list[str] → convert DoctorKind (validate; invalid → DoctorError).
- **C1-02 — UNKNOWN → score 0.0 phá overall**: UNKNOWN là "không biết" — chốt overall = mean các scores (UNKNOWN=0.0) + metrics đếm unknown — deterministic, ghi rõ.
- **C1-03 — DoctorResult checks_total/passed khi placeholder**: checks 0/0 + status PASS — hợp lệ (placeholder).

## Vòng 1 — P2
- C2-01 — `run_all(kinds)` signature: kinds list[DoctorKind]|None → None = tất cả (sorted theo enum order — deterministic).
- C2-02 — check fn raise → status ERROR, score 0.0, details ghi exception (deterministic).
- C2-03 — metrics: {doctors_run, passed, warning, error, unknown, checks_total, checks_passed}.

## Vòng 2 — P1
- **P1-01 — ReadinessHarness chạy checks qua DoctorChecks dùng chung** — nếu doctor harness đã đăng ký check, readiness thấy luôn. OK — 2 harnesses dùng chung `checks` instance (wiring cùng object) — chốt.
- **P1-02 — hard gate summary phải chứa "RELEASE BLOCKED" khi policy fail** (INV-022c literal + behavioral: summary chứa chuỗi).

## Vòng 2 — P2
- P2-01 — `ReadinessScorer.score(results, policy_violations=0)` — policy từ config truyền qua harness.
- P2-02 — HardGate list order deterministic: policy gate trước, overall gate sau.
- P2-03 — min_overall mặc định 0.0 (không block vô lý khi user chưa cấu hình).

## Resolve → spec v2 (implement theo)
