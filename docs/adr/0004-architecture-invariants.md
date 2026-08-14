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
- **M5 extension (planned, see PLAN.md M5 §22)**: 6 additional invariants
  INV-011..INV-016 (Memory Isolation, Context Budget, Model Routing Policy,
  Plan Validation, Graph Acyclicity, Scheduler Separation) are defined in the
  PLAN.md M5 — Core Intelligence milestone and will be enforced when M5 lands.
- **M6 extension (planned, see PLAN.md M6 §9)**: 5 additional invariants
  INV-017..INV-021 (Harness Isolation, Evidence First, Verification Before
  Verdict, Evaluation Determinism, Release Gate) are defined in the PLAN.md M6
  — AIOS Harness milestone and will be enforced when M6 lands.
- **M7 extension (planned, see PLAN.md M7 §13)**: 8 additional invariants
  INV-022..INV-029 (Identity First, Tenant Isolation, Credential Isolation,
  Resource Fairness, Distributed Execution Safety, Audit Completeness,
  Sandbox Boundary, Control Plane Isolation) are defined in the PLAN.md M7
  — Enterprise milestone and will be enforced when M7 lands.
- **M9 extension (planned, see PLAN.md M9 §33)**: 5 additional invariants
  INV-030..INV-034 (Autonomous Action Boundary, Autonomy Bounded,
  Long-running Resumable, Self-Improvement via Harness, Autonomous Memory No
  Unverified Promote) are defined in the PLAN.md M9 — Autonomous milestone and
  will be enforced when M9 lands. Note the user's draft reused INV-011..INV-015
  (already owned by M5); they were renumbered to INV-030..INV-034 to keep IDs
  globally unique for the AST enforcement test.
  This ADR remains the canonical source for INV-001..INV-010; the full set
  INV-001..INV-034 is tracked in PLAN.md.
- **M10 (AIOS 1.0 — Freeze, see PLAN.md M10)**: M10 does NOT add new invariants.
  It **freezes the entire set INV-001..INV-034** as the "AIOS Architecture
  Constitution 1.0" and promotes every violation from warning to **release
  blocker** (see PLAN.md M10 §5). The 15-item "core principle" list in the
  M10 draft is a thematic consolidation of the 34 canonical IDs; the M5/M6/M7
  invariants (INV-011..INV-029) are part of the Constitution and must NOT be
  dropped. Renumbering the 34 canonical IDs down to a clean INV-001..INV-015
  would be a breaking change (requires updating `test_architecture.py`, all
  milestone sections, and this ADR) and is deferred to AIOS 2.0 if ever needed.
