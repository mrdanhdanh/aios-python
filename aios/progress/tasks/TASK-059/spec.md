# TASK-059 — Multi-Agent Autonomy (M9-P4)

## Mục tiêu
AIOS tự quyết `single vs parallel vs sequential vs hierarchical` — chỉ thêm complexity khi tạo giá trị đo được (PLAN §M9-23). **Autonomous Delegation** (§M9-24): `Task A → Agent 1 (owner, deadline, budget, output contract)`.

## Phạm vi
- `autonomous/multi_agent.py`: `MultiAgentOrchestrator` — mode selection deterministic + delegation + result aggregation
- `contracts.py`: `AgentTask` (id, title, required_capabilities[], output_contract str), `Delegation` (task_id, agent_id, owner, deadline, budget, status), `DelegationResult`, `AgentMode` (SINGLE/PARALLEL/SEQUENTIAL/HIERARCHICAL)

## Input/Output
- In: `delegate(tasks, agents, mode)`; Out: `list[DelegationResult]`
- Fail-closed: agent thiếu capability yêu cầu → raise (không delegate bừa)

## Tiêu chí chấp nhận (AC)
1. 4 modes: SINGLE/PARALLEL/SEQUENTIAL/HIERARCHICAL
2. Mode selection deterministic: 1 task → SINGLE; nhiều task độc lập (không dependency) → PARALLEL; có dependency → SEQUENTIAL; nested (task con) → HIERARCHICAL
3. Delegation contract: owner/deadline/budget/output_contract — `extra=forbid`
4. Agent capability check: agent phải có đủ required_capabilities → thiếu → raise `DelegationError`
5. Delegation status lifecycle: PENDING → RUNNING → COMPLETED/FAILED (state machine đơn giản)
6. Execute qua `agent_fn` injectable (không chạm agent registry trực tiếp — Worker qua Capability)
7. PARALLEL: kết quả gom theo task id (deterministic order)
8. SEQUENTIAL: chạy theo thứ tự dependency (task sau nhận result task trước qua context)
9. HIERARCHICAL: task con gom vào parent result
10. Emit event `autonomy.delegated` mỗi delegation
11. Contract `extra=forbid` + unit tests coverage ≥ 90%

## Amend (critique ×2 resolve)
- C1-01: `AgentTask.depends_on: list[str]`; mode: 1 task → SINGLE; không dependency → PARALLEL; có dependency → SEQUENTIAL; `hierarchical: bool` → HIERARCHICAL
- C1-02: v1 deterministic — chạy tuần tự, mode quyết định THỨ TỰ + AGGREGATION (parallel thật → Parallel Scheduler M5 wiring sau)
- C1-03: `agent_fn(task, context)` — context = result task trước (SEQUENTIAL) / {} (khác); agents: list[dict] (id + capabilities)
- C1-04: subtasks → result = {task_id: {subtask_id: result}}
- C1-05: PENDING → RUNNING → COMPLETED/FAILED (+SKIPPED cho task sau task fail trong SEQUENTIAL)
- C2-01: chọn agent đầu tiên sorted theo id có đủ capability (deterministic)
- C2-02: deadline/budget v1 lưu contract (enforce wiring sau)
- C2-03: SEQUENTIAL task fail → các task sau SKIPPED (fail-fast)
