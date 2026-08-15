# TASK-032 — M6-H4 Evaluation Harness — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `harness/evaluation/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/harness/evaluation/contracts.py` — EvaluationKind 5 + Metric/Suite (thr validator >=0)/EvaluationItem (trajectory+score)/TrajectoryStep/Trajectory/Score (kind default)/EvaluationResult/Status + extra=forbid
- `backend/src/aios_core/harness/evaluation/errors.py`
- `backend/src/aios_core/harness/evaluation/evaluators.py` — Deterministic (exact|contains|regex|numeric_ge|bool parse-fail 0.0) + Semantic (Jaccard) + LLM stub (item.score/params, reproducible: model/prompt_version/temperature) + Human stub + Composite (weighted sub_scores) + Engine dispatch/score default threshold
- `backend/src/aios_core/harness/evaluation/trajectory.py` — `TrajectoryEvaluator` final_correct last-output + warning deny/failed/recovery + marks 5 keys
- `backend/src/aios_core/harness/evaluation/suites.py` — loader dict/json/yaml safe_load + thresholds lạ drop
- `backend/src/aios_core/harness/evaluation/evaluation.py` — `EvaluationHarness` id=evaluation run suite+items cap max_items + aggregate mean bỏ None + INCONCLUSIVE → fail + trajectory item đầu + persist TRƯỚC raise + strict + get_result
- `backend/src/aios_core/config.py` — `EvaluationSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring register "evaluation"

## Key behavior
- Evaluation Model: Deterministic → Semantic → LLM Judge → Human → Composite (LLM Judge không mặc định — INV-020 determinism)
- Trajectory Evaluation: Final Correct / Trajectory Warning (gọi sai tool → deny → retry → đúng)

## Verification
- `pytest` full suite: **1387 passed, coverage 95.27%, 12/12 AC** (xem `test.md`)
