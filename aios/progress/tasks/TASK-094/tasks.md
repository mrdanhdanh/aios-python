# TASK-094 — Tasks breakdown

## Implement
- [ ] T1: `harness/diagnose/contracts.py` — FailureSeverity + FailureRecord + FailureCorpusReport (extra="forbid")
- [ ] T2: `harness/diagnose/engine.py` — DiagnoseEngine (analyze, compute_signature, normalize_message)
- [ ] T3: `harness/diagnose/errors.py` — DiagnoseError(HarnessError)
- [ ] T4: `harness/diagnose/harness.py` — DiagnoseHarness(id="diagnose") + persist + get_corpus
- [ ] T5: `harness/diagnose/__init__.py` — exports
- [ ] T6: Wiring `runtime_kernel.py` — DiagnoseHarness vào registry + container
- [ ] T7: CLI `cli.py` — subparser `harness diagnose` + dispatch + handler

## Test
- [ ] T8: `tests/test_harness_diagnose.py` — 12 AC
- [ ] T9: Update 5 registry tests (thêm "diagnose" → 11 harness)
- [ ] T10: Chạy full suite + arch-health + doctor

## Docs
- [ ] T11: evaluation.md + test.md
- [ ] T12: PROGRESS.md + LOG.md + commit
