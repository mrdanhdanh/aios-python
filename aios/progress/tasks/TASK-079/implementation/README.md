# TASK-079 — Implementation artifacts

## Code (backend)

| File | Vai trò |
|------|---------|
| `backend/src/aios_core/rendering/__init__.py` | Package Rendering facade |
| `backend/src/aios_core/rendering/contracts.py` | InputEvent, RenderFrame, RenderFn (raw W×H×3), RenderReplayResult |
| `backend/src/aios_core/rendering/prng.py` | SeededPrng mulberry32 (thuần, KNOWN_VECTOR test) |
| `backend/src/aios_core/rendering/timeline.py` | RenderTimeline (record ordered + state_hash deterministic) |
| `backend/src/aios_core/rendering/replay.py` | RenderReplay (freeze_policy none/fixed/paused + pixel_hash SHA256) |
| `backend/src/aios_core/rendering/harness.py` | DeterministicHarness (2 replay → stable/diff + VerificationOutcome INV-035) |
| `backend/src/aios_core/rendering/idempotency.py` | AssetIdempotencyClassifier (exactly/at-least/at-most-once, fail-closed) |
| `backend/src/aios_core/workflow/cli.py` | CLI `aiagent render-replay` (--seed/--frames/--width/--height/--freeze/--show-hashes) |
| `backend/tests/test_rendering.py` | 18 tests (AC1–AC8 + arch allow-list) |
