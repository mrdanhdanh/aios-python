# TASK-022 — tasks.md (breakdown checklist)

> Chuỗi hard gate: spec → critique ×2 → tasks → review → implement → test → evaluate → commit

## Checklist

| # | Bước | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| 1 | Spec v1 → v3 (critique-1 14 vấn đề, critique-2 10 vấn đề) | done | — |
| 2 | tasks.md | done | file này |
| 3 | Review (reviewer subagent) | todo | — |
| 4 | metrics.py + duration_by_workflow() | todo | GROUP BY name |
| 5 | Implement orchestrator/advisor.py — ImprovementAdvisor 5 rules | todo | deterministic, dedup |
| 6 | Implement orchestrator/supervisor.py — ExecutionSupervisor | todo | clock float, stuck |
| 7 | Implement orchestrator/evaluation_collector.py | todo | evaluator + KeyError |
| 8 | Implement orchestrator/goals/reporting.py — GoalReporter | todo | 5 status |
| 9 | api/routers/orchestrator_v2.py + app.py + wiring | todo | 4 endpoint + TaskQueue wire + collector trigger |
| 10 | CLI advisor/supervisor (workflow/cli.py) | todo | — |
| 11 | Test 5 files + full suite | todo | — |
| 12 | Evaluation + PROGRESS/LOG + commit | todo | — |
