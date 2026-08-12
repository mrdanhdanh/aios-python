# Critique vòng 2 — TASK-009

## Đánh giá chung
P1-2 đúng hoàn toàn; P1-1/P1-3 đúng hướng còn lỗ hổng; P1-4 mới sửa 1/3 chỗ. Vòng 2: **5 P2** (Yêu cầu #2 stale, construct-vs-register, evaluations semantics, PLAN còn 2 chỗ, validation algorithm) + **10 P3**. Sẵn sàng: 4/5.

## Vấn đề + Resolution

### P2-1 — Yêu cầu chi tiết #2 còn stale (regex cũ + "không escape")
- **Resolution**: xóa 2 câu cũ; thay: extract qua regex `(?<!\{)\{([A-Za-z_]\w*)\}(?!\})`; `{{`/`}}` = escape (render literal).

### P2-2 — Validate construct vs register mâu thuẫn
- **Resolution**: extract + validate CÙNG lúc **construct** (pydantic model_validator) — object hỏng không tồn tại; register không validate lại (ghi chú); sửa Phạm vi "validate register" → "validate lúc construct".

### P2-3 — evaluations semantics + unknown id
- **Resolution**: `evaluations(id, version=None)` → None = TOÀN BỘ history (thứ tự append), có version → lọc; `evaluate`/`evaluations` id unknown → PromptError; bind + append CÙNG critical section (lock).

### P2-4 — PLAN amend còn 2 chỗ
- **Resolution**: amend (a) milestone M1-P2: "Knowledge Graph (v1 in-memory, populate thủ công — xem amend)"; (b) Prompt Registry: "Template (v1: str.format subset; jinja2 → M4)".

### P2-5 — Validation algorithm brace chưa pin
- **Resolution**: pin scan trái→phải: (1) `{{`/`}}` → escape nhảy 2; (2) field regex tại vị trí → nhảy qua; (3) còn lại → PromptError; test `{{{name}}}` → PromptError; `{{name}}` hợp lệ; `{name}}` → PromptError.

### P3 — (áp)
1. bind_tool/unbind_tool/agents_using unknown capability → CapabilityError (đồng bộ)
2. register_agent_use agent_id rỗng → ValueError
3. PromptRegistry register trùng (id,version) → overwrite + warning (nhất quán)
4. Catalog search bỏ qua giá trị None (không str(None)="none")
5. Catalog remove_entry unknown → idempotent
6. Graph add_edge: self-loop cho phép v1 (ghi chú); relation rỗng → ValueError; find value None thật — chấp nhận v1
7. PromptEvaluation.timestamp = UTC ISO; list() insertion order
8. Thêm 1 test concurrent cho PromptRegistry (register+get)
9. render variable value=None → chấp nhận (str.format "None")
10. AC8 relation names cụ thể: capability -provides-> tool? — pin: `tool -provides-> capability`, `agent -uses-> capability`, `workflow -requires-> capability`

## Kết luận
- [x] **Resolve toàn bộ (5 P2 + 10 P3)** — cập nhật spec + amend PLAN, sẵn sàng implement.
