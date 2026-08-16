# TASK-081 — Test (M11-P3: R9 AssetPipeline + R4 Registry + R11 Matcher)

> Ngày: 2026-08-16 | Nhánh: feature/ISSUE-4-m11-deterministic-runtime

## Unit tests

| Suite | Kết quả | Ghi chú |
|-------|---------|---------|
| `tests/test_assets.py` (15 tests) | ✅ **15/15 PASS** | AC1–AC8 + manifest roundtrip |
| `tests/test_rendering.py` (regression) | ✅ PASS | 18/18 |

## CLI thật (AC9)

| Lệnh | Kết quả |
|------|---------|
| `aiagent asset list` | 1 capability: `agent-sprite-forge` (kinds=['map','sprite'], source=skills/agent-sprite-forge/) — **wire từ manifest skill thật (operation/test-A)** |
| `aiagent asset match "generate sprite pixel art"` | 1 result — score 14 (`kind:sprite; keyword:generate/sprite/pixel/art`) — R11 deterministic offline |
| `aiagent asset produce agent-sprite-forge --kind sprite --name cat --seed 7` | `produced: skill://agent-sprite-forge/sprite/cat` sha256=14f8fcd0… idempotency=at_least_once |
| `aiagent asset produce ... --kind audio` | `produce FAILED: skill không hỗ trợ kind=audio` — fail-closed, exit=1 |

## Full suite

- [x] **2018 passed / 0 failed** (64s) — baseline 2003 + 15 mới; không regression (AC10)

## Bugs phát hiện & fix trong quá trình implement

1. `model_dump_json(sort_keys=...)` — pydantic v2 không hỗ trợ sort_keys trong model_dump_json/model_dump → dùng `json.dumps(model_dump(mode="json"), sort_keys=True)`
2. `default_asset_capabilities()` sai parents index (`parents[5]` = Desktop thay vì `parents[4]` = repo root) — registry không đọc được skills/
3. `_SkillPipeline` đọc `manifest["kinds"]` nhưng manifest skill thật chỉ có `capabilities` → luôn raise; fix map capabilities→kinds (sprite-generation→sprite, map-generation→map)
