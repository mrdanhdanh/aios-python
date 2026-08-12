# Critique vòng 1 — TASK-008

## Đánh giá chung
Khung tốt, không scope creep. Nhưng 2 P1 (YAML loader/CLI không chủ — deliverable M1; định danh workflow không nhất quán) + 8 P2 + 9 P3. **Sẵn sàng: 3/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — YAML loader + CLI không có chủ (PLAN M1: `aiagent run workflow.yaml --simulate`)
- **Resolution**: thêm vào In: `WorkflowDefinition.from_dict()` + `from_yaml()` (yaml.safe_load — PyYAML có sẵn) + `workflow/cli.py` — `run workflow.yaml --simulate`: load → compile → ExecutionService với fake runner (echo node) → in kết quả; CLI entry `python -m aios_core.workflow.cli` (v1 không cài console_scripts). Ghi PROGRESS đúng deliverable.

### P1-2 — Định danh: key library vs definition.name vs plan.id
- **Resolution**: **canonical name = definition.name**; `register(definition)` — bỏ tham số name (fail-fast nếu giữ name → lệch raise WorkflowError); MockCompiler `plan.id = f"wf:{definition.name}"` luôn.

### P2 — (đặc tả)
1. **Extract DAG helper thuần**: `kernel/dag.py` chỉ 3 logic check (unique/unknown/cycle), giữ nguyên message từng chữ; KHÔNG move PlanNodeType; chạy lại 107 test TASK-003 không sửa — thành AC
2. **AC1 ≥ 8 case**: thêm unknown dep, nodes rỗng, retries/timeout âm (definition + node level) — fail-fast ở definition
3. **Merge defaults None vs 0**: `WorkflowNode.timeout_s: float | None = None`, `retries: int | None = None` (None = không khai báo → fallthrough; 0 = vô hạn giữ nguyên); AC2 test node timeout_s=0 không bị đè
4. **search**: query empty/whitespace → []; v1 case-insensitive substring trên name+description; nhiều từ → match toàn chuỗi (M2 tokenize)
5. **promote(unknown) → WorkflowError**; usage(unknown) → WorkflowError; promote = usage+1 dưới lock; promote chỉ tăng counter (M2 mới rank)
6. **AC4 dùng permissions rỗng hoặc ["filesystem"]** — tránh policy pre-check FAILED "approval required" (ghi chú: là hành vi TASK-005 không phải lỗi compiler)
7. **edges = read-only computed property** (derive từ depends_on — không stored field); test nhỏ
8. **WorkflowNode defaults pin**: id/type/name required; agent="", capabilities=[], depends_on=[], timeout_s=None, retries=None

### P3 — (áp)
1. AC7 thêm LangGraphCompiler; re-export workflow ở aios_core/__init__
2. `is_available()` lên WorkflowCompiler ABC default True (Mock kế thừa, stub override False)
3. MockCompiler set created_at=now ISO + status=READY sau compile
4. Version drop khi compile — note audit M2
5. Reuse semver.parse_version (TASK-003)
6. register chỉ nhận WorkflowDefinition instance (strict)
7. Thêm test thread-safe (2 thread register/search/promote)
8. list() insertion order
9. name strip whitespace (reject whitespace-only)

## Kết luận
- [x] **Resolve toàn bộ (2 P1 + 8 P2 + 9 P3)** — cập nhật spec, chuyển critique vòng 2.
