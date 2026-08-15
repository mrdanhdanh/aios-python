# TASK-049 — Critique v2 (đầy đủ)

## Phản biện độc lập vòng 2
- **P1-01**: default checks phải đủ 6 nhóm PLAN (contract, behavior, security, permission, compatibility, performance) — behavior/performance là check_fn injectable placeholder có evidence "not_configured" nhưng không fail.
- **P1-02**: CERTIFIED + ENTERPRISE_CERTIFIED phải yêu cầu enterprise evidence (tenant isolation note / signing key) — dùng manifest.publisher/signature hiện diện.
- **P2-01**: report phải expose `level` sau certify, không phải trường tính riêng.
- **P2-02**: `certify()` không mutate manifest input.
## Resolution v2
- ✅ 6 nhóm default (2 injectable placeholder pass-with-note).
- ✅ enterprise evidence = publisher + signature tồn tại.
- ✅ level là field report.
- ✅ thuần, không mutate.
