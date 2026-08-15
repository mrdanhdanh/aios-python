# TASK-048 — Implementation checklist

- [x] Spec + critique ×2 resolve.
- [x] Review pre-implement.
- [ ] `ecosystem/marketplace.py` (Publisher, signer, TrustChain 9 bước, MarketplaceRegistry SQLite, InstallResult).
- [ ] CLI `aiagent marketplace publish <file>` (install tối thiểu).
- [ ] `tests/test_ecosystem_marketplace.py`.
- [ ] Regression + progress + commit.

# Review pre-implement
**APPROVED có điều kiện**: 3 class tách, canonical JSON sign, key không serialize, injectable resolver, InstallResult luôn trả, CLI tối thiểu.
