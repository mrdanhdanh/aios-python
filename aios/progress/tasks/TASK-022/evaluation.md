# Evaluation — TASK-022 (Orchestrator v2)

> 2026-08-13 | đối chiếu spec v4 (8 AC) với kết quả thực tế.

## Kết quả kiểm chứng

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|------------|
| AC1 | ImprovementAdvisor 5 rules + None quality skip + dedup/sort + empty | ✅ | test_advisor.py 8 test (empty, low quality, None ignore, failures, tool failures, prompts, slow, dedup) |
| AC2 | ExecutionSupervisor: tracking + stuck (fake clock) + close + queue hook | ✅ | test_supervisor.py 7 test (running/finished, failed+cancelled, stuck ×2, queue, close, no execution_id) |
| AC3 | EvaluationCollector: evaluator gắn quality, no evaluator noop, error + KeyError swallow, aggregate | ✅ | test_evaluation_collector.py 5 test |
| AC4 | GoalReporter: 5 status, avg_progress, failed=FAILED+CANCELLED, detail, deterministic | ✅ | test_goal_reporter.py 6 test |
| AC5 | API 4 endpoint GET 200 + 404 | ✅ | test_orchestrator_v2_api.py 4 test (suggestions, snapshot, report, detail+404) |
| AC6 | CLI advisor/supervisor chạy thật (JSON) + db suffix convention | ✅ | CLI chạy thật OK; R2-1 resolved (kèm bypass fix _metrics) |
| AC7 | INV-010 giữ (không import models); full suite + coverage | ✅ | test_architecture pass; 809 pass, coverage 94.92% |
| AC8 | Không sửa goal.py/task_queue.py/execution.py | ✅ | git status: chỉ app/wiring/metrics/cli + module mới |

## Thống kê
- **Tests**: 30 mới — full suite **779 → 809**, coverage 94.92%
- **Files mới**: orchestrator/advisor.py, supervisor.py, evaluation_collector.py, goals/reporting.py + api/routers/orchestrator_v2.py + 5 test files
- **Files sửa**: metrics.py (+duration_by_workflow), app.py (+router), wiring.py (+orchestrator_v2, TaskQueue wire, collector trigger), cli.py (advisor/supervisor + bypass fix _metrics), .gitignore (+backend/aios/, *.db.*)

## Hard gate
- Spec v1 → critique-1 (14 vấn đề, 5 P1) → v2 → critique-2 (10 vấn đề, 2 P1) → v3 → review (APPROVED có điều kiện: 1 R2 + 3 R3) → v4 → implement → test → evaluate → commit
- Bypass: 1 entry `[bypass]` (fix _metrics db suffix — R2-1) ghi LOG

## Kết luận
**TASK-022 DONE** — 8/8 AC pass, Orchestrator v2 hoàn tất (Improvement Advisor, Execution Supervisor, Evaluation Collector, Goal Manager nâng cao — báo cáo).
