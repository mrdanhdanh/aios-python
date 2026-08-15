# TASK-060 — Autonomous Evaluation (M9-P3)

## Mục tiêu
Biến M6 Harness Evaluation thành **decision mechanism** (PLAN §M9-25): `Evaluation { correctness · quality · cost · risk · progress · confidence } → Decision { continue / retry / replan / stop / ask_human }`. Agent evaluation phải đánh giá cả trajectory và outcome (§M9-25). **Progress Estimator** (§M9-26): `Goal completion · Confidence · Risk · Budget remaining` — 3 iterations không tăng progress → STUCK → replan.

## Phạm vi
- `autonomous/evaluation.py`: `AutonomousEvaluator` — evaluation composite → decision; `ProgressEstimator` — completion/confidence/risk/budget-remaining
- `contracts.py`: `EvaluationDimensions` (6 field), `AutonomousVerdict` (5 decision), `ProgressEstimate`

## Input/Output
- In: dimensions + history (progress sequence); Out: decision + estimate
- Fail-closed: thiếu dimensions → raise

## Tiêu chí chấp nhận (AC)
1. `evaluate(dimensions)` trả `AutonomousVerdict` deterministic — 5 giá trị
2. Decision rules: correctness thấp → RETRY; cost/risk cao → ASK_HUMAN; progress không tăng 3 iterations → REPLAN; confidence cao + correctness cao → CONTINUE; budget cạn → STOP
3. ProgressEstimator: completion % từ progress hiện tại + tổng; confidence = min(các confidence); risk = max(rủi ro); budget_remaining = 1 - cost/budget
4. STUCK detect: 3 iterations liên tiếp không tăng progress → progress_stuck=True
5. Trajectory: `trajectory_warning` nếu có tool fail/recovery trong evidence (đánh dấu dù final đúng — §M9-25)
6. Deterministic (không LLM mặc định — thresholds injectable)
7. Contract `extra=forbid`
8. Emit event `autonomy.decision` khi quyết định
9. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique ×2 resolve)
- C1-01: thứ tự rules — (1) budget cạn → STOP; (2) risk cao → ASK_HUMAN; (3) correctness thấp → RETRY; (4) progress stuck → REPLAN; (5) → CONTINUE
- C1-02: `trajectory_evidence: dict` (tool_failures/recovery_count) — >0 → warning
- C1-03: ProgressEstimator giữ progress_history; stuck khi 3 giá trị cuối bằng nhau; reset()
- C1-04: 6 scalar 0..1; confidence tổng = min(correctness, quality, confidence)
- C1-05: event {goal_id, verdict, progress, stuck}
- C2-01: cost = tỷ lệ dùng/budget (clamp 1); cost ≥ 1.0 → STOP
- C2-02: ProgressEstimator class riêng (không God Object)
- C2-03: `EvaluationConfig(correctness_min=0.7, risk_max=0.8, cost_max=1.0)` injectable
