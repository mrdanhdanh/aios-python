# TASK-059 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Mode selection từ đâu (dependency)?
Tasks cần khai báo dependency để phân biệt PARALLEL/SEQUENTIAL.
→ **Resolve**: AgentTask có `depends_on: list[str]` (task ids). Mode: 1 task → SINGLE; mọi task không dependency (không task nào depends_on) → PARALLEL; có dependency → SEQUENTIAL; task có `subtasks` → HIERARCHICAL (xác định bằng flag `hierarchical: bool` — v1 đơn giản).

## C1-02 (P2) — PARALLEL thật (threads) hay mô phỏng?
→ **Resolve**: v1 deterministic — chạy tuần tự nhưng GOM kết quả theo mode (không thread). Parallel thật → wiring sau (Parallel Scheduler M5). Ghi rõ: mode quyết định THỨ TỰ + AGGREGATION, không phải concurrency thật v1.

## C1-03 (P2) — agent_fn signature?
→ **Resolve**: `agent_fn: Callable[[AgentTask, dict], Any]` — (task, context) → result. Context = result các task trước (SEQUENTIAL) / {} (SINGLE/PARALLEL). Agent resolution (chọn agent theo capability) do orchestrator làm: nhận `agents: list[dict]` (id + capabilities) — check capability trước khi gọi.

## C1-04 (P3) — HIERARCHICAL aggregation?
→ **Resolve**: task có subtasks (list AgentTask) — result = {task_id: {subtask_id: result}}; subtask capability check riêng.

## C1-05 (P3) — Delegation lifecycle đủ?
→ **Resolve**: PENDING → RUNNING → COMPLETED/FAILED; raise nếu transition sai (pattern cũ).

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
