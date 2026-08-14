# Critique vòng 2 — TASK-027 (Execution Graph)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
C1-01 ⚠️ SAI (thiếu nửa executor → C2-01 P1) · C1-02 ✅ (còn hở → C2-03 P2) · C2-01 ⚠️ MỘT PHẦN (thiếu test init → C2-07 P3) · C2-02 ✅ · C2-03 ⚠️ MỘT PHẦN (thiếu test biên → C2-11 P3) · C2-04 ✅ · C2-05 ⚠️ MÂU THUẪN MỚI (risk table stale → C2-05 v2 P2) · C2-06 ⚠️ MỘT PHẦN (worker start-guard thiếu → C2-02 P1) · C2-07 ✅ · C3-01 ✅ · C3-02 ⚠️ MỘT PHẦN (no raise path → C2-04 P2) · C3-03 ⚠️ KHÔNG RÕ (wait timeout → C2-10 P3) · C3-04 ⚠️ MỘT PHẦN (→ C2-12 P3) · C3-05 ✅

## Mục B — Vấn đề mới

### P1
**C2-01**: AST gate đòi literal `validate_dag(` trong executor.py nhưng YC-5 pre-validate chỉ gọi `validate_graph_acyclic`.
→ **Resolution**: executor.py pre-validate **gọi thẳng** `validate_dag([_DagView(n.id, [d.node_id for d in n.depends_on]) for n in graph.nodes])` (import _DagView từ contracts) — literal trong cả 2 file; sửa YC-5 step 1 + §5.1 note.

**C2-02**: Cancel mid-batch — node queued (đã submit, chưa start) vẫn chạy runner → vi phạm AC6.
→ **Resolution**: worker start sequence: (1) check cancel flag + status hiện tại — flag set → persist CANCELLED, KHÔNG chạy runner; status != READY (terminal do policy) → bỏ qua; (2) ngược lại READY→RUNNING (persist) → runner loop với flag check TRƯỚC MỖI attempt kể cả lần 1. Thêm test A→{B,C,D}, max_parallel=2, cancel khi B/C chạy → D không bao giờ được gọi, D CANCELLED.

### P2
- **C2-03**: READY→RUNNING do ai? + "thứ tự START" mơ hồ. → **Resolution**: READY→RUNNING do **worker** tại thời điểm task thực sự bắt đầu; `execution_order` append do **main** tại submit (đổi tên "thứ tự submit"); test READY persist: A→B, A→C, max_parallel=1 → runner B assert `get_state(id)["nodes"]["C"] == "ready"`.
- **C2-04**: Wave loop thiếu no-progress guard (node kẹt READY → spin vô hạn); GraphExecutionError không raise path. → **Resolution**: guard sau dead-end: "ready rỗng VÀ tồn tại node non-terminal → raise GraphExecutionError"; test monkeypatch submit kẹt READY.
- **C2-05**: §7 risk table vẫn ghi default execution_id = graph.id (stale) + thiếu test namespace. → **Resolution**: sửa §7 → `f"graph:{graph.id}"`; test: execute không truyền execution_id → `get_state(f"graph:{graph.id}")` có state, `get_state(graph.id) is None`, `GraphResult.execution_id == f"graph:{graph.id}"`.
- **C2-06**: State write protocol từ worker — update_state shallow-merge → lost-update. → **Resolution**: executor sở hữu dict nodes (khởi tạo đủ mọi id = PENDING; set_state lưu reference); worker CHỈ gán key đã tồn tại (GIL-atomic, không đổi size); persist qua update_state(nodes=nodes) cùng reference; KHÔNG read-modify-write toàn dict.

### P3
- **C2-07**: Test init-validation: `GraphExecutor(state, GraphSettings(default_failure_policy="bogus"))` → GraphValidationError.
- **C2-08**: `started_at` = ISO-8601 string (pattern created_at).
- **C2-09**: Test retry-cancel: fail attempt 1, cancel giữa attempt 2 → CANCELLED, không chạy attempt tiếp.
- **C2-10**: Ghi `event.wait(timeout=5)` cho barrier tests.
- **C2-11**: Test biên max_concurrent_running: 3 ready, max=2 → 2.
- **C2-12**: §3 ghi chú: set_state lưu reference; get_state deepcopy + fallback repr; 028 đọc qua GraphResult.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C2-01, C2-02 (P1) + C2-03..C2-06 (P2) + P3 → spec v3. Sau vòng này **approve** (không cần vòng 3 — không đổi kiến trúc).
