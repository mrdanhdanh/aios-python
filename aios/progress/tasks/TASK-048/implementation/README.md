# TASK-048 — M8-E6 Marketplace / Distribution — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `ecosystem/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/ecosystem/marketplace.py` — `MarketplaceRegistry` (publisher + packages persist) + `TrustChain` 9 bước (Download → Manifest validation → Signature verification → Dependency check → Permission analysis → Compatibility check → Security scan → Harness certification → Install) + HMAC canonical
- `backend/src/aios_core/ecosystem/contracts.py` — `Publisher` (id + signing_key — KHÔNG serialize raw key, chỉ fingerprint)
- `backend/src/aios_core/ecosystem/errors.py`
- `backend/src/aios_core/workflow/cli.py` — CLI `marketplace publish`

## Key behavior
- Trust Model: mỗi package có `publisher { id, signing_key }`; AIOS biết Publisher/Package/Version/Signature/Certification
- Fail bước nào → error rõ bước đó; signature sai → fail ở bước signature
- Certification level < CERTIFIED → warning (policy quyết định); security scan fail → fail cứng
- Compatibility (aios range) sai → fail

## Verification
- `pytest` full suite: **1639 passed** — xem `test.md` + `tests/test_ecosystem_marketplace.py`
