# Evaluation — TASK-021 (P8 Observability & Diagnostics)

> 2026-08-13 | đối chiếu spec v4 (10 AC) với kết quả thực tế.

## Kết quả kiểm chứng

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|------------|
| AC1 | MetricsService: đếm, duration ghép, orphan NULL, re-run row mới nhất, summary, persist, unsubscribe | ✅ | test_observability_metrics.py 7 test (counts+duration, tool+failures, orphan, rerun, untracked ignore, persist, close) |
| AC2 | PromptHistory: record/list/count, sort_keys fidelity, persist | ✅ | test_observability_prompt_history.py 4 test |
| AC3 | Profiler: fake clock, report/clear, double-start raise | ✅ | test_observability_profiler.py 5 test |
| AC4 | HealthDoctor: worst-wins, diagnostics hooks, error không crash | ✅ | test_observability_doctor.py 5 test |
| AC5 | ArchitectureHealth: scan(package_dir=tmp) violation detection, 3 check, planner exempt, policy real src | ✅ | test_observability_arch_health.py 7 test |
| AC6 | EvaluationStore: auto-record COMPLETED/FAILED/CANCELLED, duration cache, evaluate row mới nhất, KeyError, average, persist | ✅ | test_observability_evaluation.py 8 test |
| AC7 | execution.py: FAILED 6 nhánh + CANCELLED (flag + cancel giữa node); resume ×2 + cancel trước execute không emit; test cũ pass | ✅ | test_execution_failed_events.py 5 test + full suite (test_execution.py cũ pass) |
| AC8 | API 5 GET + 1 POST (404/422); CLI 3 lệnh; config.yaml block | ✅ | test_observability_api.py 7 test + CLI chạy thật (metrics/doctor/arch-health JSON đúng) |
| AC9 | Allow-list observability/ (self-package exempt) | ✅ | test_inv_observability_import_allowlist pass; full suite 779 pass, coverage 95.11% |
| AC10 | execution.py diff chỉ thêm emit | ✅ | 5 điểm emit mới, không đổi behavior (test cũ pass) |

## Thống kê
- **Tests**: 49 mới — full suite **730 → 779**, coverage 95.11%
- **Files mới**: observability/ 8 module (metrics, prompt_history, profiler, doctor, arch_scan, arch_health, evaluation, __init__) + api/routers/observability.py + 8 test files
- **Files sửa**: execution.py (+emit 5 điểm), config.py/config.yaml (ObservabilitySettings), api/app.py + wiring.py (regs["observability"]), workflow/cli.py (3 subcommand), tests/_arch_scan.py (shim), test_architecture.py (allow-list)
- **Move**: _arch_scan.py tests/ → src (1 engine, shim re-export)

## Hard gate
- Spec v1 → critique-1 (25 vấn đề, 7 P1) → v2 → critique-2 (11 vấn đề, 2 P1) → v3 → review (APPROVED có điều kiện: 3 amendment) → v4 → implement → test → evaluate → commit

## Kết luận
**TASK-021 DONE** — 10/10 AC pass, P8 Observability & Diagnostics hoàn tất (metrics, prompt history, profiler, doctor, arch health, evaluation v2 core).
