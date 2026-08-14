# TASK-026 — Test Results (Planning Engine)

**Ngày**: 2026-08-15 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `1003 passed, 0 failed` (baseline 949 → +54 test mới)
- **Coverage**: 95.00% (threshold 80% cứng — pass)
- **Arch tests**: 31/31 pass (gồm 5 test INV-014/planning mới)

## Test mới (54)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_planning_engine.py` | 48 | contracts (extra=forbid, RiskReport.highest, 8 rules, report.valid, PlanningError.report), goal analyzer (intent/target/complexity/workflow token-match/determinism), decomposer (review 6 node §12 exact, SIMPLE 1 node, test rule skeleton, OPEN rỗng, register template), dependency (topo, self/unknown flag), capability (sạch, unknown risk, no-tools risk), risk (items==[] §12, open_goal, many_nodes), planner build (template path, workflow path retries/timeout fall-through, max_nodes), validator 8 hạng mục (contract, capability, permission, policy deny/ask, dependency, resource, cycle, timeout) + engine gate C1-03 (cycle/depbad → PlanningError đúng rule), engine (rule/template offline llm_calls==0, deterministic, LLM path stub → coding template 3 node, error → llm_calls==1, planner None, medical→doctor), INV-014 behavioral |
| `tests/test_architecture.py` | +5 | `test_inv_planning_import_allowlist`, `test_inv014_planning_gate` (AST call-site), `test_inv014_runtime_no_planning`, `test_inv014_validation_has_8_rules`, `test_inv014_no_god_object` |
| `tests/test_runtime_kernel.py` | +1 | `test_planning_engine_wired` (resolve + offline plan) |

## Kiểm chứng AC (11/11)
- **AC1** ✅ Contracts extra=forbid; ValidationRule đủ 8; PlanningError giữ report
- **AC2** ✅ GoalAnalyzer: intent/target/complexity deterministic; workflow token-match
- **AC3** ✅ Decomposer: review 6 node §12 exact (type/deps), TEMPLATE vs RULE phân biệt, OPEN rỗng
- **AC4** ✅ DependencyAnalyzer topo order + flag
- **AC5** ✅ CapabilityResolver: sạch/unknown-high/no-tools-medium; agent theo intent
- **AC6** ✅ RiskAnalyzer: VD §12 items==[] exact; open_goal; many_nodes
- **AC7** ✅ ExecutionPlanner: workflow path (retries/timeout fall-through), template path, DRAFT, max_nodes guard
- **AC8** ✅ INV-014 validator 8 hạng mục; engine gate parse node_id + đúng rule; cycle T1→T2→T3→T1 → PlanningError cycle fatal
- **AC9** ✅ Offline ladder: workflow/template/rule → llm_calls==0; LLM path llm_calls==1; reset/last_result; deterministic 2 lần
- **AC10** ✅ Wiring: resolve PlanningEngine; plan offline; Settings parse block planning; 1003 pass / 95.00%
- **AC11** ✅ Architecture: 5 arch test pass; additive only (git diff: 6 MOD + 3 NEW)

## Ghi chú / Deviations
1. **Test-only intents** `cyclic`/`depbad` thêm vào bảng keyword goal_analyzer (để engine gate test cycle/dependency qua template).
2. **CapabilityResolver nhận `intent` param** — agent fill theo goal intent (spec YC-5 "plan-level agent từ goal.intent map"); review template khai báo agent="coder" trực tiếp.
3. **Engine set source TEMPLATE** khi decompose dùng template (goal.source từ analyzer chỉ là RULE).
4. **LLM path reuse template** — intent "coding" → coding template 3 node (spec YC-10 "map intent → template"); generic 2-node fallback khi không template.
5. **Validator contract fail → early return** (nodes có thể raw dict — tránh AttributeError các mục sau).
6. **Engine gate phân loại rule** theo message: cycle detected → CYCLE; depends on unknown → DEPENDENCY; else CONTRACT.
7. `PolicyDecision.reason` field tồn tại ✓ — validator dùng đúng.

## Kết luận
- [x] Tất cả 11 AC pass
- [x] Full suite 1003 pass, coverage 95.00%
- [x] INV-014 enforced (behavioral + AST); offline-first verified (llm_calls==0 cho 3 bậc đầu)
