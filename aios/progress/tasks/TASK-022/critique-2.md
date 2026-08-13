# Critique ×2 — TASK-022 (critic subagent, vòng 2)

> 2026-08-13 | critic phản biện spec v2 — 2 P1 + 3 P2 + 5 P3 → spec v3.

## P1 (2) → Resolution
- **P1-1**: Supervisor trộn started_at (datetime) vs clock (float) → TypeError runtime → **Resolve**: started_ref = clock() float monotonic; expose started_at ISO từ event.timestamp (lưu cả 2).
- **P1-2**: Advisor rule 4 thiếu dependency PromptHistory trong constructor → **Resolve**: constructor nhận prompt_history; enumeration list(10000) group theo prompt_id.

## P2 (3) → Resolution
- **P2-1**: Collector không có trigger (chết trong production) → **Resolve**: wiring subscribe 3 terminal events → collect_workflow (evaluator None → no-op).
- **P2-2**: File CLI không xác định (backend/cli/ là bẫy) → **Resolve**: sửa workflow/cli.py (file CLI thật).
- **P2-3**: Thiếu critique-1.md + PROGRESS/LOG entry → **Resolve**: tạo đầy đủ hồ sơ (file này + PROGRESS/LOG).

## P3 (5) → Resolve: list_goals(limit=10000) (P3-1), task_queue_count wrap len(list_items(QUEUED)) (P3-2), running sort execution_id (P3-3), avg_quality non-None (P3-4), app.py include_router (P3-5).

## Trạng thái: RESOLVED 10/10 → spec v3
