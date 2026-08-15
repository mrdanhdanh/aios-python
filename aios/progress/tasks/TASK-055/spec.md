# TASK-055 — Autonomous Recovery (M9-P2)

## Mục tiêu
Từ retry/fallback/report (M4) thành **Autonomous Recovery**: `Detect → Classify → Diagnose → Generate strategies → Score → Policy check → Execute → Verify` (PLAN §M9-15). Recovery KHÔNG retry vô hạn: retry budget · failure fingerprint · circuit breaker · cooldown · escalation (§M9-16).

## Phạm vi
- `autonomous/recovery.py`: `AutonomousRecovery` — fingerprint (signature lỗi), CircuitBreaker (open/close theo fail count + cooldown), strategy generation + scoring deterministic, verify sau execute, escalation
- `contracts.py`: `FailureEvent` (execution_id, error_type, message, at), `RecoveryPlan` (strategies[], chosen, executed, verified), `RecoveryStatus`

## Input/Output
- In: `recover(failure)` → Out: `RecoveryOutcome` (recovered: bool, strategy, attempts, escalated)
- Fail-closed: không strategy khả thi → escalate (không tự ý hành động)

## Tiêu chí chấp nhận (AC)
1. Fingerprint: cùng error_type + message hash → cùng fingerprint (deterministic)
2. Circuit breaker: N fail liên tiếp (threshold injectable) → OPEN (dừng retry, cooldown); sau cooldown → HALF/CLOSED
3. Retry budget: attempts > max_retries → escalate (KHÔNG retry vô hạn)
4. Strategies deterministic, scored (retry < fallback < alternative theo policy); policy deny strategy → bỏ qua
5. Execute strategy → verify (callable) — fail → strategy kế tiếp; hết → escalate
6. Cooldown: sau escalation/circuit open, recovery chờ cooldown_s trước khi thử lại
7. Emit event `autonomy.recovery` mỗi attempt
8. Fingerprint map: cùng lỗi → strategy lặp lại không chọn (tránh lặp vô ích)
9. Contract `extra=forbid`
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique ×2 resolve)
- C1-01: breaker **per-fingerprint** (không global); open khi count ≥ threshold
- C1-02: score RETRY=1.0, FALLBACK=0.7, ALTERNATIVE=0.5, ESCALATE=0.0; policy deny → 0
- C1-03/C2-02: verifier injectable (mặc định True); thành công → reset count breaker
- C1-04: escalate = outcome hợp lệ (không raise)
- C1-05: fingerprint = sha256(error_type+"|"+message)[:16]
- C2-01: recover() check breaker trước — OPEN → escalated sớm
- C2-03: cooldown_until = now + cooldown_s; hết cooldown → CLOSED
