# TASK-026 — Evaluation (Planning Engine)

**Ngày**: 2026-08-15 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (11/11 AC pass — xem test.md)

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 Contracts | ✅ | TestContracts (5 test) |
| AC2 GoalAnalyzer | ✅ | TestGoalAnalyzer (5 test) |
| AC3 Decomposer | ✅ | TestDecomposer (5 test) |
| AC4 Dependency | ✅ | TestDependency (3 test) |
| AC5 Capability | ✅ | TestCapability (3 test) |
| AC6 Risk | ✅ | TestRisk (3 test) |
| AC7 ExecutionPlanner | ✅ | TestPlanner (3 test) |
| AC8 INV-014 validator | ✅ | TestValidator (11 test) + engine gate |
| AC9 Offline ladder | ✅ | TestEngine (10 test) |
| AC10 Wiring | ✅ | test_planning_engine_wired + 1003 pass / 95.00% |
| AC11 Architecture | ✅ | 5 arch test + git diff additive only |

## Đánh giá so với PLAN.md §M5-11..14
- **Planning Engine 7 bước** (§11): Goal Analyzer → Task Decomposer → Dependency Analyzer → Capability Resolver → Risk Analyzer → Execution Planner → Validation — đủ 7 module + validator, mỗi module 1 trách nhiệm (no God Object — arch assert)
- **Offline-first ladder** (§13): workflow → template → rule → LLM — 3 bậc đầu 0 LLM (llm_calls==0 verified); LLM path chỉ khi OPEN/complex; decomposition luôn deterministic (LLM chỉ chọn intent/workflow)
- **Plan Validation 8 hạng mục** (§14/INV-014): contract/capability/permission/policy/dependency/resource/cycle/timeout — behavioral test + AST gate call-site + runtime không phụ thuộc planning
- **Task Decomposition VD §12**: "Review module authentication và viết test" → template review 6 node exact `T1→{T2,T3}→T4→T5→T6` ✓

## Bài học
1. **pydantic model_copy chạy lại model_validator** — không thể tạo plan lỗi (cycle/dep) qua model_copy; phải qua engine gate (ValidationError → PlanningError) hoặc model_construct
2. **Template lookup theo intent, không theo text** — test-only intent phải có keyword trong bảng analyzer
3. **Engine phải set source đúng bậc** (TEMPLATE vs RULE) — analyzer chỉ biết RULE mặc định
4. **LLM path nên reuse template** thay vì skeleton generic — deterministic + tái sử dụng
5. **Contract fail → early return** trong validator (nodes có thể raw) — defense tránh AttributeError chuỗi
6. **Gate phân loại rule theo message** ("cycle detected"/"depends on unknown") — đủ chính xác cho report

## Đề xuất cho task sau
- **TASK-027 Execution Graph**: `plan.nodes` (PlanNode: id/type/name/agent/capabilities/depends_on/timeout_s/retries) + required_permissions/resources/estimated_tokens là input đủ — edge = depends_on; join/failure policy mapping ở 027
- **TASK-028 Parallel Scheduler**: plan READY từ engine → scheduler dispatch
- Orchestrator flow (PLAN §20): nối Planning Engine vào Decision Pipeline — đã wiring qua DI (resolve PlanningEngine)

## Kết luận
- [x] ĐẠT spec (11/11 AC)
- [x] INV-014 enforced (behavioral + AST); additive only
- [x] Offline-first verified; coverage 95.00% (toàn suite 1003 pass)
