# TASK-005 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Scheduler | `kernel/services/scheduler.py` |
| State | `kernel/services/state.py` |
| Resource | `kernel/services/resource.py` |
| Execution | `kernel/services/execution.py` |
| RuntimeKernel | `kernel/runtime_kernel.py` |
| Contract changes | `execution_plan.py` (timeout_s float), `events.py` (WORKFLOW_CANCELLED), `config.py` (resources) |
| Tests (5 file mới) | `test_scheduler.py`, `test_state.py`, `test_resource.py`, `test_execution.py`, `test_runtime_kernel.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- **ExecutionService**: runner = `dict[node_id → fn(node, results_so_far)]`; topo Kahn FIFO; fail-fast; timeout retryable (0 → không timeout); cancel check trước reset; execution_id = plan.id; try/finally release mọi path; pre-check policy (reject/approval/resource); emit qua EventService (có audit)
- **Snapshot/resume**: state lưu plan.to_dict + nodes + results; resume đọc plan từ state, reset failed/running → pending
- **Scheduler**: poll loop + skip overlap + error-continue + hooks on_startup/shutdown
- **ResourceService**: atomic acquire + clamp release; stats snapshot
- **RuntimeKernel**: register_instance cho Union/non-type ctor (EventService, ArtifactService, ContextService, ResourcesSettings, EventBus) + register class còn lại; DI resolve string annotations qua get_type_hints
