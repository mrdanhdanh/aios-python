# TASK-082 — Implementation

> Code thật nằm ở backend/ (xem bảng dưới). Task này implement M11-P3b/c/d:
> R6 Creative Domain + R8 Vendor Integrity + R12 Reference-Asset.

| Module | File | Nội dung |
|--------|------|----------|
| R6 | `backend/src/aios_core/orchestrator/workflow_matcher.py` | Creative pre-route (bước 0) + `CREATIVE_TRIGGERS` + `CREATIVE_CONFIDENCE`; `creative_matcher=None` → hành vi cũ |
| R6 | `backend/src/aios_core/rendering/workflows.py` | 2 workflow creative (`creative/game_scaffold`, `creative/sprite_generate`) + `register_creative_workflows()` |
| R8 | `backend/src/aios_core/config.py` + `config.yaml` | `SecuritySettings.vendor_bundles` (path → pinned sha256) |
| R8 | `backend/src/aios_core/security/checks.py` | Check thứ 12 `vendor_integrity` (SHA256 byte-identical, fail-closed INV-035) |
| R12 | `backend/src/aios_core/rendering/reference.py` | `ReferenceDescription` + `MockVisionAnalyzer` (seed sha256) + `ReferenceAssetUnderstanding` (fail-closed) |
| R12 | `backend/src/aios_core/workflow/cli.py` | `aiagent reference describe <image>` |
| Test | `backend/tests/test_m11_p3bcd.py` | 16 tests (R6/R8/R12) |
| Test | `backend/tests/test_security.py` | Fix 11 → 12 items (R8) |
