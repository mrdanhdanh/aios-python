# TASK-021 — M4-P8 Observability & Diagnostics — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `observability/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/observability/metrics.py` — `MetricsService` (category, UPDATE row mới nhất, orphan NULL)
- `backend/src/aios_core/observability/prompt_history.py` — `PromptHistory`
- `backend/src/aios_core/observability/profiler.py` — `Profiler` (fake clock)
- `backend/src/aios_core/observability/doctor.py` — `HealthDoctor` (hooks, worst-wins)
- `backend/src/aios_core/observability/arch_scan.py` — moved từ `tests/_arch_scan.py` (SRC_ROOT parents[2], shim)
- `backend/src/aios_core/observability/arch_health.py` — `ArchitectureHealth` (rglob + collect_imports, 3 check)
- `backend/src/aios_core/observability/evaluation.py` — `EvaluationStore` (cache STARTED, CANCELLED→failed)
- `backend/src/aios_core/kernel/services/execution.py` (+5 emit: FAILED 6 nhánh `_run` + CANCELLED)
- `backend/src/aios_core/api/` (router 5 GET + 1 POST), `backend/src/aios_core/workflow/cli.py` (metrics/doctor/arch-health)

## Verification
- `pytest` full suite: **779 passed, coverage 95.11%, 10/10 AC** (xem `test.md`)
