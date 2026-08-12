# Critique vòng 2 — TASK-010

## Đánh giá chung
Resolution v1 áp không đồng bộ — tạo 3 P1 mới (intent None mâu thuẫn !skill/#; Yêu cầu #5 dừng cứng mâu thuẫn Phạm vi #5; thứ tự longest vs priority) + 8 P2 + 8 P3. **Sẵn sàng: 2.5/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — "intent luôn None từ Normalizer" mâu thuẫn !skill/# 
- **Resolution**: chọn (a): Normalizer ĐƯỢC gán intent cho 2 case đặc biệt (`#` → chat, `!skill` → skill), còn lại None; Orchestrator: `if req.intent` từ normalizer → dừng pipeline, resolved_by="normalizer".

### P1-2 — Yêu cầu #5 còn "dừng cứng khi rule có agent"
- **Resolution**: sửa Yêu cầu #5: rule có agent → VẪN chạy matcher (không gọi planner); rule không agent → chạy matcher; matcher khớp → gắn workflow_name; hết → planner.

### P1-3 — Thứ tự RuleEngine: longest vs priority
- **Resolution**: pin tổng thứ tự: **priority desc → longest pattern → insertion asc**; thêm case `"generate api generator"` → coding (priority 10 thắng) vào AC2.

### P2 — (áp)
1. **resolved_by="rule"** khi rule+matcher cùng khớp (workflow_name phụ); ghi chú UI hiển thị cả 2
2. **AC5 viết lại cơ chế thật**: "generate api" (rule coding/coder) + matcher token search "api" → workflow `crud_generator` (fixture description chứa "api") → response agent='coder' + workflow_name, resolved_by='rule'
3. **PlanResult thêm `error: bool = False`**
4. **llm_calls cơ chế**: Planner giữ `self._calls` (tăng quanh mỗi model.chat kể cả raise); Orchestrator đọc `planner.calls` cộng vào stats; PlannerStub calls==0
5. **Normalizer.__init__(alias: dict | None = None, library: WorkflowLibrary | None = None)** — library optional (None → bỏ qua @, confidence 0.5); Orchestrator truyền CÙNG library instance cho normalizer + matcher
6. **Stopword/short-token filter**: bỏ token < 3 ký tự + stopwords (the/a/please/vui/lòng/làm...); ưu tiên macro → search cả câu → search token
7. **SystemKnowledge catch GraphError/CatalogError → None**; "how many X" dùng `catalog.search("", kind=X)` đếm
8. **Matcher confidence**: search trả tên → `library.get(name)` → re-check `token in name` (0.8) hay description (0.6); macro map validate workflow tồn tại (get → WorkflowError → bỏ qua)

### P3 — (áp khi implement)
1. `re.escape(pattern)` trong RuleEngine
2. Plural/gián cách chấp nhận v1 (ghi chú R2)
3. Longest = độ dài pattern string
4. Tie "update system status" (system status 8 + update system 8) → insertion; thêm case AC2
5. `OrchestratorResponse.agent: str | None`
6. `handle(request: str | dict | NormalizedRequest)` — pin
7. Planner parse fail → intent="chat" + error
8. Macro `@` anchor `^@`; `@crud api lang=python` — params extract sau macro

## Kết luận
- [x] **Resolve toàn bộ (3 P1 + 8 P2 + 8 P3)** — cập nhật spec, sẵn sàng implement.
