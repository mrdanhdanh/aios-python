# Review — TASK-010 (Pre-Implementation)

## Tổng quan
Verify code nền: library.search/get, catalog kind exact, graph.neighbors raise, MockModel.calls, ModelTimeoutError ⊂ ModelError — đều đúng. 10/10 AC phủ tasks.md. **CHANGES REQUESTED: 2 R1 blocking + 3 R2 + 8 R3.**

## Vấn đề + Resolution

### R1-1 — Yêu cầu chi tiết #5 vẫn giữ "dừng cứng khi rule có agent" (mâu thuẫn Phạm vi #5 + AC5)
- **Resolution**: sửa Yêu cầu #5: "rule có agent → VẪN chạy matcher (chỉ bỏ qua planner); rule+matcher cùng khớp → resolved_by='rule' + workflow_name phụ".

### R1-2 — Cơ chế reset llm_calls chưa pin (planner._calls cumulative không reset được)
- **Resolution**: chọn (a) — `Planner.reset_calls()`; Orchestrator.reset() gọi planner.reset_calls(); test: sau reset, 10 request lạ → llm_calls == 10.

### R2 — (áp)
1. **SystemKnowledge**: pin `SystemKnowledge(catalog: SystemCatalog, graph: KnowledgeGraph)` + mapping plural→singular (workflows→workflow, skills→skill, agents→agent, tools→tool); "workflow <keyword>" dùng `library` (WorkflowLibrary) — pin: `SystemKnowledge(catalog, graph, library)`.
2. **Macro phân vai**: Normalizer `^@` chỉ set confidence=1.0 (KHÔNG tra library); Matcher là nơi duy nhất validate macro → workflow_name.
3. **Query "workflow <keyword>"**: nguồn = library.search (khác catalog); trả "Workflows: <names>".

### R3 — (ghi chú implement)
1. 7 file test (thêm test_agent_selector) — sửa số liệu Phạm vi #10
2. handle(NormalizedRequest) → skip Normalizer, chạy từ RuleEngine
3. plan=None khi resolved trước planner
4. Matcher token search: duyệt token theo thứ tự, dừng ở token đầu có match (first)
5. Matcher dùng library từ constructor (không qua tham số match)
6. PlannerStub intent_map: exact text match
7. Ghi chú: caller inject CÙNG library instance cho normalizer + matcher
8. Dict input "params": user params merge với regex-extracted (user thắng)

## Kết luận
- [x] **Resolve toàn bộ (2 R1 + 3 R2 + 8 R3)** — spec cập nhật, sẵn sàng implement.
