# ADR-0001: Workflow Engine Independence

- **Status**: accepted
- **Date**: 2026-08-12

## Context
AIOS must not be locked into a single workflow engine (LangGraph, CrewAI, AutoGen...).
M1 introduced a declarative `WorkflowDefinition` contract compiled to an internal
`ExecutionPlan`; the engine executes nodes with retry/timeout/cancel/snapshot.

## Decision
Keep `WorkflowDefinition` fully engine-agnostic. Engines plug in behind a
`WorkflowCompiler` interface (`compile(definition) -> ExecutionPlan`). M1 ships
`MockCompiler` (runs on `ExecutionService`); `LangGraphCompiler` is a stub with
`is_available() == False`. Swapping engines = adding a compiler, never changing
definitions, orchestrator, or execution semantics.

## Consequences
- Positive: engine migrations are additive; simulation works offline without LangGraph.
- Negative: the compiler layer is an indirection — LangGraph-specific features
  (checkpointing graph state) need explicit mapping to `ExecutionPlan` later (M2/M4).

# ADR-0002: Capability-First (Agents never bind to tools)

- **Status**: accepted
- **Date**: 2026-08-12

## Context
Agents must not hard-code tool dependencies (Docker sandbox, MCP, REST...). M1
built `CapabilityRegistry`: agents declare capabilities (`execute_code`,
`read_file`); tools bind to capabilities; routing happens at runtime.

## Decision
Agents (and the Orchestrator's Capability Router) only ever reference capability
names. Tools declare `capabilities` in their contracts; the registry maps
capability → tools with priority/health-based selection (M2). Swapping the tool
behind a capability never touches agent code.

## Consequences
- Positive: testability (mock tool behind a capability), extensibility (new tools
  serve existing capabilities), clear audit ("who uses execute_code" via graph).
- Negative: an extra indirection layer; capability naming requires governance to
  avoid near-duplicate names (e.g. `execute_code` vs `run_code`).

# ADR-0003: Policy-First (Pre-execution gate)

- **Status**: accepted
- **Date**: 2026-08-12

## Context
Untrusted or expensive requests must be gated before any execution. M1 built
`PolicyService` (deny > approval > allow) + `PermissionService` (allow/deny/ask).

## Decision
Every execution path goes through policy evaluation BEFORE resource acquisition
and node execution. Permissions are one facet of policy (scopes); policy also
covers token budget, internet access, sandbox requirement, approval. The
`ExecutionService` pre-checks policy and returns FAILED with a reason — never
runs nodes when policy denies.

## Consequences
- Positive: fail-fast, auditable gates; safe default (unknown scope → ask/deny).
- Negative: policy evaluation adds latency on every run; approval flows need a
  broker (Permission Broker, M2/TASK-012) to avoid blocking the pipeline.
