# Evaluation — TASK-032 (Evaluation Harness, M6-H4)

## Tiêu chí chấp nhận (AC)
| AC | Yêu cầu | Kết quả |
|----|---------|---------|
| AC1 | Contracts: EvaluationKind 5, Metric, Suite, EvaluationItem, Trajectory(Step), Score, EvaluationResult/Status | ✅ extra=forbid + thresholds >= 0 |
| AC2 | DeterministicEvaluator: exact/contains/regex/numeric_ge/bool; parse fail → 0.0 | ✅ |
| AC3 | SemanticEvaluator Jaccard deterministic; LLM stub + reproducible; Human stub | ✅ |
| AC4 | CompositeEvaluator weighted mean (sub_scores) | ✅ |
| AC5 | Engine dispatch + Score (None → inconclusive; default threshold) | ✅ |
| AC6 | TrajectoryEvaluator: Final Correct / Trajectory Warning (denied/failed/recovery) | ✅ marks 5 keys |
| AC7 | SuiteLoader: dict/json/yaml safe_load; SuiteError; thresholds lạ bỏ qua | ✅ |
| AC8 | EvaluationHarness qua H1: run+verify; strict raise; persist trước raise; get_result | ✅ pattern H2/H3 |
| AC9 | INCONCLUSIVE score → passed_all False | ✅ |
| AC10 | Reproducible fields LLM_JUDGE; rỗng deterministic | ✅ INV-020 |
| AC11 | Config + wiring register "evaluation" | ✅ |
| AC12 | Arch INV-020e..h; ≥1370 tests; coverage ≥90% | ✅ 1387 tests, 95.27% |

## Critique resolution
- C1-01..03 (EvaluationItem, aggregate mean + counts, default threshold) ✓
- P1-01..02 (trajectory item đầu có steps; ctx.config["items"]) ✓
- P2-01..04 (item.score override, counts, thresholds validator) ✓
- R2-1..2 (numeric_ge parse cả 2; mean bỏ None) ✓

## Metrics
- Tests: 1299 → **1387** (+88); coverage 95.26 → 95.27%
- Module mới: `harness/evaluation/` 7 file (~700 LOC)
- 4 harnesses đăng ký: verification, test, evaluation

## Bài học
1. Pydantic field bắt buộc không default → ValidationError tại runtime — test phát hiện ngay
2. Registry test phải cập nhật theo milestone tiến độ (assert chính xác tập hiện tại)
3. Trajectory warning đúng tinh thần PLAN: final correct nhưng có deny/failed/recovery → warning

## Kết luận
**TASK-032 HOÀN TẤT** — 12/12 AC, hard gate đầy đủ (spec v3 → critique ×2 → review → implement → test → evaluate).
