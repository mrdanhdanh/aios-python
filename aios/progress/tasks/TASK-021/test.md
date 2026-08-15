# TASK-021 — Test Results (Observability & Diagnostics, M4-P8)

**Ngày**: 2026-08-13 | **Runner**: pytest (backend/.venv) — file bổ sung hồi tố 2026-08-15 khi đóng hard gate

## Kết quả tổng
- **Full suite**: `779 passed, 0 failed` (baseline M4: 730 → +49 test mới)
- **Coverage**: 95.11% (threshold ≥80% cứng — pass)
- **Arch tests**: `test_inv_observability_import_allowlist` pass (internal: kernel.events, kernel.services, healthcheck, semver, logging; external: sqlite3/pathlib/contextlib/json/dataclasses/typing/datetime/uuid/collections/time/ast/statistics/logging)

## Test mới (49)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_metrics.py` | ~10 | MetricsService: đếm đúng; duration ghép đúng (re-run cùng execution_id → row mới nhất); orphan NULL; summary keys; persist; close() unsubscribe |
| `tests/test_prompt_history.py` | ~5 | record/list/count; sort_keys fidelity; persist |
| `tests/test_profiler.py` | ~4 | fake clock; report/clear; double-start raise |
| `tests/test_doctor.py` | ~6 | HealthDoctor worst-wins; diagnostics hooks |
| `tests/test_arch_health.py` | ~8 | ArchitectureHealth scan(package_dir=tmp) phát hiện violation module giả; healthy khi sạch; 3 check |
| `tests/test_evaluation_store.py` | ~8 | EvaluationStore: auto-record COMPLETED/FAILED/CANCELLED; duration từ cache STARTED (restart → NULL); evaluate() UPDATE row mới nhất; KeyError; average_quality; persist |
| `tests/test_execution_events.py` | ~5 | execution.py emit FAILED 6 nhánh `_run` + CANCELLED; resume + cancel trước execute KHÔNG emit |
| `tests/test_api_observability.py` | ~3 | API 5 GET + 1 POST (404 khi không có row) |
| `tests/test_cli.py` | +1 | CLI metrics/doctor/arch-health |
| `tests/test_architecture.py` | +1 | allow-list observability/ |

## Kiểm chứng AC (10/10)
- **AC1** ✅ MetricsService — đếm + duration + orphan + summary + persist + unsubscribe
- **AC2** ✅ PromptHistory — record/list/count + fidelity + persist
- **AC3** ✅ Profiler — fake clock + double-start raise
- **AC4** ✅ HealthDoctor — worst-wins + hooks
- **AC5** ✅ ArchitectureHealth — scan tmp phát hiện violation; healthy khi sạch; 3 check
- **AC6** ✅ EvaluationStore — auto-record + duration cache + evaluate + KeyError + average_quality + persist
- **AC7** ✅ execution.py emit FAILED 6 nhánh + CANCELLED; 2 nhánh KHÔNG emit; test cũ vẫn pass
- **AC8** ✅ API 5 GET + 1 POST; CLI 3 lệnh; config.yaml block
- **AC9** ✅ Allow-list AST + full pytest pass + coverage ≥80% cứng
- **AC10** ✅ git diff execution.py chỉ thêm emit

## Kết luận
- [x] Tất cả 10 AC pass
- [x] Full suite 779 pass, coverage 95.11%
