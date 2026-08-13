# Critique ×1 — TASK-022 (critic subagent, vòng 1)

> 2026-08-13 | critic phản biện spec v1 — 5 P1 + 5 P2 + 4 P3 → spec v2.

## P1 (5) → Resolution
- **P1-1**: Rule 5 không implement được (MetricsService không có per-workflow duration/count) → **Resolve**: thêm `MetricsService.duration_by_workflow()` (trong scope).
- **P1-2**: Rule 4 "mà không có evaluation" không có data source → **Resolve**: đổi thành "prompt ≥ 3 renders → suggest review" (v1 chưa có prompt evaluation).
- **P1-3**: by_status "6 status" sai — GoalStatus có 5 → **Resolve**: 5 status.
- **P1-4**: collector store.evaluate() KeyError chưa xử lý → **Resolve**: bắt KeyError best-effort + AC test.
- **P1-5**: average_quality None so sánh < 0.5 → TypeError → **Resolve**: bỏ qua avg None (AC test).

## P2 (5) → Resolve: rule 3 target="" (P2-1), wiring tạo TaskQueue + hook (P2-2), bỏ catalog_count/llm_calls (P2-3), list(10000)+group (P2-4), failed_tasks = FAILED+CANCELLED (P2-5).

## P3 (4) → Resolve: supervisor không catch-up ghi giới hạn (P3-1), collect_all limit 10000 (P3-2), avg_progress gồm mọi goal (P3-3).

## Trạng thái: RESOLVED 14/14 → spec v2
