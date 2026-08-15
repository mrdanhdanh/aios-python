# TASK-060 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Decision rules mâu thuẫn nhau (correctness thấp + cost cao)?
Thứ tự ưu tiên rules phải deterministic.
→ **Resolve**: thứ tự: (1) budget cạn → STOP; (2) risk cao → ASK_HUMAN; (3) correctness < threshold → RETRY; (4) progress stuck 3 iterations → REPLAN; (5) còn lại → CONTINUE. Rule đầu thắng.

## C1-02 (P2) — Trajectory warning từ đâu?
→ **Resolve**: dimensions có `trajectory_evidence: dict` (VD {"tool_failures": 2}) — warning nếu tool_failures > 0 hoặc recovery_count > 0. Đơn giản, deterministic.

## C1-03 (P2) — Progress stuck: 3 iterations không tăng — ai theo dõi sequence?
→ **Resolve**: ProgressEstimator giữ `progress_history: list[float]` (append mỗi estimate); stuck khi len ≥ 3 và 3 giá trị cuối bằng nhau (không tăng). `reset()` cho goal mới.

## C1-04 (P3) — confidence/risk là scalar?
→ **Resolve**: `EvaluationDimensions(correctness, quality, cost, risk, progress, confidence)` — 6 scalar 0..1 (cost/risk cao = 1). Confidence tổng = min(correctness, quality, confidence).

## C1-05 (P3) — Event payload?
→ **Resolve**: {goal_id, verdict, progress, stuck} — đủ cho observability.

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
