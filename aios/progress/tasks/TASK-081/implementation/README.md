# TASK-081 — Implementation artifacts

## Code (backend)

| File | Vai trò |
|------|---------|
| `backend/src/aios_core/rendering/asset.py` | R9: AssetSpec/AssetOutput/AssetCapability/AssetPipeline Protocol + AssetError + ASSET_KINDS (6 loại) |
| `backend/src/aios_core/rendering/registry.py` | R4: AssetCapabilityRegistry (thread-safe, discover/list/get, counters, produce fail-closed) + default_asset_capabilities() (đọc skills/*/manifest.json, map capabilities→kinds) + _SkillPipeline |
| `backend/src/aios_core/rendering/matcher.py` | R11: CreativeMatcher (scoring deterministic kind*10 + keyword*1 + prefix*3, match/suggest) |
| `backend/src/aios_core/rendering/__init__.py` | Export mới (ASSET_KINDS, AssetCapability, CreativeMatcher, ...) |
| `backend/src/aios_core/workflow/cli.py` | CLI `aiagent asset list/discover/match/produce` |
| `backend/tests/test_assets.py` | 15 tests (AC1–AC8 + manifest) |

## Skills (wire registry)

| File | Vai trò |
|------|---------|
| `skills/agent-sprite-forge/manifest.json` | Manifest skill thật — mang từ `operation/test-A` (tham khảo trực tiếp theo user duyệt) — registry đọc → capability kind=asset |
