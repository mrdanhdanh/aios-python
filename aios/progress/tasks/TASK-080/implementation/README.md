# TASK-080 — Implementation artifacts

## Code (backend)

| File | Vai trò |
|------|---------|
| `backend/src/aios_core/rendering/ui_state.py` | UIState contract (R10): canonical JSON + state_hash + diff reasoning |
| `backend/src/aios_core/rendering/evidence.py` | VisualEvidence (R1): 7 trường, screenshot base64 data URI, render_state required, PNG_1PX_BASE64 |
| `backend/src/aios_core/rendering/probe.py` | VisualRegressionProbe (R1): compare ref vs current → pixel/dom/state diff + outcome fail-closed (MISSING_EVIDENCE/NOT_EXECUTED/ERROR) |
| `backend/src/aios_core/observability/visual.py` | VisualMetrics: counters visual_probe_count/visual_fail_closed_violations + gauge visual_pixel_diff_max (idempotent singleton) |
| `backend/src/aios_core/workflow/cli.py` | CLI `aiagent visual-probe` (--dump-ref/--dump-current/--ref/--current/--threshold/--missing-ref) |
| `backend/tests/test_visual.py` | 16 tests (AC1–AC9 + JSON roundtrip) |
| `backend/tests/test_architecture.py` | +`threading` vào observability allow-list (TASK-080 comment) |
