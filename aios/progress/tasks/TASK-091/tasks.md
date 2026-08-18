# TASK-091 — Tasks breakdown (checklist)

> M13-P2 Meta-Harness (P2). Spec v3 (tích hợp critique-1 2P1/5P2/3P3 + critique-2 1P1/4P2/5P3).
> Dependency: P0 (TASK-089 ✅) → P1 (TASK-090 ✅) → P2 → (P3 TASK-092 ∥ P4 TASK-093)

## 1. Khảo sát (done)
- [x] Đọc `harness/execution/{evidence,contracts,pipeline,replay}.py`, `harness/contracts.py`, `harness/coverage/{coverage,readiness}.py`, `harness/runner.py`, `harness/registry.py`, `kernel/runtime_kernel.py`, `workflow/cli.py`, `tests/test_harness_coverage.py`

## 2. Contracts (`harness/meta/contracts.py`)
- [x] `MetaCase` enum (8 cases)
- [x] `MetaOracle` enum (NOT_PASS/FAIL/INCONCLUSIVE/TAMPER/CORRUPT) — P2-4
- [x] `MetaCaseResult` (verifier_state:str, expected_state:MetaOracle, fail_closed:bool, detail)
- [x] `MetaStatus` (PASS/FAIL)
- [x] `MetaReport` (cases, all_fail_closed, status, metrics{total,fail_closed,by_case}, summary, reproducible) — P3-3

## 3. Engine (`harness/meta/engine.py`)
- [x] `MetaHarnessEngine` — thuần, chạy 8 cases, oracle hardcode (P2-1)
- [x] Case 1 FALSE_POSITIVE: evidence thiếu critical + check pass → INCONCLUSIVE → fail_closed
- [x] Case 2 FALSE_NEGATIVE: check fail → FAIL → fail_closed
- [x] Case 3 MALFORMED_EVIDENCE: evidence rỗng → INCONCLUSIVE → fail_closed
- [x] Case 4 BROKEN_VERIFIER: stub luôn PASS trên evidence thiếu → Meta PHÁT HIỆN → fail_closed=True (scenario a, P1-1)
- [x] Case 5 CORRUPTED_ARTIFACT: sha256(content) != ref → phát hiện (P2-2, hashlib đã allow)
- [x] Case 6 REPLAY_MISMATCH: evidence tampered → replay_verdict msg "TAMPER" → fail_closed (P2-3)
- [x] Case 7 SKIPPED_VERIFICATION: check skipped + passed → effectively_passed=False → INCONCLUSIVE → fail_closed (INV-035)
- [x] Case 8 VERIFY_SKIPPED: HarnessRunner COMPLETED without verify → Meta PHÁT HIỆN → fail_closed=True (scenario a, P1-1, P2-4)
- [x] Gọi `has_critical_evidence` TRƯỚC `compute_verdict` (P3-5)
- [x] `all_fail_closed = all(c.fail_closed)`; status PASS iff all_fail_closed

## 4. Harness (`harness/meta/harness.py`) + errors
- [x] `MetaError(HarnessError)`
- [x] `MetaHarness(Harness)` — id="meta", name="meta-harness" (P2-3), version="1.0.0"
- [x] `__init__(engine=None, *, state_service=None)` → route state_service vào engine (P2-2)
- [x] `run(ctx)` → engine.run() → report.model_dump
- [x] `verify(ctx, payload)` → strict + status != PASS → raise MetaError (INV-035)
- [x] `_persist` / `get_report(run_id)`

## 5. Wiring + CLI
- [x] Register `MetaHarness` vào `HarnessRegistry` (runtime_kernel.py)
- [x] CLI: parser group `harness` + subcommand `meta` + handler `_harness_meta` + dispatch + `--no-strict` (P3-2)
- [x] `aiagent harness meta` → JSON + exit 0 (PASS) / 1 (FAIL)

## 6. Cập nhật TASK-090 (negative 8/8)
- [x] `_NEGATIVE_PATHS` CORRUPTED_EVIDENCE + REPLAY_MISMATCH → covered=True (evidence "module:aios_core.harness.meta")
- [x] `_COMPONENT_MODULES["meta"] = "aios_core.harness.meta"` (P2-5)
- [x] `make_registry` (test) thêm `MetaHarness` → total 7→8

## 7. Tests (`tests/test_harness_meta.py`)
- [x] AC1 enum 8 cases
- [x] AC2 FALSE_POSITIVE
- [x] AC3 FALSE_NEGATIVE
- [x] AC4 MALFORMED_EVIDENCE
- [x] AC5 BROKEN_VERIFIER (fail_closed=True)
- [x] AC6 CORRUPTED_ARTIFACT
- [x] AC7 REPLAY_MISMATCH
- [x] AC8 SKIPPED_VERIFICATION
- [x] AC9 VERIFY_SKIPPED (fail_closed=True, integration)
- [x] AC10 MetaReport shape (no timestamp)
- [x] AC11 registry + lifecycle + persist round-trip
- [x] AC12 fail-closed strict→MetaError
- [x] AC13 CLI PASS exit 0 / FAIL exit 1
- [x] AC14 full suite + arch-health + doctor
- [x] AC15 coverage 8/8 READY + 4 test coverage updated (P1-2/P2-1)
- [x] AC16 monkeypatch module-level (P3-4) → Meta FAIL (scenario b)
- [x] AC17 determinism run 2×

## 8. Test coverage cập nhật (4 test)
- [x] `test_negative_8_of_8` (rename P3-1)
- [x] `test_metrics_and_summary` ("negative 8/8")
- [x] `test_ready_when_meta_covered` (rename P3-1)
- [x] `test_components_8_exclude_self` (rename P2-1, total==8)

## 9. Docs/PROGRESS/LOG
- [ ] Update PLAN.md §M13 P2 (đánh dấu deviation nếu có)
- [x] Update PROGRESS.md (TASK-091 done)
- [x] Update LOG.md
- [x] Commit hard gate + implement
