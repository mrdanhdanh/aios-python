# TASK-066 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-066.

## Các vấn đề

### C1-01 (P1) — "Không chạy lại node đã done" phải đo được qua event, không chỉ journal status
Journal tự ghi "done" rồi resume đọc journal → pass giả nếu wrapper không thực sự skip runner.
→ **Resolve**: Test đo `WORKFLOW_STARTED`/`node executed` count qua event bus: chạy 4 node, crash ở node 3 → resume → assert node 1–2 KHÔNG emit run event lần 2 (đếm qua TOOL_STARTED hoặc node runner side-effect counter).

### C1-02 (P2) — JournaledExecutor cần interface rõ với ExecutionService
Wrapper phải gọi execution thật (execute nodes) không phải tự chạy lại pipeline.
→ **Resolve**: JournaledExecutor nhận `node_runner: Callable[[node_id, ctx], None]` + `resume_point(execution_id) -> node_id|None`; chính nó duyệt nodes (đã có ExecutionGraph) — KHÔNG đụng ExecutionService internals; test dùng node_runner đếm lần chạy.

### C1-03 (P2) — Journal corrupt: phân biệt "thiếu file" vs "ghi dở"
Thiếu journal = execution chưa từng start (resume → raise ExecutionNotFound); ghi dở (crash giữa write) → SQLite atomic → hoặc có hoặc không.
→ **Resolve**: SQLite transaction cho mỗi node write (atomic); resume không tìm thấy execution_id → raise JournalError. Test cả 2.

### C1-04 (P3) — Idempotency danh sách khai báo ở đâu?
→ **Resolve**: `IdempotencyClassifier(idempotent_writes: set[str], read_ops: set[str])` — mặc định: op không khai báo = non_idempotent_write (fail-closed, an toàn).

## Kết luận
Resolve vào spec v2.
