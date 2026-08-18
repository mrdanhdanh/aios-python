# TASK-094 — Evaluation

> Date: 2026-08-18 | Task: M14-P0 Detect & Diagnose

## AC Checklist

| # | AC | Result | Evidence |
|---|-----|--------|----------|
| AC1 | FailureRecord shape + extra="forbid" | ✅ | TestContracts |
| AC2 | FailureSignature deterministic | ✅ | TestSignature |
| AC3 | normalize_message strips timestamps/uuids/paths/hex | ✅ | TestNormalize |
| AC4 | analyze(FAILED) → FailureRecord | ✅ | TestAnalyze |
| AC5 | analyze(COMPLETED) → None | ✅ | TestAnalyze |
| AC6 | Severity mapping (all error subclasses) | ✅ | TestSeverity |
| AC7 | Component localization | ✅ | TestLocalization |
| AC8 | FailureCorpusReport shape + dedup | ✅ | TestCorpusReport |
| AC9 | Harness id="diagnose" + persist | ✅ | TestHarness |
| AC10 | CLI exit 0 + JSON | ✅ | TestCLI |
| AC11 | Full suite + arch-health + doctor | ✅ | 2286 PASS |
| AC12 | Determinism | ✅ | TestDeterminism |

**12/12 AC achieved.**

## Lessons

1. `_extract_error` must strip status prefix ("FAILED: ") before checking for error class name — otherwise "FAILED:" is mistaken for the error type.
2. Failure corpus dedup by signature prevents duplicate entries from repeated runs with same error.
3. Lightweight evidence (subset only) keeps corpus memory usage manageable.
