# Session Note — TASK-011 (M1/P3 remediation)

## Status
- TASK-011 COMPLETE (hard gate: spec → critique×2 → tasks → review → implement → test → evaluate → [commit pending user confirm]).
- Full suite: **428 passed, coverage 95.76%** (gate `--cov-fail-under=80` PASS; project target ≥95%).
- All 9 P3 findings F-001..F-009 implemented + targeted tests.
- PROGRESS.md marked TASK-011 `done`; LOG.md + evaluation.md written.

## Key gotchas (reusable if touching these modules again)
1. `ResourceService.acquire_slot_wait` MUST wait OUTSIDE the `Condition` lock (use a plain `threading.Event.wait`), else `pending()`/`release_slot()` deadlock. FIFO wake via `release_slot` sets next waiter.
2. `WorkflowDefinition` uses `.nodes` (NOT `.steps`).
3. CLI doctor: wrap `_db_path` in `str()` before `json.dumps` (Path not JSON-serializable).
4. Context inheritance default = `inherit=False` (backward-compat); new tests pass `inherit=True` explicitly.
5. `acquire_slot()` stays NON-blocking (returns False when full) — `ExecutionService._run` depends on this.
6. `CapabilityRegistry.tools_for` copies the list (O(n)); benchmark O(1) on `reg.get()` instead. `tools_for` still correctness-checked.
7. `ContractMetadata` requires `id, name, version, author, license` + `contract_version, schema_version`.
8. Container import path is `aios_core.container`, NOT `aios_core.kernel.container`.

## Commit note
- Changes staged in working tree (14 M + 3 untracked: evaluation.md, test_benchmark.py, docs/adr/).
- NOT committed yet — awaiting explicit user confirmation to commit (per guardrail).
