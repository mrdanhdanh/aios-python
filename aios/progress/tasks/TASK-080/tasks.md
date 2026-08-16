# TASK-080 — Tasks breakdown (checklist)

## Implement

- [ ] I1. `rendering/ui_state.py` — UIState contract (version 1.0, canonical JSON sort_keys, state_hash)
- [ ] I2. `rendering/evidence.py` — VisualEvidence (7+2 trường, screenshot base64, render_state required)
- [ ] I3. `rendering/probe.py` — VisualRegressionProbe (compare ref vs current: pixel diff theo threshold, dom diff path, state diff; outcome mapping MISSING_EVIDENCE/NOT_EXECUTED/ERROR — INV-035)
- [ ] I4. Observability: register visual metrics (counters + gauge, idempotent, lazy)
- [ ] I5. CLI `aiagent visual-probe` (--dump-ref/--dump-current/--ref/--current/--threshold/--missing-ref) + mock evidence
- [ ] I6. Tests `tests/test_visual.py` (AC1–AC9) + arch allow-list

## Test

- [ ] T1. UIState canonical + hash (AC1, AC2)
- [ ] T2. VisualEvidence fields (AC3)
- [ ] T3. Probe compare giống/khác state (AC4, AC5)
- [ ] T4. Probe missing ref → MISSING_EVIDENCE (AC6) + pixel diff > 0 → FAIL kèm evidence (AC7)
- [ ] T5. Observability metrics (AC8)
- [ ] T6. CLI thật (AC9)
- [ ] T7. Full suite (AC10) + arch test

## Evaluate

- [ ] E1. Đối chiếu 10 AC
- [ ] E2. Health check phase P2 (doctor + arch-health + conformance)
- [ ] E3. LOG.md + PROGRESS.md + commit
