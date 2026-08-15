# TASK-075 — Implementation + Evaluation

## Implementation
| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/observability/performance.py` | PerformanceMetrics (latency/throughput/storage, no-du) + TokenEstimate + CostEstimator (tokens/1M × cost) + CostDashboard (Workflow/Agent/Tool/Goal/Success) + CostAggregator |
| `backend/src/aios_core/workflow/cli.py` | +`aiagent cost` + `aiagent performance` |
| `backend/tests/test_performance.py` | 11 tests |

## Evaluation — 9/9 AC ĐẠT
Cost/Goal/Workflow/Agent/Tool/Success đo được offline; model independence test 3 provider.

## Bài học
- cost_per_success = total/success (0 success → None/SKIPPED) — không chia 0.
- Lệnh CLI phải tuân layer rule (scanner) — import qua container.
