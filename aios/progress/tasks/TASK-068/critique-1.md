# TASK-068 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-068.

## Các vấn đề

### C1-01 (P1) — "Chặn execution mới" chặn ở đâu? ExecutionService không hỏi gate
ExecutionService.execute không có preflight hook — chặn bằng cách nào?
→ **Resolve**: KillSwitch cung cấp `preflight() -> bool`; wiring RuntimeKernel KHÔNG sửa ExecutionService — thay vào đó `ExecutionGate` là object mà execution path (CLI run/API) check TRƯỚC khi gọi execute. Test: gate chặn đúng; CLI run sau emergency → từ chối. Ghi chú rõ: enforcement ở boundary (caller), không chui vào service.

### C1-02 (P2) — Cancel approvals pending: approvals ở đâu?
→ **Resolve**: M2 PermissionBroker không có store approvals persist — emergency đánh dấu state `approvals_cancelled=True` (counter) + ghi event; danh sách pending do caller quản lý. Test counter + event.

### C1-03 (P2) — Reversible rollback: đánh dấu gì?
→ **Resolve**: emergency_stop nhận `running: list[execution_id]` → đánh dấu trong state (dict execution_id → status reversible) + event payload. Test.

### C1-04 (P3) — CLI status hiển thị gì?
→ **Resolve**: `aiagent status` in emergency flag + counters (blocked executions/tool calls) + reversible list.

## Kết luận
Resolve vào spec v2.
