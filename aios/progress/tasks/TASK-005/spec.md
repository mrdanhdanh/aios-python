# TASK-005 — M1/P0.5c: Kernel Services II (Scheduler, State, Resource, Execution) + RuntimeKernel

## Mục tiêu
Hoàn thiện Runtime Kernel: 4 service còn lại (Scheduler, State, Resource, Execution) + `RuntimeKernel` — thành phần wiring tất cả 9 services vào DI Container với lifecycle start/stop. Đây là trái tim thực thi: ExecutionService chạy ExecutionPlan (TASK-003) với retry/timeout/cancel/snapshot-resume, được bảo vệ bởi ResourceService (token/concurrent) và PolicyService (TASK-004).

## Phạm vi
- **In** (thuộc `backend/src/aios_core/kernel/services/`):
  1. `scheduler.py` — `SchedulerService(poll_interval_s: float = 0.05)`: đăng ký job (one-shot sau delay; interval mỗi N giây), `schedule_one_shot(name, delay_s, callback)`, `schedule_interval(name, interval_s, callback)`, `start()/stop()`, `list_jobs() -> [(name, kind, running)]`, `cancel(name)`; callback trong daemon thread; **interval skip tick nếu callback trước chưa xong**; **interval lỗi → log + tiếp tục tick**; stop/cancel không kill callback đang chạy (document); schedule trùng tên → thay thế + warning; **implement `on_startup()`/`on_shutdown()`** (container.start() gọi tự động); idempotent start/stop
  2. `state.py` — `StateService`: state machine — `set_state/get_state/update_state/snapshot/restore`; **schema: `{plan: dict, nodes: {id: status}, results: {id: result}, started_at}`**; status: pending|running|completed|failed; in-memory + RLock; snapshot deepcopy có try/except → fallback repr (results nên JSON-serializable)
  3. `resource.py` — `ResourceService`: token budget + concurrent — `acquire_tokens/release_tokens` (atomic, release clamp ≥0), `acquire_slot/release_slot` (clamp ≥0), `stats() -> {used_tokens, running}`; limits từ `ResourcesSettings` (mở rộng Settings: `resources.max_tokens`, `resources.max_concurrent` — vào In scope + config.yaml + test_config)
  4. `execution.py` — `ExecutionService(event_service: EventService, policy_service: PolicyService, state_service: StateService, resource_service: ResourceService)`: execute(plan, runner) — **runner contract: `dict[str, Callable[[PlanNode, dict[str, Any]], Any]]`** map node_id → `fn(node, results_so_far)`; kết quả node = giá trị trả về → node_results; runner raise → node failed; runner không có entry → node failed reason "no runner for node X"; runner gọi đúng 1 lần mỗi attempt; topo **Kahn FIFO theo thứ tự plan.nodes**; retry per-node (1 + retries, timeout cũng là lỗi retryable); timeout `PlanNode.timeout_s: float` (<=0 → không timeout); cancel(execution_id) — chỉ hiệu lực giữa nodes; **execution_id = plan.id; execute() kiểm tra pending cancel TRƯỚC → có → trả CANCELLED ngay (không reset, không chạy); không có → reset state + cancel flag → chạy; cancel id không tồn tại → no-op**; snapshot sau mỗi node (lưu plan.to_dict); resume đọc plan từ state, validate node ids → mismatch raise, chạy lại node ≠ completed, pre-check + acquire/release chung code path; fail-fast; try/finally release mọi path; `ExecutionResult(status, execution_id, node_results, reason="")` — reason paths: deny → decision.reason + policy_version, resource fail → "resource unavailable", timeout → "node X timed out", cancel → "cancelled"; requires_approval → chặn FAILED "approval required"; sandbox_required → warning + chạy; map required_permissions → PolicyRequest.scopes (scope lạ bỏ qua + log); KHÔNG mutate plan.status; emit qua EventService.emit — payload: execution_id, plan_id, reason (khi có); events STARTED/COMPLETED/FAILED/CANCELLED
  5. `runtime_kernel.py` (đặt ở `kernel/`) — `RuntimeKernel`: create(settings) — **register_instance: EventBus, EventService, ArtifactService (construct tay từ settings paths), ContextService (clock mặc định), ResourcesSettings (từ settings.resources); register class: PermissionService, PolicyService, SchedulerService, StateService, ResourceService, ExecutionService**; start()/stop() → container; bus/container property
  6. **Mở rộng `Settings`**: `resources.max_tokens: int | None`, `resources.max_concurrent: int | None`
  7. Tests: test_scheduler, test_state, test_resource, test_execution, test_runtime_kernel (5 file)
  8. **Contract change TASK-003**: `PlanNode.timeout_s: int` → `float` (sửa execution_plan.py + test_execution_plan.py); `EventType` thêm `WORKFLOW_CANCELLED`
- **Out (không làm)**: cron expression (v1), job persist (restart mất job), ExecutionPlan Planner (M2), node_runner thật (M2), checkpoint persist DB (in-memory v1 — TASK-005 snapshot/resume trong cùng process)

## Yêu cầu chi tiết
1. **SchedulerService**: start() thread loop (daemon) poll mỗi poll_interval_s; stop() set flag + join (1s); schedule sau start cũng được (lock); callback daemon thread riêng; interval skip overlap; interval lỗi tiếp tục; on_startup/on_shutdown hook
2. **StateService**: snapshot deep copy (try/except → repr fallback); restore thay thế; schema đầy đủ (plan/nodes/results/started_at)
3. **ResourceService**: acquire atomic (kiểm tra + trừ trong lock); release clamp ≥ 0; stats snapshot dưới lock; limits từ ResourcesSettings
4. **ExecutionService**: execute bọc try/finally (release mọi path); topo Kahn FIFO; retry/timeout/cancel/snapshot/resume theo resolution P2; pre-check policy (reject → FAILED; requires_approval → FAILED "approval required"; sandbox_required → warning + chạy); resources acquire trước (tokens theo estimated_tokens + slot), release cuối; events STARTED/COMPLETED/FAILED/CANCELLED; ExecutionResult.reason đầy đủ
5. **RuntimeKernel**: create(settings) — register_instance EventService/ArtifactService, register class còn lại; start/stop → container; property bus/container
6. Mọi test dùng tmp_path + fake runner/clock/delay nhỏ; mỗi module test riêng; coverage ≥ 80%

## Input / Output
- Input: TASK-003 (ExecutionPlan, Container, EventBus), TASK-004 (PolicyService, services, Settings)
- Output: 5 modules + RuntimeKernel + 5 test files + exports, commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: Scheduler: one-shot sau delay chạy đúng (fake delay nhỏ); interval chạy N lần rồi cancel; **interval skip khi callback chưa xong; interval lỗi → vẫn tick tiếp**; cancel không tồn tại → no-op; start 2 lần idempotent; schedule trùng tên → thay thế (có test)
- [ ] AC2: State: set/get/update; snapshot deep copy (mutate bản gốc không ảnh hưởng); snapshot object không copy được → fallback repr không crash; restore thay thế (có test)
- [ ] AC3: Resource: acquire_tokens vượt budget → False; release không âm (clamp); acquire_slot vượt concurrent → False; stats đúng (có test)
- [ ] AC4: Execution: plan 2 node (depends_on) chạy đúng topo; runner nhận đúng node; result COMPLETED + node_results; results lưu state (có test)
- [ ] AC5: Retry: fail 2 lần rồi thành (retries=2) → COMPLETED; fail hết retry → WORKFLOW_FAILED + reason "node X failed" + **fail-fast: node sau không chạy** (có test)
- [ ] AC6: Timeout (0.1s): runner sleep > timeout → FAILED + reason; **timeout tính là lỗi retryable** (retries=1 → chạy lại); timeout_s=0 → không timeout (có test)
- [ ] AC7: Cancel: runner node 1 set threading.Event → return; test chờ event → cancel() → CANCELLED + reason; node 2 không chạy; emit WORKFLOW_CANCELLED (có test)
- [ ] AC8: Snapshot/resume: chạy 1 node → snapshot (có plan); resume với runner mới → node 2 chạy, node 1 không chạy lại; **plan mismatch state → raise rõ** (có test)
- [ ] AC9: Pre-check: PolicyService deny → WORKFLOW_FAILED, runner KHÔNG gọi; **requires_approval=True → FAILED "approval required"**; sandbox_required → warning + chạy tiếp (có test)
- [ ] AC10: Resource integrate: acquire_tokens fail → không chạy runner; **sau fail/cancel → stats về baseline (try/finally release)** (có test)
- [ ] AC11: Events: STARTED/COMPLETED/FAILED/CANCELLED emit đúng (có test)
- [ ] AC12: RuntimeKernel.create: container.has đủ 9 service interfaces + bus; **resolve lần lượt CẢ 9 interface không raise**; start/stop idempotent; ExecutionService execute plan đơn giản (fake runner dict, required_permissions=[filesystem], Settings với tmp_path paths) end-to-end (có test)
- [ ] AC13: pytest pass + coverage ≥ 80%; test_import: `from aios_core.kernel import RuntimeKernel` + `from aios_core.kernel.services import SchedulerService, StateService, ResourceService, ExecutionService` pass
- [ ] AC14: Mọi test dùng tmp_path + không sleep lâu — git sạch sau test
- [ ] AC15: Settings.resources load từ config.yaml + default (test_config); `ExecutionResult.reason` non-empty cho mọi FAILED/CANCELLED (có test)

## Phụ thuộc
- TASK-003 + TASK-004 done
- Python 3.13.14

## Rủi ro
- R1: Scheduler thread test flaky → dùng poll 0.05s + fake delay nhỏ; interval test đếm lần gọi trong cửa sổ thời gian ngắn
- R2: Execution timeout dùng thread join — thread daemon chạy tiếp sau timeout (không kill được) → ghi chú, runner phải cooperative (M2)
- R3: Resume trong cùng process (in-memory state) — persist DB để sau (P8/M4)
- R4: Resource limits từ Settings — mở rộng Settings `resources.max_tokens/max_concurrent` (cùng pattern audit/artifacts TASK-004)
