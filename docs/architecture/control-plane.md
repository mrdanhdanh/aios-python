# Control Plane — AIOS 1.0

> Control Plane = bộ não vận hành AIOS: Orchestrator + các registry + Policy/Governance. Mọi thao tác quản trị/điều phối đi qua đây (INV-005: Orchestrator không God Object; INV-007: Policy First; INV-029: tenant workload không truy cập nội bộ ngoài API contract).

## Thành phần (module thật — `backend/src/aios_core/`)

| Nhóm | Module | Vai trò |
|------|--------|---------|
| Decision Pipeline | `orchestrator/normalizer.py` · `rule_engine.py` · `workflow_matcher.py` · `planner.py` | 4 tầng offline-first: 70–90% request dừng ở Rule Engine, 0 token |
| Planning (M5) | `orchestrator/planning/` (goal_analyzer, task_decomposer, dependency_analyzer, capability_resolver, risk_analyzer, execution_planner, validation, engine) | Task graph + plan validation (INV-014) |
| Điều phối | `orchestrator/agent_selector.py` · `capability_router.py` · `supervisor.py` · `failure_recovery.py` (trong `goals/`) | Chọn agent/capability, giám sát, recovery |
| Governance | `orchestrator/goals/` (goal, task_queue, permission_broker) · `policy/` · `enterprise/` (identity, tenancy, governance, security) | Policy Engine, Permission Broker, RBAC/ABAC (INV-022..029) |
| System Brain | `catalog/` · `knowledge_graph/` · `orchestrator/system_knowledge.py` | System Catalog + Knowledge Graph — trả lời O(1), không quét registry |
| Cải tiến | `orchestrator/advisor.py` · `evaluation_collector.py` · `goals/reporting.py` | Improvement Advisor, Evaluation Collector (M4) |
| Autonomy (M9) | `autonomous/` (goal, planner, world, loop, governor, recovery, long_horizon, memory, stuck, experimentation, evaluation, multi_agent, scheduler) | Autonomy Layer — định hướng Orchestrator (INV-030..034) |

## Registry (thuộc Control Plane)

`models/registry.py` (ModelRegistry) · `capabilities/registry.py` (CapabilityRegistry) · `agents/registry.py` · `workflow/library.py` (WorkflowLibrary) · `skills/registry.py` · `plugins/registry.py` · `ecosystem/registry.py` · `prompts/registry.py` · `contracts/` (ContractCatalog 1.0 — TASK-064)

## Bất biến liên quan (Constitution 1.0)

- INV-005 Control Plane Isolation — Orchestrator không God Object (module hóa, arch test).
- INV-007 Policy First — policy quyết định trước execution; Permission chỉ là 1 phần.
- INV-013 Model Routing Policy — model selection phải qua Routing Policy.
- INV-014 Plan Validation — Execution Plan validate trước runtime.
- INV-022 Identity First · INV-023 Tenant Isolation · INV-024 Credential Isolation · INV-025 Resource Fairness · INV-029 Control Plane Isolation (M7).

## Luồng quyết định

```
Request → Normalizer → Rule Engine → Workflow Matcher → (Planner LLM nếu cần)
       → Policy check → Memory Coordinator → Context Optimizer → Model Router
       → Planning Engine → Execution Graph → Policy re-check → Execution
```
Policy được kiểm tra TRƯỚC model selection và TRƯỚC execution (PLAN §M5-20).
