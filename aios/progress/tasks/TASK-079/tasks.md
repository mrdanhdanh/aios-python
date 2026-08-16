# TASK-079 — Tasks breakdown (checklist)

## Implement

- [ ] I1. `rendering/__init__.py` + `contracts.py` (InputEvent, RenderFrame, RenderReplayResult — pydantic extra=forbid; RenderFn = Callable[[RenderFrame], bytes])
- [ ] I2. `prng.py` — SeededPrng mulberry32 (thuần, test vector cố định)
- [ ] I3. `timeline.py` — RenderTimeline (record ordered + timestamp tăng)
- [ ] I4. `replay.py` — RenderReplay (record → replay(render_fn, seed) → frames + pixel_hash SHA256)
- [ ] I5. `harness.py` — DeterministicHarness (config seed/fps/max_frames/freeze_policy/width/height; run() 2 replay → RenderReplayResult + diff_frames + VerificationOutcome INV-035; render_fn raise → BLOCKED)
- [ ] I6. `idempotency.py` — AssetIdempotencyClassifier (exactly-once/at-least-once/at-most-once; fail-closed không khai báo = at-most-once; retry/approve/compensate)
- [ ] I7. CLI `aiagent render-replay` (--seed/--frames/--width/--height/--show-hashes) + mock render_fn trong CLI
- [ ] I8. Test: `tests/test_rendering.py` (AC1–AC9) + 1 arch test import allow-list (C3-02)

## Test

- [ ] T1. Contracts + timeline (AC1, AC2)
- [ ] T2. Replay deterministic (AC3, AC4)
- [ ] T3. PRNG seed (AC5)
- [ ] T4. Harness stable/unstable + BLOCKED (AC6, AC7)
- [ ] T5. Idempotency classifier (AC8)
- [ ] T6. CLI thật (AC9)
- [ ] T7. Full suite (AC10) + arch test

## Evaluate

- [ ] E1. Đối chiếu 10 AC
- [ ] E2. Health check phase P1 (doctor + arch-health + conformance)
- [ ] E3. LOG.md + PROGRESS.md + commit
