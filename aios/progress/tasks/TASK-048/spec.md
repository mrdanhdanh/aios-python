# TASK-048 — Marketplace (M8-E6)

## Mục tiêu
Phân phối tuân Trust Model: `Download → Manifest validation → Signature verification → Dependency check → Permission analysis → Compatibility check → Security scan → Harness certification → Install`. Publisher có `id + signing_key`; package có signature (deterministic HMAC-SHA256 — không crypto phức tạp, đủ trust chain v1).

## Phạm vi
- `ecosystem/marketplace.py`: `Publisher`, `PackageRecord` (publisher, name, version, manifest, signature), `TrustChain` (pipeline 9 bước deterministic), `MarketplaceRegistry` (SQLite, register_publisher, publish, install_flow).
- Signature: `sign(manifest_json, key)` → HMAC hex; `verify` lại.
- Install flow: verify từng bước → fail → `MarketplaceError` kèm bước lỗi.

## Input/Output
- Input: publisher registration, package (manifest + signature).
- Output: verified package → installable (trả manifest + cert level), errors có step.

## Tiêu chí chấp nhận
1. Publisher register + sign + verify đúng.
2. TrustChain chạy đủ 9 bước; fail bước nào → error rõ bước đó.
3. Signature sai → fail ở bước signature.
4. Manifest invalid (extra/thiếu id) → fail manifest validation.
5. Dependency missing trong registry → fail dependency.
6. Certification level < CERTIFIED → warning (không fail, policy quyết định) — nhưng security scan fail → fail cứng.
7. Compatibility (aios range) sai → fail.
8. MarketplaceRegistry persist publisher + packages.
9. Import allow-list ecosystem (thêm hashlib/hmac).
10. Test: sign/verify, pipeline steps, fail từng bước, persist.
