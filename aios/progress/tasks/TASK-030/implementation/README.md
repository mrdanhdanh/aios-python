# TASK-030 — M6-H2 Execution Verification — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `harness/execution/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/harness/execution/contracts.py` — 5 loại Check + CheckResult + Verdict 4 state + VerificationTask + EvidenceServices (duck-typed Protocol)
- `backend/src/aios_core/harness/execution/evidence.py` — collect: `_resolve_state_key` 3 bước + `_collect_events` filter candidates + truncation detection + `has_critical_evidence`
- `backend/src/aios_core/harness/execution/pipeline.py` — run_checks 5 kinds + runner duck + skipped + compute_verdict (FAIL>INCONCLUSIVE>PASS) + build_result metrics deterministic
- `backend/src/aios_core/harness/execution/replay.py` — round-trip integrity + TAMPER dict-level + fallback tool-results
- `backend/src/aios_core/harness/execution/verification.py` — `VerificationHarness` kế thừa H1 + persist TRƯỚC raise + verdict.json convention
- `backend/src/aios_core/config.py` — `ExecutionSettings` (event_window/persist_verdict_artifact)
- `backend/src/aios_core/kernel/runtime_kernel.py` — EvidenceServices (state/events/artifacts shared)

## Key behavior
- Verification Pipeline: Execution → Collect Evidence → Deterministic Checks → Policy Checks → Tests → Evaluation → Verdict (PASS · PASS_WITH_WARNING · FAIL · INCONCLUSIVE)
- Evidence Package: request/normalized-request/plan/execution-graph/events/tool-results/test-results/evaluation/artifacts/verdict
- Replay: Production Run → Trace → Replay → Simulation → Debug (không chạy lại Tool thật)
- INV-019: không PASS chỉ vì execution không exception

## Verification
- `pytest` full suite: **1210 passed, coverage 95.26%, 10/10 AC** (xem `test.md`)
