# TASK-022 — M4-P8 Orchestrator v2 — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `orchestrator/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/orchestrator/advisor.py` — `ImprovementAdvisor` (5 rules deterministic + dedup)
- `backend/src/aios_core/orchestrator/supervisor.py` — `ExecutionSupervisor` (clock float, stuck, FAILED+CANCELLED)
- `backend/src/aios_core/orchestrator/evaluation_collector.py` — `EvaluationCollector` (evaluator + KeyError swallow + aggregate)
- `backend/src/aios_core/orchestrator/goals/reporting.py` — `GoalReporter` (5 status)
- `backend/src/aios_core/observability/metrics.py` (+1 method `duration_by_workflow`)
- `backend/src/aios_core/api/` (router orchestrator_v2: 4 GET)
- `backend/src/aios_core/workflow/cli.py` (advisor/supervisor)

## Key behavior
- Advisor: 5 rules → suggestion từ log/evaluation; quality None bỏ qua; dedup + sort; không dữ liệu → []
- Supervisor: theo dõi running workflows, queue, events; stuck detection
- Collector: trigger subscribe sau mỗi workflow; không crash khi evaluator raise / store KeyError
- INV-010: orchestrator/ không import `aios_core.models`

## Verification
- `pytest` full suite: **809 passed, coverage 94.92%, 8/8 AC** (xem `test.md`)
