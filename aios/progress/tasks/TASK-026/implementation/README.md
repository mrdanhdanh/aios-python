# TASK-026 — M5 Planning Engine — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `orchestrator/planning/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/orchestrator/planning/` — 11 file:
  - `contracts.py`, `goal_analyzer.py` (keyword local + token-match workflow), `task_decomposer.py` (3 đường), `dependency_analyzer.py` (topo + flag), `capability_resolver.py` (agent theo intent), `risk_analyzer.py` (4 rules), `execution_planner.py` (workflow/template path + DRAFT), `validation.py` (8 hạng mục INV-014 + early-return), `engine.py` (ladder offline + LLM path reuse template + gate phân loại rule), `errors.py` (+`PlanningError`), `__init__.py`
- `backend/src/aios_core/config.py` — `PlanningSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring

## Key behavior
- Goal → Goal Analyzer → Task Decomposer → Dependency Analyzer → Capability Resolver → Risk Analyzer → Execution Planner → Execution Graph
- Planning KHÔNG nhất thiết LLM: Known workflow → Template planning → Rule planning → LLM planning (offline-first)
- Plan Validation (INV-014): Contract · Capability · Permission · Policy · Dependency · Resource · Cycle · Timeout — reject circular dependency trước Runtime

## Verification
- `pytest` full suite: **1003 passed, coverage 95.00%, 11/11 AC** (xem `test.md`)
