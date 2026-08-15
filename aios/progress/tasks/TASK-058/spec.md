# TASK-058 — Autonomous Experimentation (M9-P3)

## Mục tiêu
Từ M9-P2 lên A4: `Hypothesis → Experiment Design → Sandbox → Execute → Evaluate → Compare baseline → Accept/Reject` (PLAN §M9-21). **INV-033: cải thiện tự thân phải qua Experiment → Harness → Evaluation → Evidence → Decision → Deploy** — KHÔNG "LLM-says-better → production" (§M9-33). Self-improvement không thẳng production: Production → Observation → Hypothesis → Sandbox → Harness → Evaluation → Approval → Canary → Production (§M9-22).

## Phạm vi
- `autonomous/experimentation.py`: `ExperimentationEngine` — Hypothesis contract + experiment pipeline (design → execute → evaluate → compare → verdict)
- `contracts.py`: `Hypothesis` (id, statement, baseline, target_metric, target_value), `Experiment` (hypothesis_id, params, result, evidence, verdict), `ExperimentVerdict` (ACCEPTED/REJECTED/INCONCLUSIVE)

## Input/Output
- In: `run(hypothesis, params, execute_fn, evaluate_fn)`; Out: `Experiment` với verdict + evidence
- Fail-closed: thiếu baseline/target → raise `ExperimentError`

## Tiêu chí chấp nhận (AC)
1. **INV-033**: pipeline bắt buộc qua harness-evaluation — `evaluate_fn` injectable (mặc định = Harness EvaluationEngine nếu có; nếu không → REJECTED vì thiếu evidence — không tự verdict)
2. Hypothesis: id, statement, baseline (giá trị), target_metric, target_value — `extra=forbid`
3. `run()`: execute (sandbox_fn injectable) → evaluate → compare baseline → verdict ACCEPTED nếu kết quả ≥ target (hướng improvement), REJECTED nếu < baseline, INCONCLUSIVE nếu thiếu dữ liệu
4. Evidence bắt buộc trong Experiment (không verdict nếu không evidence — INV-033 tinh thần)
5. Compare deterministic: metric value vs baseline + target
6. `deploy()` chỉ cho phép khi verdict=ACCEPTED (canary flag — deploy = đánh dấu đề xuất, không tự sửa production)
7. Lịch sử experiment persist (SQLite) — audit + so sánh
8. Emit event `autonomy.experiment` mỗi experiment
9. Contract `extra=forbid`
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique ×2 resolve)
- C1-01: `Hypothesis.direction: "higher"|"lower"` — ACCEPTED khi higher ∧ value ≥ target; lower ∧ value ≤ target
- C1-02: `evaluate_fn` BẮT BUỘC qua constructor (fail-fast nếu quên wire) — verdict chỉ từ evidence
- C1-03: deploy() = đánh dấu deployed + canary trên row (KHÔNG tự sửa production)
- C1-04: persist SQLite `autonomous_experiments`
- C1-05: value None hoặc evidence rỗng → INCONCLUSIVE
- C2-01: `sandbox_fn` injectable — execute qua sandbox (KHÔNG chạy trực tiếp)
- C2-02: evidence bắt buộc key metric_value/result — thiếu → INCONCLUSIVE
- C2-03: `run(hypothesis, params)`
