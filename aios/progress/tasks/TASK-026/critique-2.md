# Critique vòng 2 — TASK-026 (Planning Engine)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
13/14 resolution đúng khớp code thật. C1-01 RESOLVED ĐÚNG khả thi NHƯNG wiring YC-11 bỏ sót `registry=model_registry` → P1 mới (C2-01). C1-02/C1-03/C2-01..C2-08/C3-01..04 đều RESOLVED ĐÚNG (verify PolicyService/ExecutionPlan/WorkflowLibrary/Policy signature).

## Mục B — Vấn đề mới

### P1
**C2-01**: YC-11 wiring THIẾU `registry=model_registry` — LLM path qua container: router inject nhưng registry None → `registry.get(...)` AttributeError; AC10 chỉ test RULE path nên lỗi im lặng.
→ **Resolution**: thêm `registry=model_registry` vào block wiring YC-11 + test: LLM path qua container (OPEN goal + Planner thật + mock model) trả plan hợp lệ (hoặc assert không crash).

### P2
**C2-02**: Claim "INV-005 rule A tự bao phủ planning/" SAI — `dir_imports` dùng `glob("*.py")` không đệ quy → không quét `orchestrator/planning/`.
→ **Resolution**: sửa §5.2/§5.6: enforcement = allow-list test mới; đề xuất sửa dir_imports recursive là việc riêng (không làm trong 026); vị trí subpackage vẫn đúng (3 lý do còn lại).

**C2-03**: `RiskAnalyzer.analyze(goal, tasks, plan_hint: dict)` — logic dùng settings nhưng signature không có; plan_hint không định nghĩa.
→ **Resolution**: đổi signature `analyze(goal, tasks, settings: PlanningSettings)`; `estimated_tokens` tính từ tasks type count (2000/200) — nguồn duy nhất.

**C2-04**: Tiêu chí scan No-God-Object (c) tự mâu thuẫn — task_decomposer BẮT BUỘC đọc goal.source/complexity/intent.
→ **Resolution**: định nghĩa scan cụ thể: (c1) goal_analyzer.py không chứa `decompose(`; (c2) goal_analyzer.py không chứa `TASK_TEMPLATES`; (c3) task_decomposer.py không chứa keyword-intent mapping (`"review|analyze|audit"`-style); (c4) engine.py không chứa `ValidationRule.` — ghi rõ từng chuỗi scan.

**C2-05**: LLM path chưa normalize intent (`medical` vs `doctor`) + "rule skeleton generic" chưa định nghĩa.
→ **Resolution**: YC-10.4: (a) normalize deterministic `medical→doctor`, intent ngoài bảng → `chat`; (b) generic fallback cố định: intent không template → RULE skeleton `[T1 <intent> (type=LLM), T2 Report (type=TASK, depends_on=[T1])]` (2 node); (c) test stub trả "medical" → intent doctor + skeleton đúng.

**C2-06**: Tokenizer known-workflow match — `"crud-generator".split()` không match `"crud"`.
→ **Resolution**: `re.split(r"[^a-z0-9]+", name.lower())` cho cả name lẫn text (split mọi ký tự không chữ-số); tie-break "nhiều token nhất → name asc"; test thêm hyphen/underscore.

### P3
- **C2-07**: Relative import planning/ phải dùng 3 dots (`from ...capabilities.registry`) — ghi chú spec.
- **C2-08**: `router.select` raise RouterError → wrap thành `PlanningError("no model available: ...")`.
- **C2-09**: workflow_names[0] không tồn tại trong library → bỏ qua (map theo intent); có → source=LLM, llm_calls=1.
- **C2-10**: `model is None and router is None → raise PlanningError("no model available")`.
- **C2-11**: Test resolver capability lạ assert trên return resolver đơn vị (engine raise sớm — RiskReport không qua engine).
- **C2-12**: Allow-list scan loop từng file (pattern `test_inv_tools_import_allowlist`) — sửa wording §5.2.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C2-01 (P1) + C2-02..C2-06 (P2) + P3 → spec v3. Sau vòng này **approve** (không cần vòng 3).
