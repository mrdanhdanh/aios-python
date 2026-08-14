# Critique-2 — TASK-032 (spec v2)

**Critic**: orchestrator tự phản biện vòng 2 (độc lập vòng 1 — ghi nhận)

## P1
- **P1-01 — Trajectory trong EvaluationResult khi item không có trajectory**: Trajectory.steps rỗng → analyze trả marks all False, final_correct None, warning False. Chốt: aggregate trajectory per item; EvaluationResult.trajectory = trajectory của item ĐẦU TIÊN có steps (deterministic) hoặc None nếu không item nào — ghi counts trong metrics.
- **P1-02 — `items` đặt ở ctx.config["dataset"]** — nhưng Suite.dataset là tên dataset (string). Xung đột naming? Chốt: ctx.config["items"] = list[EvaluationItem]; Suite.dataset = tên tham chiếu (metadata). Sửa §3.6.

## P2
- **P2-01 — Engine.evaluate semantic threshold**: SemanticEvaluator trả similarity float (không pass/fail) — Score.passed = value >= threshold ✓ (engine.score chung). OK.
- **P2-02 — Human/LLM stub score từ params.get("score")** — nhưng Metric.params là per-metric; per-item score khác nhau thì sao? Chốt: item dict có key `score` override khi kind LLM_JUDGE/HUMAN (item-level); metric.params.score là default. Engine.evaluate nhận item dict → ưu tiên item["score"].
- **P2-03 — EvaluationResult.scores là aggregate** — mỗi Score 1 metric; counts trong metrics: items_total, items_passed, metrics_total, metrics_passed, inconclusive.
- **P2-04 — threshold float validation** — Suite.thresholds value >= 0 (pydantic field_validator).

## P3
- **P3-01 — TrajectoryStep.tool required khi kind=="tool"** — không enforce (chấp nhận None, deterministic).
- **P3-02 — get_result trả dict** (pattern H3 P3-05).
- **P3-03 — config.yaml block** `evaluation:`.
- **P3-04 — arch INV-020e dùng dir_imports rglob evaluation/**. 
