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
