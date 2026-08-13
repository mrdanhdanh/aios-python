# TASK-021 — M4-P8: Observability & Diagnostics (metrics, prompt history, profiler, doctor, arch health, evaluation v2)

**Metadata**: TASK-021 | M4/P8 | 2026-08-13 | v4 (sau review — APPROVED có điều kiện: C1/C2/C3 amended) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/observability/` (control plane)

## 1. Mục tiêu
Triển khai P8 Observability & Diagnostics theo PLAN.md: "metrics, audit log, prompt history, simulation mode, system doctor, performance profiler, health score, evaluation framework v2 (gắn vào workflow)". Audit log + health score + simulation đã có — bổ sung phần còn lại, deterministic (INV-010), event-driven (INV-009).

## 2. Phạm vi
**In**: `observability/` (metrics.py, prompt_history.py, profiler.py, doctor.py, arch_scan.py, arch_health.py, evaluation.py) + `kernel/services/execution.py` (**CHỈ thêm emit FAILED/CANCELLED — P1-1 v1**) + `config.py`/`config.yaml` (ObservabilitySettings) + `api/routers/observability.py` (5 GET + 1 POST feedback) + wiring + `workflow/cli.py` (doctor/metrics/arch-health) + move `tests/_arch_scan.py` → `observability/arch_scan.py` (shim ở tests) + test_architecture.py (allow-list + docstring).
**Out**: không sửa models/agents; không tự động đề xuất (TASK-022); không backfill từ audit; **quality/feedback write qua API POST** (P2-3 resolved).

## 3. Kiến trúc

### 3.1 metrics.py — MetricsService
- `MetricsService(bus: EventBus, db_path)`: subscription tổng `bus.subscribe(None, handler)`.
- Bảng SQLite `metrics(id INTEGER PK AUTOINCREMENT, category TEXT, name TEXT, execution_id TEXT, node_id TEXT, started_at TEXT, finished_at TEXT, duration_ms REAL)` — pattern chuẩn.
- **`category` (P3-1 v2)**: `"workflow"` | `"tool"` — KHÔNG dùng event type (finish type khác start type). `name`: workflow → plan_id; tool → node_name.
- START events (WORKFLOW_STARTED/TOOL_STARTED) → INSERT (category, name, execution_id, node_id, started_at=event.timestamp, finished_at NULL).
- Finish events (WORKFLOW_COMPLETED/FAILED/CANCELLED, TOOL_FINISHED) → UPDATE row **mới nhất chưa finish** (P2-2 v2):
  `UPDATE metrics SET finished_at=?, duration_ms=? WHERE category=? AND execution_id=? AND node_id IS ? AND finished_at IS NULL AND id = (SELECT MAX(id) FROM metrics WHERE category=? AND execution_id=? AND node_id IS ? AND finished_at IS NULL)`
  (workflow: node_id NULL → dùng `IS NULL` — P3-1 v2; tool: node_id từ payload).
- **Orphan STARTED** → duration NULL — `average_duration` bỏ qua; test cover.
- API: `counts()`, `average_duration(category) -> float | None`, `slowest(category, limit=5)`, `recent(limit=20)` (timestamp desc), `summary()` (keys: counts, avg_duration_ms, tool_failures — TOOL_FINISHED ok=false, total).
- `close()` unsubscribe. Audit (EventService) = source of truth; metrics = aggregate cache.

### 3.2 prompt_history.py — PromptHistory
- Bảng `prompt_history(id PK, prompt_id, version, variables_json, output, duration_ms, created_at)`.
- `record(prompt_id, version, variables, output, duration_ms=None) -> int` — `json.dumps(variables, sort_keys=True)`.
- `list(prompt_id=None, limit=100)` (created_at desc); `count()`. Caller (API/CLI) gọi explicit — không sửa registry.

### 3.3 profiler.py — Profiler
- `ProfileSection(name, section, duration_ms)`; `profile(name, section)` context manager + start/stop (`time.perf_counter`); `Profiler(clock=None)` fake clock; `report()`, `clear()`; double-start cùng key → ValueError.

### 3.4 doctor.py — HealthDoctor (tránh trùng agents.SystemDoctor)
- `HealthDoctor(health_registry, diagnostics: list[Callable[[], dict]], metrics_summary: Callable[[], dict] | None = None)` — **hooks từ wiring, KHÔNG import skills/catalog/prompts**.
- `report() -> DoctorReport(status: HealthStatus, checks: list[HealthReport], diagnostics: dict, timestamp)` — worst-wins từ healthcheck.py.
- Default diagnostics (wiring): registry counts (skills/prompts/catalog/workflow library qua hooks), db sizes, audit count, metrics summary.

### 3.5 arch_scan.py + arch_health.py
- **Move** `tests/_arch_scan.py` → `observability/arch_scan.py`: **SRC_ROOT = `Path(__file__).resolve().parents[2]`** (P1-1 v2 — parents[2] = backend/src khi file ở src/aios_core/observability/; KHÔNG thêm "/ src"). Giữ nguyên collect_imports/module_imports/dir_imports API.
- `tests/_arch_scan.py` = shim `from aios_core.observability.arch_scan import *` — cập nhật docstring test_architecture.py: "tests NEVER import aios_core at runtime (except arch_scan shim — pure stdlib, no side effects)" (P3-4 v2). `aios_core/__init__.py` import nặng → chấp nhận (không fail, chỉ collection chậm hơn).
- `arch_health.py`: `ArchitectureHealth.scan(package_dir: Path) -> ArchReport(healthy, violations: list[ArchViolation(kind, module, message)], timestamp)` — **tự rglob + `collect_imports(module_rel, package_dir)` KHÔNG dùng dir_imports** (P1-2 v2 — dir_imports hardcode SRC_ROOT, relative_to raise với path ngoài src).
- Checks (subset khớp test_architecture):
  1. `layer`: agents/ → {aios_core.kernel.services, aios_core.tools}; workflow/ → {langgraph, aios_core.models}; orchestrator/ → {aios_core.models} (trừ planner); capabilities/ → {aios_core.models, aios_core.workflow, aios_core.tools}
  2. `contract`: contracts/ → {aios_core.kernel.services, aios_core.kernel.events}
  3. `policy`: execution.py AST Attribute self._policy.evaluate (như test_inv007)

### 3.6 evaluation.py — Evaluation framework v2 core
- `WorkflowEvaluation` dataclass: execution_id, workflow_id, success: bool, duration_ms, quality, feedback, created_at. **workflow_id := plan_id — opaque string, KHÔNG parse prefix** (P3-5 v2).
- `Evaluator` Protocol: `evaluate(...) -> EvaluationVerdict(quality, feedback)`.
- `EvaluationStore(bus, db_path)`: subscribe **WORKFLOW_STARTED/COMPLETED/FAILED/CANCELLED** (C1 — R1-1) → giữ `{execution_id: started_at}` in-memory, xóa khi finish; duration = finish - start (restart giữa chừng → NULL — nhất quán orphan). **Semantics (P2-4 v2)**: COMPLETED → success=true; FAILED/CANCELLED → success=false. `counts()` keys: {success, failed, total} — failed = FAILED + CANCELLED.
- `evaluate(execution_id, quality, feedback)` — UPDATE row **mới nhất** theo execution_id (P2-2 v2); chưa có row → KeyError.
- `list(workflow_id=None, limit=100)`; `average_quality(workflow_id=None) -> float | None`.

### 3.7 execution.py emit mới (P1-1 v1 + P2-1 v2 + C2 — R1-2/R2-1)
- Emit `WORKFLOW_FAILED {execution_id, plan_id, reason}` tại **mọi nhánh trả FAILED trong `_run`** (6 nhánh): policy rejected, approval required, resource unavailable ×2, node fail, exception (P2-1 v2).
- Emit `WORKFLOW_CANCELLED {execution_id, plan_id, reason}` tại: cancel đầu vòng lặp node (flag set) VÀ node fail với `result == "cancelled"` (cancel giữa node — R2-1).
- **2 nhánh `resume()` (no snapshot state / state node ids mismatch) KHÔNG emit** — xảy ra TRƯỚC WORKFLOW_STARTED (tránh orphan FAILED) (R1-2). Cancel trước execute → KHÔNG emit (P3-2 v2).
- `plan` trong scope ở mọi điểm EMIT (verified). KHÔNG đổi behavior khác.

### 3.8 API + CLI + config
- `config.py`: `ObservabilitySettings(db_path="aios/data/observability.db")` + config.yaml.
- `api/routers/observability.py`: GET `/api/v1/observability/metrics`, `/prompt-history?limit=`, `/doctor`, `/arch-health`, `/evaluations?workflow_id=&limit=` + **POST `/evaluations/{execution_id}/feedback` {quality, feedback}** (P2-3 v2) → 404 nếu execution_id không có row.
- CLI: `aiagent doctor` (HealthDoctor JSON), `aiagent metrics` (summary; DB rỗng → zeros), `aiagent arch-health` (ArchReport JSON) — lazy import.
- Wiring xây service từ settings; observability→workflow/cli import OK (không vi phạm INV-003).

## 4. AC
- AC1: MetricsService — đếm đúng; duration ghép đúng (kể cả re-run cùng execution_id → row mới nhất); orphan NULL; summary keys; persist; close() unsubscribe
- AC2: PromptHistory — record/list/count; sort_keys fidelity; persist
- AC3: Profiler — fake clock; report/clear; double-start raise
- AC4: HealthDoctor — worst-wins; diagnostics hooks
- AC5: ArchitectureHealth — scan(package_dir=tmp) phát hiện violation module giả; healthy khi sạch; 3 check
- AC6: EvaluationStore — auto-record COMPLETED (success=true) + FAILED/CANCELLED (success=false); duration từ cache STARTED (restart → NULL); evaluate() UPDATE row mới nhất; chưa có row → KeyError; average_quality; persist
- AC7: execution.py — emit FAILED ở 6 nhánh trong `_run` + CANCELLED (flag đầu vòng lặp + cancel giữa node); 2 nhánh resume() + cancel trước execute KHÔNG emit; test cũ vẫn pass (gồm test_cli.py — R2-3)
- AC8: API 5 GET + 1 POST (404 khi không có row); CLI 3 lệnh; config.yaml block
- AC9: allow-list observability/ — internal: {kernel.events, kernel.services, healthcheck, semver, logging} (**trừ self-package aios_core.observability*** — R2-2); external: {sqlite3, pathlib, contextlib, json, dataclasses, typing, datetime, uuid, collections, time, ast, statistics, logging}; test_inv_observability_import_allowlist; full pytest pass + **coverage ≥ 80% cứng** (95% = mục tiêu soft — R3-5)
- AC10: execution.py diff chỉ thêm emit (verify git diff)

## 5. Test
- test_observability_metrics.py, test_observability_prompt_history.py, test_observability_profiler.py, test_observability_doctor.py, test_observability_arch_health.py, test_observability_evaluation.py, test_observability_api.py, test_execution_failed_events.py, **test_cli.py (C3 — R2-3: doctor output mới giữ key "kernel": "ok")**, test_architecture.py (allow-list + shim pass)

## 6. Ghi chú (quyết định qua critique ×2 + review)
- SRC_ROOT = parents[2] (P1-1 v2); arch_health tự rglob + collect_imports (P1-2 v2)
- Emit FAILED chỉ trong `_run` 6 nhánh; resume() ×2 không emit; cancel giữa node → CANCELLED (R1-2/R2-1)
- EvaluationStore duration qua cache STARTED in-memory (C1/R1-1)
- UPDATE row mới nhất chưa finish (P2-2 v2); category thay type (P3-1 v2); node_id IS NULL cho workflow
- POST feedback endpoint (P2-3 v2); CANCELLED → failed (P2-4 v2); plan_id opaque (P3-5 v2)
- observability không dùng logging riêng — bus log lỗi handler; shim kéo runtime → docstring cập nhật (P3-3/4 v2)
- `__init__.py` exports (R3-1); regs["observability"] expose services (R3-2); policy check skip khi thiếu file (R3-3); summary() total = tổng rows (R3-4); handler filter đúng 6 event types (R3-7); shim import tường minh 4 tên (R3-6)
- No backfill; audit = source of truth
