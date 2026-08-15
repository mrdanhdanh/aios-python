# TASK-069 — Implementation

| Artifact | Nội dung |
|----------|----------|
| `backend/src/aios_core/observability/slo.py` | SloKind (RATIO/ABSOLUTE_ZERO) + SloDefinition (extra=forbid) + 12 SLO + SloEngine.check() (PASS/FAIL/SKIPPED) + metrics_from_runtime(kernel) + format_slo_report |
| `backend/src/aios_core/observability/metrics.py` | +`counts_by_outcome()` + workflow finish set ok (additive) |
| `backend/src/aios_core/workflow/cli.py` | +`aiagent slo` |
| `backend/tests/test_slo.py` | 12 tests |
