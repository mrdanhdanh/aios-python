# TASK-026 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (15 + 11 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. Contracts** — `orchestrator/planning/contracts.py`: PlanSource, GoalComplexity, GoalAnalysis, TaskSpec (type PlanNodeType — C2-04), RiskItem/RiskReport, ValidationRule (8), PlanValidationIssue/Report, PlanningResult (plan bắt buộc — C3-02); `orchestrator/errors.py` +PlanningError
- [ ] **T2. GoalAnalyzer** — `goal_analyzer.py`: keyword table LOCAL (C2-02), target regex, complexity, known-workflow token-match `re.split(r"[^a-z0-9]+")` (C2-06)
- [ ] **T3. Templates + TaskDecomposer** — `templates.py` (TASK_TEMPLATES review 6 node §12 exact type; test; coding; chat) + `task_decomposer.py` (3 đường: WORKFLOW skip / TEMPLATE / RULE phân biệt rõ — C3-04; OPEN → rỗng)
- [ ] **T4. DependencyAnalyzer** — `dependency_analyzer.py`: verify depends_on + topo order (stable, id asc), flag invalid
- [ ] **T5. CapabilityResolver** — `capability_resolver.py`: capabilities ⊆ list (fatal + risk), agent điền theo intent map, tools_for rỗng → risk medium
- [ ] **T6. RiskAnalyzer** — `risk_analyzer.py`: `analyze(goal, tasks, settings)` (C2-03 v2), 4 rules, sort (level, kind), items==[] cho VD §12 (C3-01)
- [ ] **T7. ExecutionPlanner** — `execution_planner.py`: build (known workflow path với retries fall-through — C2-06; template/rule path), id/request_ref/created_at deterministic (C2-01), DRAFT status, max_nodes guard
- [ ] **T8. PlanValidator** — `validation.py`: 8 hạng mục (contract/capability/permission/policy requires_approval C1-02/dependency/resource/cycle/timeout), issues sorted, continue-after-fatal accumulate (C3-03), validate() + ValidationContext
- [ ] **T9. Engine** — `engine.py`: pipeline điều phối 7 module (offline ladder), try/except ValidationError → PlanningError (C1-03), llm_calls sau gọi kể cả error (C2-08), last_result/reset_calls lock, latency_ms monotonic
- [ ] **T10. LLM path** — `_plan_with_llm`: router.select → registry.get (C1-01), wrap RouterError/ModelError (C2-08 v2), model None + router None guard (C2-10 v2), normalize intent medical→doctor (C2-05 v2), generic skeleton [T1, T2 Report] (C2-05 v2), workflow_names ảo skip (C2-09 v2), planner None → PlanningError
- [ ] **T11. Config + wiring** — `config.py` PlanningSettings + `config.yaml` planning block + `runtime_kernel.py` (lazy import; **registry=model_registry — C2-01 v2**)
- [ ] **T12. Unit tests** — `tests/test_planning_engine.py`: contracts, goal_analyzer (intent/target/complexity/workflow token-match), decomposer (6 node §12 exact, TEMPLATE vs RULE), dependency (topo), resolver (capability lạ — assert đơn vị C2-11), risk (items==[]), planner build (workflow path, retries, DRAFT), validator 8 hạng mục (model_construct C1-03; PolicyService deny C2-07; cycle → PlanningError), engine (offline ladder llm_calls==0, deterministic 2 lần), LLM path (stub medical→doctor, error → llm_calls==1, planner None), wiring (OPEN qua container không crash — C2-01 v2)
- [ ] **T13. Arch tests** — `test_architecture.py`: `test_inv_planning_import_allowlist` (loop files C2-12 v2; 3-dots imports C2-07 v2), `test_inv014_planning_gate` (AST call-site `self._validator.validate(` — pattern INV-007), `test_inv014_runtime_no_planning` (kernel/services không import planning), `test_inv014_validation_has_8_rules`, `test_inv014_no_god_object` (scan chuỗi c1..c6 — C2-04 v2)
- [ ] **T14. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (95% mục tiêu); git diff verify additive only
- [ ] **T15. test.md + evaluation.md** — đối chiếu 11 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
