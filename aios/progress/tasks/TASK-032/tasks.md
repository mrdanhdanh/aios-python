# Tasks — TASK-032 (H4 Evaluation Harness)

> Spec v3 (critique ×2 resolved).

- [ ] **T1** contracts.py — EvaluationKind/Metric/Suite/EvaluationItem/TrajectoryStep/Trajectory/Score/EvaluationResult/EvaluationStatus (extra=forbid; thresholds >= 0 validator P2-04)
- [ ] **T2** errors.py — EvaluationError + SuiteError
- [ ] **T3** evaluators.py — Deterministic (exact/contains/regex/numeric_ge/bool + parse fail 0.0), Semantic (Jaccard), LLM stub (item.score/params.score + reproducible), Human stub, Composite (sub_scores weighted), Engine dispatch + score (default threshold)
- [ ] **T4** trajectory.py — TrajectoryEvaluator.analyze: final_correct (step cuối output ok), warning (C3 Final Correct/Trajectory Warning), marks 5 keys, counts
- [ ] **T5** suites.py — SuiteLoader: load/load_many (list | `suites:` key), json/yaml safe_load, SuiteError, thresholds lạ bỏ qua
- [ ] **T6** evaluation.py — EvaluationHarness (id="evaluation"): run (suite+items cap, aggregate mean, trajectory đầu có steps), verify persist TRƯỚC raise (key "evaluation"), metrics rỗng → fail, strict flag, get_result
- [ ] **T7** __init__.py + config EvaluationSettings + config.yaml + wiring runtime_kernel register "evaluation"
- [ ] **T8** tests/test_harness_evaluation.py — ≥70 test (AC1..AC11): contracts 12, evaluators 20, trajectory 10, loader 8, harness 15, config/wiring 5
- [ ] **T9** arch tests INV-020e..h (no kernel/models imports, reproducible literal, EvaluationError+Engine literal, safe_load)
- [ ] **T10** Full suite: tổng ≥1370, coverage ≥90%; hồ sơ + LOG/PROGRESS + commit
