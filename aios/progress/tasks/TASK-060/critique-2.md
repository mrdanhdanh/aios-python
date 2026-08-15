# TASK-060 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Budget cạn — nguồn từ đâu (governor)?
→ **Resolve**: dimensions.cost = tỷ lệ cost dùng / budget (0..1, có thể >1 → clamp 1). STOP khi cost ≥ 1.0 (cạn) — deterministic, không cần governor trực tiếp (governor vẫn là gate chính; evaluator là decision support).

## C2-02 (P2) — ProgressEstimator độc lập hay trong evaluator?
→ **Resolve**: `ProgressEstimator` class riêng (tách trách nhiệm — không God Object); AutonomousEvaluator nhận estimator (mặc định tạo mới).

## C2-03 (P3) — Thresholds injectable?
→ **Resolve**: `EvaluationConfig(correctness_min=0.7, risk_max=0.8, cost_max=1.0)` — injectable qua constructor.

## Kết luận
Resolve xong — spec đủ chặt.
