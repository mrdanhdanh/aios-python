# TASK-090 — Tasks breakdown (checklist)

> M13-P1 Harness Coverage — spec v3 (19 AC). Dependency: P1 → P2 (TASK-091).

## 1. Module `harness/coverage/`

- [ ] `errors.py`: `CoverageError(HarnessError)`
- [ ] `contracts.py`: `CoverageDimension` (9), `NegativePath` (8), `CoverageItem`, `DimensionCoverage`, `NegativePathCoverage`, `HarnessCoverageReport` (KHÔNG status), `HarnessReadinessStatus`, `HarnessReadinessReport` (hard_gates: list[HardGate])
- [ ] `coverage.py`: `HarnessCoverage` — build(): auto-collect 9 chiều (Component exclude self 7 / Contract 21 / State 14 / Transition 12 / Event 6 / Failure-mode 8 / Scenario 20 GS / Verification-path 12 / Artifact 2) + negative-path 6/8 (evidence anchored backend root) + evidence check (find_spec/Path.exists) + report (ratio/overall_ratio/negative_path_ratio/metrics/summary/reproducible)
- [ ] `readiness.py`: `HarnessReadinessScorer` — score(): 7 dims (Structural/Contract/Behavioral/Failure mean(4)/Replay/Scenario/Production=0.0) + hard gates (replay ≥ min_replay, production conditional, overall) + param validation (0,1] → ValueError
- [ ] `harness.py`: `CoverageHarness` (id="coverage") — run/verify (fail-closed)/_persist/get_report
- [ ] `__init__.py`: export

## 2. Wiring + CLI

- [ ] `kernel/runtime_kernel.py`: đăng ký `CoverageHarness` (id="coverage") + registry shared + StateService
- [ ] `workflow/cli.py`: subcommand `harness coverage` (flags: --min-overall/--min-replay/--production-tests/--no-strict) + dispatch + `_harness_coverage()` (JSON document + exit 0/1)

## 3. Tests `tests/test_harness_coverage.py`

- [ ] TestContracts: enums (9+8), defaults, extra="forbid"
- [ ] TestCoverage: 9 chiều auto-collect (AC1-5), negative 6/8 + evidence check (AC6/18), registry rỗng (AC15), determinism (AC13), metrics/summary (AC14), đủ keys (AC16)
- [ ] TestReadiness: 7 dims + overall + gates (AC7), NOT_READY fail-closed (AC8), production conditional (AC17), param validation (AC19)
- [ ] TestHarness: registry + lifecycle + persist round-trip (AC9), strict → DIAGNOSED/FAILED (AC11)
- [ ] TestWiring: RuntimeKernel → registry có coverage
- [ ] TestCLI: exit 1 v1 + JSON document (AC10)

## 4. Verify

- [ ] Test file mới PASS
- [ ] Full suite không regression (AC12)
- [ ] arch-health 0 violations + doctor healthy
- [ ] CLI thật: `aiagent harness coverage` → NOT_READY exit 1 + JSON đủ

## 5. Docs & DoD

- [ ] Cập nhật PLAN.md §M13 P1 (done + ghi chú fail-closed v1 NOT_READY)
- [ ] Cập nhật PROGRESS.md + LOG.md
- [ ] Commit