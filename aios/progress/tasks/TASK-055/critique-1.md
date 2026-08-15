# TASK-055 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Circuit breaker trạng thái global hay per-fingerprint?
Breaker chung cho mọi lỗi thì 1 lỗi ồn ào chặn cả hệ thống; per-fingerprint thì phức tạp.
→ **Resolve**: breaker per-fingerprint (v1): `{fingerprint: fail_count}`; open khi count ≥ threshold; cooldown_s sau đó reset. Không global.

## C1-02 (P2) — Strategy scoring cụ thể?
→ **Resolve**: score deterministic: RETRY=1.0, FALLBACK=0.7, ALTERNATIVE=0.5, ESCALATE=0.0; policy deny → score 0 (bỏ qua). Chọn score cao nhất còn khả thi.

## C1-03 (P2) — Verify sau execute thế nào?
→ **Resolve**: `verifier: Callable[[str], bool]` injectable (mặc định True — deterministic); mặc định này chỉ dùng test; production wiring truyền verifier thật.

## C1-04 (P3) — Escalate trả gì?
→ **Resolve**: `RecoveryOutcome(recovered=False, escalated=True, reason="no feasible strategy")` — không raise (escalation là outcome hợp lệ).

## C1-05 (P3) — Fingerprint hash?
→ **Resolve**: `sha256(error_type + "|" + message)[:16]` — deterministic, đủ chống trùng.

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
