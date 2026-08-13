# TASK-022 — M4-P8: Orchestrator v2 (Improvement Advisor, Execution Supervisor, Evaluation Collector, Goal Manager nâng cao)

**Metadata**: TASK-022 | M4/P8 | 2026-08-13 | v4 (sau review — APPROVED có điều kiện: R2-1 + R3×3 resolved) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/orchestrator/` (control plane)

## 1. Mục tiêu
Triển khai Orchestrator v2 theo PLAN.md: "Improvement Advisor (tự đề xuất skill/workflow/prompt mới từ log + evaluation), Execution Supervisor nâng cao, Evaluation Collector đầy đủ, Goal Manager nâng cao (progress tracking + báo cáo)". Deterministic (INV-010 — không LLM trong advisor v1), event-driven (INV-009), tái sử dụng EvaluationStore/MetricsService (TASK-021).

## 2. Phạm vi
**In**: `orchestrator/advisor.py` (ImprovementAdvisor), `orchestrator/supervisor.py` (ExecutionSupervisor), `orchestrator/evaluation_collector.py` (EvaluationCollector), `orchestrator/goals/reporting.py` (GoalReporter) + `observability/metrics.py` (**+1 method `duration_by_workflow()` — P1-1**) + wiring (TaskQueue wire — P2-2) + API router `/api/v1/orchestrator-v2` + CLI `aiagent advisor`/`supervisor` + test_architecture.py (INV-010 giữ).
**Out**: không LLM; không tự động áp dụng đề xuất (chỉ tạo suggestion); không sửa goal.py/task_queue.py/execution.py (git diff verify).

## 3. Kiến trúc

### 3.1 advisor.py — ImprovementAdvisor
```python
@dataclass(frozen=True)
class Suggestion:
    kind: str          # workflow | prompt | skill | capability
    action: str        # create | improve | review
    target: str        # tên component liên quan ("" nếu không xác định)
    reason: str
    evidence: dict     # số liệu (failures, avg_quality, duration...)

class ImprovementAdvisor:
    def __init__(self, evaluation_store, metrics_service, prompt_history) -> None: ...
    def suggest(self) -> list[Suggestion]
```
- Rules deterministic (chạy tuần tự, 0..n suggestion mỗi rule):
  1. **workflow quality thấp**: workflow có ≥ 2 evaluations, `avg_quality is not None and avg_quality < 0.5` → suggest improve workflow (P1-5 — bỏ qua workflow quality None).
  2. **workflow fail nhiều**: workflow ≥ 3 evaluations và failed/total > 0.5 → suggest review workflow.
  3. **tool failures**: `metrics.tool_failures() >= 3` → suggest review capability, **target = ""** (không xác định tool nào — P2-1).
  4. **prompt chưa có đánh giá**: prompt có ≥ 3 renders → suggest review prompt — đếm qua `prompt_history.list(limit=10000)` group theo prompt_id (P1-2 v2 — v1 chưa có prompt evaluation).
  5. **workflow chậm**: `metrics.duration_by_workflow()` (P1-1 — method MỚI: trả {name: (avg_ms, count)}) — workflow count ≥ 3 và avg > 10_000 ms → suggest improve workflow (performance).
- Enumerate: `evaluation_store.list(limit=10000)` + group bằng Python (P2-4).
- Sort: (kind, target, action); dedup (kind, target, action).

### 3.2 supervisor.py — ExecutionSupervisor
```python
@dataclass(frozen=True)
class SupervisorSnapshot:
    running: tuple[dict, ...]       # {execution_id, plan_id, started_at}
    recent_completed: int
    recent_failed: int
    queue_size: int | None          # từ hook task_queue_count
    stuck: tuple[dict, ...]         # running quá stuck_after_s

class ExecutionSupervisor:
    def __init__(self, bus, task_queue_count: Callable[[], int] | None = None,
                 stuck_after_s: float = 60.0, clock: Callable[[], float] | None = None) -> None
    def snapshot(self) -> SupervisorSnapshot
    def close(self) -> None
```
- Subscribe WORKFLOW_STARTED (track start — **dùng `clock()` float monotonic làm started_ref; lưu kèm event.timestamp ISO để expose** — P1-1 v2), COMPLETED/FAILED/CANCELLED (pop + đếm — **CANCELLED → recent_failed** — R3-1). **Giới hạn v1 (P3-1)**: counters in-memory từ lúc khởi tạo — không catch-up từ audit.
- stuck: `clock() - started_ref > stuck_after_s` (float-vs-float); **stuck = subset của running đã sort (R3-3)**.
- WORKFLOW_STARTED emit trước policy check nhưng mọi nhánh sau đều emit terminal event → tracking luôn đủ cặp (verified).

### 3.3 evaluation_collector.py — EvaluationCollector
```python
class EvaluationCollector:
    def __init__(self, evaluation_store, evaluator: Evaluator | None = None) -> None
    def collect_workflow(self, workflow_id, execution_id, result: dict) -> None
    def collect_all(self) -> dict
```
- `collect_workflow`: evaluator được wire → chạy → store.evaluate(quality, feedback); **bắt cả lỗi evaluator VÀ KeyError** (store chưa có row — P1-4) → best-effort, không crash.
- **Trigger (P2-1 v2)**: wiring subscribe WORKFLOW_COMPLETED/FAILED/CANCELLED → `collect_workflow` (evaluator=None → no-op).
- `collect_all`: aggregate từ `store.list(limit=10000)` (P3-2): `{workflow_id: {count, success, failed, avg_quality}}` — deterministic sort theo workflow_id.

### 3.4 goals/reporting.py — GoalReporter
```python
@dataclass(frozen=True)
class GoalReport:
    total: int
    by_status: dict[str, int]      # 5 status (active/paused/completed/failed/cancelled — P1-3)
    avg_progress: float            # trung bình progress TẤT CẢ goals (P3-3)
    completed_tasks: int
    failed_tasks: int              # FAILED + CANCELLED (P2-5 — đồng bộ _recompute_goal)
    goals: tuple[dict, ...]        # {id, title, status, progress, task_count}

class GoalReporter:
    def __init__(self, goal_manager) -> None
    def report(self) -> GoalReport
    def report_goal(self, goal_id: str) -> dict | None
```
- Đọc qua public API `goal_manager.list_goals()` / `get_goal(id)` (verified — không sửa GoalManager).

### 3.5 metrics.py — method mới (P1-1)
`MetricsService.duration_by_workflow() -> dict[str, tuple[float, int]]` — `SELECT name, AVG(duration_ms), COUNT(*) FROM metrics WHERE category='workflow' AND duration_ms IS NOT NULL GROUP BY name` → {plan_id: (avg_ms, count)}.

### 3.6 API + CLI + wiring
- `api/routers/orchestrator_v2.py`: GET `/api/v1/orchestrator-v2/advisor/suggestions`, `/supervisor/snapshot`, `/goals/report`, `/goals/{goal_id}/report`; **app.py include_router** (P3-5).
- Wiring: regs["orchestrator_v2"] = {advisor, supervisor, collector, goal_reporter}; advisor nhận evaluation_store + metrics_service + prompt_history từ regs["observability"] (P1-2 v2); supervisor nhận kernel.bus + task_queue_count hook = `lambda: len(task_queue.list_items(QueueItemStatus.QUEUED))` (P3-2); **wiring tạo TaskQueue (settings.goals.db_path) + event_service** (P2-2 v1); collector nhận store + evaluator (None mặc định) + **subscribe 3 terminal events** (P2-1 v2); goal_reporter nhận regs["goals"]. **Thứ tự build (R3-2)**: orchestrator_v2 luôn build SAU observability (advisor cần regs["observability"]) — collector subscribe sau EvaluationStore.
- CLI: **sửa `workflow/cli.py`** (P2-2 v2 — file CLI thật của aiagent): `aiagent advisor` (suggestions JSON), `aiagent supervisor` (snapshot JSON) — lazy import. **db_path convention (R2-1)**: service dùng suffix giống wiring — metrics = `db_path + ".metrics"`, evals = `db_path + ".evals"`, prompts = `db_path + ".prompts"`; **kèm bypass fix `_metrics()` hiện có đang đọc raw db_path (bug TASK-021 — ghi LOG `[bypass]`)**.

## 4. AC
- AC1: ImprovementAdvisor — 5 rules (test mỗi rule: dữ liệu giả → suggestion đúng); quality None bỏ qua; dedup + sort; không dữ liệu → []
- AC2: ExecutionSupervisor — running/finished/stuck (fake clock); close(); snapshot đúng
- AC3: EvaluationCollector — evaluator mock → quality gắn; evaluator raise + KeyError (store chưa có row) → không crash; collect_all aggregate
- AC4: GoalReporter — by_status đủ 5 keys; avg_progress; failed_tasks = FAILED + CANCELLED; report_goal; deterministic
- AC5: API 4 endpoint GET 200 với dữ liệu mẫu
- AC6: CLI advisor/supervisor chạy thật (JSON)
- AC7: INV-010 — orchestrator/ module mới không import aios_core.models (dir_imports pass); full pytest pass; coverage toàn suite ≥ 80% cứng (95% mục tiêu)
- AC8: không sửa goal.py/task_queue.py/execution.py (git diff verify — chỉ metrics.py +1 method, thêm module mới + wiring/api/cli)

## 5. Test
- test_advisor.py (5 rule + None quality + dedup + empty), test_supervisor.py (tracking + stuck + close), test_evaluation_collector.py (evaluator mock + crash + KeyError + aggregate), test_goal_reporter.py (status/progress/detail), test_orchestrator_v2_api.py (4 endpoint), test_architecture.py (INV-010 giữ)

## 6. Ghi chú (quyết định qua critique-1)
- Rule 5 dùng duration_by_workflow() mới (P1-1 v1); rule 4: "≥ 3 renders → review" đếm qua list(10000) group (P1-2 v1 + P1-2 v2)
- by_status 5 status (P1-3 v1); collector bắt KeyError (P1-4 v1); avg quality None skip (P1-5 v1)
- Supervisor: started_ref = clock() float, expose started_at ISO (P1-1 v2); running sort theo execution_id (P3-3); collector trigger qua bus (P2-1 v2); CLI = workflow/cli.py (P2-2 v2)
- GoalReporter: list_goals(limit=10000) (P3-1); failed_tasks = FAILED+CANCELLED (P2-5 v1); collect_all avg_quality non-None (P3-4)
- Deterministic, offline-first, không LLM; suggestion không tự áp dụng
