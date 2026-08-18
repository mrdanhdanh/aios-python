# TASK-094 — Test results

> Date: 2026-08-18 | Task: M14-P0 Detect & Diagnose

## Test file: `backend/tests/test_harness_diagnose.py` — 32 test

| Class | Tests | Content | AC |
|-------|-------|---------|-----|
| TestContracts | 3 | FailureRecord shape, extra="forbid", severity enum | AC1 |
| TestSignature | 2 | deterministic, different inputs → different sig | AC2 |
| TestNormalize | 6 | timestamps, uuids, win/unix paths, hex, spaces | AC3 |
| TestAnalyze | 3 | FAILED→record, COMPLETED→None, DIAGNOSED status | AC4, AC5 |
| TestSeverity | 3 | HookError→HIGH, LifecycleError→MEDIUM, unknown→LOW | AC6 |
| TestLocalization | 2 | from summary, unknown fallback | AC7 |
| TestCorpusReport | 3 | empty, with records, dedup by signature | AC8 |
| TestHarness | 7 | id/version, run empty, add, dedup, completed→None, persist, runner | AC9 |
| TestCLI | 1 | exit 0 + JSON | AC10 |
| TestWiring | 1 | 11 harness in registry | AC11 |
| TestDeterminism | 1 | analyze twice → identical | AC12 |

## Results

- **32/32 PASS**
- **Full suite: 2286 PASS / 0 FAIL** (coverage 92.9%)
- **CLI**: `aiagent harness diagnose` → exit 0, empty corpus
- **arch-health**: 0 violations
- **5 registry tests updated** (added "diagnose" → 11 harness)
- **1 release wiring test updated** (10→11)
