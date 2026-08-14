# Critique vòng 1 — TASK-027 (Execution Graph)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v1

## Đánh giá chung
Spec kỹ, defense-in-depth tốt; kiểm chứng code: StateService generic store (zero-MOD khả thi), container singleton (AC11 khả thi), baseline 1003. 2 P1 (type mismatch validate_dag; TRANSITIONS mâu thuẫn executor) + 7 P2 + 5 P3.

## P1 — Blockers

### C1-01: `validate_dag` KHÔNG chạy được trên `GraphNode.depends_on: list[Dependency]` (type mismatch)
- `validate_dag` (dag.py) giả định `depends_on: list[str]` — với Dependency object, `d not in ids` luôn True → mọi graph ≥1 cạnh fail; cycle DFS sai. AST gate yêu cầu literal `validate_dag(` trong contracts.py + executor.py.
- **Resolution**: adapter tường minh trong contracts.py:
  ```python
  @dataclass
  class _DagView:
      id: str
      depends_on: list[str]

  def validate_graph_acyclic(nodes: list[GraphNode]) -> None:
      validate_dag([_DagView(n.id, [d.node_id for d in n.depends_on]) for n in nodes])
  ```
  contracts.py giữ literal `validate_dag(` (qua adapter); executor.py pre-validate gọi `validate_graph_acyclic(graph.nodes)` + giữ literal `validate_dag(` qua view trực tiếp (chọn: cả 2 file đều có literal — ghi rõ test). KHÔNG sửa dag.py.

### C1-02: TRANSITIONS cấm `PENDING→RUNNING` nhưng executor làm trực tiếp; READY không bao giờ persist
- **Resolution (chọn b — READY persist)**: trong wave: set `PENDING→READY` cho toàn bộ ready set (persist) rồi `READY→RUNNING` từng node khi submit (persist); TRANSITIONS thêm RUNNING vào PENDING; 028 đọc được READY từ store.

## P2 — Major
- **C2-01**: `GraphSettings.default_failure_policy` là config chết (converter hardcode FAIL_FAST). → **Resolution**: chọn (b): ghi rõ "field tiêu thụ ở 028 khi gọi plan_to_graph"; 027 bỏ hardcode → `plan_to_graph` nhận `failure_policy` param từ caller (default FAIL_FAST); thêm test field có tác dụng.
- **C2-02**: FAIL_FAST/SKIP_DEPENDENTS với node in-flight. → **Resolution**: "failure policy áp tại ranh giới wave — node RUNNING trong batch chạy xong ghi nhận bình thường; chỉ PENDING/READY bị BLOCKED/SKIPPED"; thêm test max_parallel=2, A→{B,C}, B fail, C barrier → C SUCCEEDED, D BLOCKED.
- **C2-03**: `max_concurrent_running` đếm sai. → **Resolution**: `max_concurrent_running = max(trước, min(len(ready), max_parallel))` mỗi wave + test biên (3 ready, max=2 → 2).
- **C2-04**: `started_at` datetime ngoài allow-list. → **Resolution**: thêm `datetime` vào external allow-list §5.2.
- **C2-05**: default `execution_id = graph.id` va chạm key với ExecutionService. → **Resolution**: default `execution_id = f"graph:{graph.id}"` (namespace riêng) + test integration state không bị mất.
- **C2-06**: RLock granularity — cancel() deadlock. → **Resolution**: ghi rõ "lock chỉ bảo vệ _cancel_flags + StateService op đơn lẻ; wave loop không giữ lock; cancel() trả ngay; retry loop check cancel flag giữa attempts".
- **C2-07**: Test cycle model_construct mức bypass. → **Resolution**: cycle dựng bằng `GraphNode.model_construct` (bypass per-node) rồi `ExecutionGraph.model_validate` → ValidationError; execute-test dùng model_construct toàn bộ (pre-validate bắt).

## P3 — Minor
- **C3-01**: thêm `node_reasons: dict[str, str] = {}` vào GraphResult.
- **C3-02**: guard "wave không progress → GraphExecutionError" + test unit (model_construct).
- **C3-03**: test barrier `event.wait(timeout=5)`.
- **C3-04**: ghi chú result không serializable → state lưu repr (StateService behavior); 028 đọc qua GraphResult.
- **C3-05**: sửa wording — "schema graph dùng key riêng theo execution_id; riêng `succeeded` ≠ `completed`".

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C1-01, C1-02 (P1) + C2-01..C2-07 (P2) + P3 → spec v2, rồi critique vòng 2.
