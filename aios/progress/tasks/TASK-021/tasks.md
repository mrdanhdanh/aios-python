# TASK-021 — tasks.md (breakdown checklist)

> Chuỗi hard gate: spec → critique ×2 → tasks → review → implement → test → evaluate → commit

## Checklist

| # | Bước | Trạng thái | Ghi chú |
|---|------|-----------|---------|
| 1 | Spec v1 → v3 (3 vòng: critique-1 25 vấn đề, critique-2 11 vấn đề) | done | — |
| 2 | tasks.md | done | file này |
| 3 | Review (reviewer subagent) | todo | — |
| 4 | Move _arch_scan.py → observability/arch_scan.py + shim tests/_arch_scan.py + SRC_ROOT parents[2] | todo | — |
| 5 | Implement observability/metrics.py — MetricsService | todo | category, UPDATE row mới nhất, orphan NULL |
| 6 | Implement observability/prompt_history.py — PromptHistory | todo | sort_keys |
| 7 | Implement observability/profiler.py — Profiler | todo | fake clock, double-start raise |
| 8 | Implement observability/doctor.py — HealthDoctor | todo | hooks diagnostics |
| 9 | Implement observability/arch_health.py — ArchitectureHealth | todo | rglob + collect_imports |
| 10 | Implement observability/evaluation.py — EvaluationStore + Evaluator | todo | CANCELLED→failed |
| 11 | Sửa execution.py — emit FAILED 6 nhánh + CANCELLED vòng lặp | todo | — |
| 12 | config.py + config.yaml — ObservabilitySettings | todo | — |
| 13 | api/routers/observability.py (5 GET + 1 POST) + wiring + app.py | todo | — |
| 14 | CLI doctor/metrics/arch-health | todo | lazy import |
| 15 | Test 8 files + allow-list | todo | — |
| 16 | Evaluation + PROGRESS/LOG + commit | todo | — |
