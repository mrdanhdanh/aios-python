# ADR-0008: Harness Trust Architecture — System Readiness ≠ Harness Trust

> Quyết định kiến trúc: tách System Readiness và Harness Trust thành 2 score
> độc lập, kết hợp qua Release Gate (pure combiner, fail-closed).

- **Status**: accepted
- **Date**: 2026-08-18
- **Extends**: [ADR-0004](0004-architecture-invariants.md) (architecture invariants, INV-017..021), [ADR-0007](0007-compatibility-migration-policy.md) (compatibility policy)
- **Milestone**: M13 — Harness Trust & Behavioral Conformance (Issue #8)

## Context

M13-P0 (TASK-089) built the Behavioral Conformance engine. M13-P1 (TASK-090)
built the Harness Coverage model (9 dimensions) + Readiness scoring. M13-P2
(TASK-091) built the Meta-Harness (verify-the-verifier). M13-P3 (TASK-092)
built the Release Gate.

However, there was no **formal architecture decision** defining: (1) that System
Readiness and Harness Trust are two independent concepts; (2) how the Release
Gate composes them; (3) how the 4 invariants贯穿 the Harness Track are enforced.

This ADR pins these design decisions so that M14 (Controlled Self-Healing) and
M15 (Autonomous Harness) can build on a stable foundation.

## Decision

### 1. Two Independent Scores

**System Readiness** and **Harness Trust** are two **independent, non-interchangeable** concepts:

| Concept | Source | What it measures | Status enum |
|---------|--------|-----------------|-------------|
| System Readiness | `HarnessReadinessReport` (CoverageHarness) | System coverage and readiness | `READY` / `NOT_READY` |
| Harness Trust | `MetaReport` (MetaHarness) | Whether the verifier itself is trustworthy | `PASS` / `FAIL` |

**Key design principle**: The Release Gate is a **pure combiner** — it does
NOT know how to compute readiness or trust; it only composes two already-computed
reports. This ensures true separation.

### 2. Release Gate (fail-closed)

```
Release Gate = PASS    iff  (System Readiness == READY)  AND  (Harness Trust == PASS)
             = BLOCKED  otherwise
```

- **fail-closed**: any exception → BLOCKED (never crash, never return PASS)
- **Sub-harness failure** → try/except → BLOCKED (always produces a verdict)
- **CLI**: `aiagent harness release` → JSON document + exit 0 (PASS) / 1 (BLOCKED)

### 3. Four贯穿 Invariants

M13 establishes 4 invariants贯穿 the Harness Track:

| Invariant | Status | Enforcement location |
|-----------|--------|---------------------|
| **FAIL-CLOSED** | ✅ M13 established | INV-035 + Release Gate + Meta-Harness |
| **INDEPENDENT VERIFICATION** | ✅ M13 established | Meta-Harness independent oracle (hardcoded) + Release Gate combiner |
| **PERMISSION BOUNDARY** | 📋 M14 | Permission Broker + Human Approval |
| **CERTIFIED BASELINE/ROLLBACK** | 📋 M14 | Certified Baseline + Rollback |

### 4. Anti-Circular Design

Meta-Harness uses a **hardcoded oracle** (MetaOracle enum) to compute
`expected_state` — it does NOT call the production verifier to determine
expected results. This ensures independence of the verification path.

```
Production verifier → Meta test oracle → Expected invariant (hardcoded)
```

Residual circularity (oracle shares the same spec source) is documented;
M16 (dsh) will provide a truly independent verification path.

### 5. Pipeline

```
Execute → Verify → Behavioral Conformance → Meta-Verify →
Measure Coverage → Establish Harness Trust → Release Gate
```

## Consequences

- **Positive**:
  - True separation — readiness and trust are computed independently and
    cannot substitute for each other
  - Release Gate is a pure combiner — easy to test, replace, and reason about
  - Fail-closed — any exception leads to BLOCKED, never a false PASS
  - 4贯穿 invariants provide a clear safety framework
- **Negative**:
  - Requires maintaining two independent scoring systems (readiness + trust)
  - Release Gate adds no new verification logic — it is a pure combiner
- **Known limitation**: The hardcoded oracle means Meta-Harness "independence"
  is logical (different code paths), not a truly independent source. M16 (dsh)
  will provide a truly independent verification path.
