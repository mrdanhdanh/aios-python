# Critique vòng 1 — TASK-026 (Planning Engine)

**Critic**: subagent critic | **Ngày**: 2026-08-14 | **Spec phản biện**: v1

## Đánh giá chung
Spec kỹ (11 YC, 11 AC, AST enforcement, risk table tự phản biện) nhưng 3 P1 chặn implement đúng (2 mâu thuẫn code thật) + 8 P2. Mức sẵn sàng 3/5.

## P1 — Blockers

### C1-01: LLM path không implement được — ModelRouter không có API public lấy ModelContract theo tên
- `ModelRouter` chỉ có select/chat/last_decision/_candidates — không có accessor model theo tên; import models.registry vi phạm INV-005 rule A; sửa router vi phạm AC9 "models/* không đổi".
- **Resolution**: inject `ModelRegistry` (untyped) vào PlanningEngine (runtime_kernel đã có `model_registry` — additive); `model = registry.get(decision.model_name)`; branch `model_name is None → raise PlanningError("no model available")`. Sửa AC9 (models/* vẫn không đổi — chỉ thêm dependency inject).

### C1-02: YC-8.4 điều kiện (a) mâu thuẫn PolicyService.evaluate thật
- Nhánh ASK trả `PolicyDecision(approved=True, requires_approval=True)` — `approved=False + requires_approval=True` không bao giờ xảy ra → branch chết.
- **Resolution**: điều kiện non-fatal = `decision.requires_approval == True` (không xét approved; ghi chú service trả approved=True ở nhánh này).

### C1-03: Hạng mục Contract/Dependency/Cycle (1/5/7) không kích hoạt qua validate(plan) — ExecutionPlan._validate_plan gọi validate_dag ngay lúc construct
- Plan lỗi unique/unknown-dep/cycle không thể tồn tại để truyền vào validator; test cycle qua engine: build raise ValidationError — ai bắt?
- **Resolution (chọn a)**: engine/ExecutionPlanner.build wrap `try/except ValidationError` → parse node_id từ message → `raise PlanningError(msg, report)` issue cycle/dependency/contract; validator mục 1/5/7 giữ defense-in-depth, test qua `model_construct()`.

## P2 — Major
- **C2-01**: `ExecutionPlan.id` required không định nghĩa + `created_at=now()` phá AC5 determinism. → **Resolution**: `id = f"plan:{source}:{intent}"` deterministic; `request_ref = request.text[:200]`; `created_at = ""` (document v1); AC5 so sánh toàn bộ dump; MockCompiler trả đúng ExecutionPlan — cân nhắc tái dùng merge logic (sửa §9 lý do).
- **C2-02**: YC-2.1 "tái dùng rule_engine.default_rules" mâu thuẫn allow-list §5.2. → **Resolution (a)**: keyword table local trong goal_analyzer; bỏ import rule_engine.
- **C2-03**: `library.search()` substring toàn query — known-workflow detection gần như chết với text thật. → **Resolution**: GoalAnalyzer tự token-match từ `library.list()` names (deterministic local), không sửa library.py; ghi fixture requirement.
- **C2-04**: Không có mapping `StepSpec.kind` → `PlanNodeType` (ảnh hưởng estimated_tokens). → **Resolution**: `StepSpec` khai báo trực tiếp `type: PlanNodeType` (bỏ kind); AC2 assert type exact.
- **C2-05**: Intent vocabulary không nhất quán (doctor vs medical) + LLM intent lạ không fallback. → **Resolution**: chuẩn hóa `medical → doctor`; fallback cho mọi intent không template (rule skeleton generic 1-3 node); test phủ.
- **C2-06**: YC-7.1 mapping thiếu retries fall-through. → **Resolution**: bổ sung "`retries: node.retries if not None else definition.retries`" (nhất quán MockCompiler).
- **C2-07**: YC-12(e) gọi `set_policy` không tồn tại. → **Resolution**: dựng `PolicyService(bus, Policy(deny_scopes=["filesystem"]))`.
- **C2-08**: `llm_calls` increment vị trí mâu thuẫn (error path). → **Resolution**: tăng `_llm_calls` NGAY SAU gọi `planner.plan()` kể cả error path; sửa YC-10.5.

## P3 — Minor
- **C3-01**: YC-6 assert exact `items == []` cho VD §12.
- **C3-02**: `PlanningResult.plan: ExecutionPlan` bắt buộc (không None).
- **C3-03**: validate continue-after-fatal, accumulate tất cả issues.
- **C3-04**: Phân biệt TEMPLATE vs RULE: template = intent trong TASK_TEMPLATES; rule = SIMPLE/không template không OPEN; test phân biệt 2 đường.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve 3 P1 + 8 P2 + 4 P3 → spec v2, rồi critique vòng 2.
