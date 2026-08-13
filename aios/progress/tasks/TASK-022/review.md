# Review — TASK-022 (reviewer subagent)

> 2026-08-13 | reviewer review spec v3: **APPROVED có điều kiện** — 1 R2 + 3 R3 → resolve vào spec v4 → implement → verify.

## Findings & Resolution
- **R2-1**: CLI db_path convention chưa pin — `aiagent advisor` đọc DB khác wiring (bug tiềm ẩn cả `_metrics()` TASK-021) → **Resolve**: pin suffix convention (db_path + ".metrics"/".evals"/".prompts"); **bypass fix `_metrics()`** (ghi LOG `[bypass]`).
- **R3-1**: CANCELLED đếm vào đâu → **Resolve**: recent_failed (FAILED + CANCELLED).
- **R3-2**: thứ tự subscribe collector vs EvaluationStore → **Resolve**: pin build orchestrator_v2 SAU observability.
- **R3-3**: stuck sort → **Resolve**: stuck = subset running đã sort.

## Verify thực tế (sau implement)
- **pytest full: 809 passed, coverage 94.92%** (trước: 779) — 30 test mới
- advisor 8 test (5 rule + None quality + dedup/sort + empty), supervisor 7, collector 5, goal_reporter 6, API 4
- CLI `aiagent advisor`/`supervisor` chạy thật OK (JSON)
- AC8: git diff — chỉ app.py/wiring.py/metrics.py/cli.py + module mới; **goal.py/task_queue.py/execution.py KHÔNG đổi**

## Kết luận
**APPROVED** — toàn bộ R2/R3 resolved + verify test thật + CLI thật.
