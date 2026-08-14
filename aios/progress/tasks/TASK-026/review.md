# Review — TASK-026 (Planning Engine) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-15

## Kết luận
- [x] **APPROVED có điều kiện** — 0 R1 (blocker); 3 R2 + 6 R3 (resolve trong implement).

## Kiểm chứng trọng tâm (đối chiếu code thật)
- (a) `PlanNodeType` (kernel/execution_plan.py: TASK/TOOL/LLM/DECISION) khớp spec ✓
- (b) `validate_dag` detect cycle (3-color DFS, message "cycle detected...{node_id}") → C1-03 regex khả thi; `ExecutionPlanBuilder.from_dict` idempotent ✓
- (c) `CapabilityRegistry` có list()/tools_for()/get() — spec dùng đúng API; KHÔNG có task→agent mapping → agent map local bắt buộc ✓
- (d) `PolicyService.evaluate` → ASK: `approved=True, requires_approval=True` (C1-02 đúng); deny: `approved=False, requires_approval=False, reason="denied scopes..."` ✓
- (e) LLM path: `ModelRouter.select` thuần (0 LLM); `Planner.plan()` gọi `model.is_available()` trước (không tăng calls khi unavailable); `mock.calls` public ✓
- (f) Allow-list: `dir_imports` glob non-recursive → INV-005 rule A KHÔNG phủ `orchestrator/planning/` → allow-list mới là enforcement thật (C2-02 v2 đúng); `_resolve_relative` 3 dots ✓; INV-013 rglob không đụng planning ✓
- (g) config: `_yaml_extra_keys_guard` động → block `planning` tự nhận; env override OK ✓
- (h) wiring: `model_registry`, `model_router`, `resources_settings`, `bus` trong scope create() ✓
- INV-014 chưa có enforcement — 5 test mới không xung đột ✓

## Vấn đề
### R2 (major)
- **R2-1**: Block wiring YC-11 bị dán trùng 2 lần mâu thuẫn (block 1 có registry=model_registry; block 2 THIẾU registry + model=None vs default() trái nhau).
  → **Resolution**: gộp 1 block duy nhất: `PlanningEngine(library=WorkflowLibrary(), capabilities=CapabilityRegistry(), policy=PolicyService(bus), resources=resources_settings, planner=Planner(), model=None, router=model_router, registry=model_registry, settings=settings.planning)` — `model=None` (router quyết định khi LLM path), `settings=settings.planning` (đã là PlanningSettings).
- **R2-2**: Allow-list §5.2 thiếu logging (`logging` external / `aios_core.logging` aios).
  → **Resolution**: thêm `"logging"` + `"aios_core.logging"` vào §5.2.
- **R2-3**: Giả định §7 "execution vẫn chạy khi orchestrator quyết định approve" SAI — `execution.py _run` trả FAILED "approval required" khi `decision.requires_approval` (runtime đọc lại policy, không đọc plan.needs_approval).
  → **Resolution**: sửa giả định — v1 `needs_approval` chỉ là metadata (Human Approval cho orchestrator v2 / 027-028); plan cần approval hiện không chạy qua ExecutionService v1 (không sửa execution — đúng Out); test không kỳ vọng plan ASK execute được.

### R3 (minor)
- **R3-1**: `GoalAnalysis.source` — analyzer set `source=RULE` mặc định (engine ghi đè sau).
- **R3-2**: `StepSpec` ghi rõ là class nội bộ `templates.py` (extra=forbid, type: PlanNodeType).
- **R3-3**: `TASK_TEMPLATES = {review, coding}` — intent `test` KHÔNG template → RULE.
- **R3-4**: Rule OPEN — thêm fallback: intent không match + text > N từ → OPEN (đa ngôn ngữ).
- **R3-5**: Resolver đánh dấu `task.invalid` (pattern dependency_analyzer) — engine re-check / validator báo fatal (defense đủ).
- **R3-6**: `plan.id = f"plan:{source}:{intent}"` trùng request cùng intent — v1 chưa nối execution nên chấp nhận; ghi note cho 027.

## Resolution ghi nhận (phản ánh trong spec v4 + implement)
- R2-1 → spec v4 YC-11 wiring block gộp 1
- R2-2 → spec v4 §5.2 allow-list +logging
- R2-3 → spec v4 §7 giả định sửa
- R3-1..R3-6 → spec v4 + implement
