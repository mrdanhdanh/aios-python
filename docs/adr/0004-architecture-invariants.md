# ADR-0004: Architecture Invariants (control-plane isolation, capability-first)

- **Status**: accepted
- **Date**: 2026-08-13

## Context
As the number of Agents/Skills/Tools grows, the architecture must stay
enforceable. The master plan (PLAN.md) already states the Control Plane /
Worker Plane split and "Orchestrator is the ONLY agent touching Runtime
services". A user architecture review (12 points) asked to pin these rules as
**invariants** with automatic tests, so violations fail review instead of being
missed.

## Decision
Pin 10 Architecture Invariants (INV-001..INV-010) in `docs/architecture.md`
§7, with automatic enforcement via AST import-graph tests
(`backend/tests/test_architecture.py`, pure `ast.parse` — no runtime import).
Four invariants are the hard core:

1. **Orchestrator is not a God Object** (INV-005) — it coordinates via the
   Runtime API and System Knowledge (Registries → Catalog → KG → System
   Knowledge), it does not own/duplicate Runtime services and does not import
   concrete model providers (allow-list: only `models.base` + `models.errors`
   in `planner.py`).
2. **Agents never touch Tools directly** (INV-002) — all access goes through
   Capability (enforced when `agents/` + `tools/` exist, TASK-013/014).
3. **Workflows don't know the engine** (INV-003) — definitions are declarative;
   `workflow/**` must not import langgraph or models.
4. **Execution never bypasses Policy** (INV-007) — `ExecutionService` must
   keep its `self._policy.evaluate(...)` call-site (hard AST test).

## Consequences
- Positive: enforceable by CI/reviewer; workers stay decoupled; upgrades
  (skills/tools) can't silently break layering; System Knowledge becomes the
  "System Brain" instead of a god object.
- Negative: AST tests need maintenance as new modules appear (directory-scan
  rules); INV-001/002 are latent until agents/tools land.
- **Known gap (v1)**: `sandbox_required` from policy is NOT enforced in
  `ExecutionService` (only `logger.warning` at execution.py:153) — sandboxing
  is deferred; INV-007 covers scope/token/internet pre-check only until then.
- INV-008 (Artifact First) and Architecture Health (M4) are recorded, not yet
  enforced.
