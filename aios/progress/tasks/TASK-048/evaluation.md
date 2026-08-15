# TASK-048 — Evaluation

> Bổ sung hồi tố 2026-08-15 khi đóng hard gate (evaluation ban đầu ghi trong LOG.md).

## Đối chiếu acceptance criteria
1. **Đạt** — Publisher register + sign + verify đúng.
2. **Đạt** — TrustChain chạy đủ 9 bước; fail bước nào → error rõ bước đó.
3. **Đạt** — Signature sai → fail ở bước signature.
4. **Đạt** — Manifest invalid (extra/thiếu id) → fail manifest validation.
5. **Đạt** — Dependency missing trong registry → fail dependency.
6. **Đạt** — Certification level < CERTIFIED → warning (policy quyết định); security scan fail → fail cứng.
7. **Đạt** — Compatibility (aios range) sai → fail.
8. **Đạt** — MarketplaceRegistry persist publisher + packages.
9. **Đạt** — Import allow-list ecosystem (thêm hashlib/hmac).
10. **Đạt** — Test sign/verify, pipeline steps, fail từng bước, persist (`tests/test_ecosystem_marketplace.py`).

## Kết luận
TASK-048 đạt phạm vi Marketplace (E6): trust chain 9 bước + HMAC + fingerprint signing key, phân phối package an toàn — Marketplace là consumer của Ecosystem infrastructure, không phải source of truth.
