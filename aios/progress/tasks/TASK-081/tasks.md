# TASK-081 — Tasks breakdown (checklist)

## Implement

- [ ] I1. `rendering/asset.py` — AssetSpec/AssetOutput/AssetCapability/AssetPipeline Protocol + AssetError
- [ ] I2. `rendering/registry.py` — AssetCapabilityRegistry (thread-safe Lock, discover/list/get, counters) + default_asset_capabilities() (khảo sát skills/)
- [ ] I3. `rendering/matcher.py` — CreativeMatcher (scoring deterministic kind*10 + keyword*1 + prefix*3, reason, suggest)
- [ ] I4. `rendering/__init__.py` export mới
- [ ] I5. CLI `aiagent asset list/discover/match/produce/--list-pipelines` + mock pipeline
- [ ] I6. Tests `tests/test_assets.py` (AC1–AC10) + arch allow-list mở rộng

## Test

- [ ] T1. Contracts AssetSpec/Output (AC1)
- [ ] T2. Pipeline produce + raise → AssetError (AC2)
- [ ] T3. Registry discover/list/get (AC3, AC4)
- [ ] T4. Matcher match/suggest (AC5, AC6)
- [ ] T5. Default capabilities từ skills/ (AC7)
- [ ] T6. Produce idempotency fail-closed (AC8)
- [ ] T7. CLI thật (AC9)
- [ ] T8. Full suite (AC10) + arch test

## Evaluate

- [ ] E1. Đối chiếu 10 AC
- [ ] E2. Health check phase P3 (doctor + arch-health + conformance)
- [ ] E3. LOG.md + PROGRESS.md + commit
