# Critique-1 — TASK-032 (spec v1)

**Critic**: orchestrator tự phản biện vòng 1 (độc lập — ghi nhận)

## P1
- **C1-01 — dataset items schema chưa chốt**: §3.6 "list[dict {input, output, expected, trajectory}]" — output bắt buộc? expected bắt buộc? Chốt: input/output/expected bắt buộc (ValidationError qua pydantic model `EvaluationItem` trong contracts), trajectory optional. Thêm model.
- **C1-02 — aggregate scores per metric với threshold khác nhau**: nhiều item → mean score per metric; Score.passed = mean >= threshold. Chốt rõ: aggregate là mean; item-level score không cần lưu (chỉ aggregate) — hoặc lưu counts (metric_items, metric_passed_items). Lưu counts deterministic.
- **C1-03 — threshold mặc định khi metric không có trong thresholds**: dùng EvaluationSettings.default_threshold (0.8) — chốt ở engine.score (params truyền threshold). Không có threshold → default.

## P2
- **C2-01 — `numeric_ge` expected là số** — so float(output) >= float(expected); parse fail → 0.0.
- **C2-02 — regex invalid pattern → 0.0** (catch re.error).
- **C2-03 — CompositeEvaluator params.sub_scores** (list[dict {metric,value,weight}]) — weighted mean; không có → None.
- **C2-04 — Engine.score cần expected/input đầy đủ** — signature `score(metric, input_, output, expected, threshold)`.
- **C2-05 — trajectory step cuối "output"**: final_correct = step cuối có kind=="output" và ok==True; không có output step → final_correct None.
- **C2-06 — EvaluationHarness dataset cap max_items** (slice deterministic) — settings.max_items.
- **C2-07 — Suite.metrics rỗng** → không score nào → passed_all False (không PASS khi không có gì) — chốt.

## P3
- **C3-01 — Trajectory marks keys**: final_correct, trajectory_warning, had_recovery, had_denied, had_failed_tool — deterministic bool.
- **C3-02 — summary per status**: PASSED/FAILED/INCONCLUSIVE prefix.
- **C3-03 — reproducible chỉ khi kind==LLM_JUDGE** — else {}.
- **C3-04 — EvaluationStatus enum: PASSED/FAILED/INCONCLUSIVE** — status từ passed_all + inconclusive count.
