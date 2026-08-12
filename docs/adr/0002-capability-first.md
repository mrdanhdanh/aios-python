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
