# TASK-048 — Critique v1 + v2

## Critique v1
- **P1-01 Trust Model đủ 9 bước**: pipeline phải là danh sách rõ ràng, fail trả `step` tên.
- **P1-02 Signature**: HMAC-SHA256 với key publisher; verify fail → fail cứng.
- **P2-01 Security scan**: kiểm permissions khai báo — nếu chứa `*` hoặc rỗng mà permissions cần → fail cứng.
- **P2-02 Certification**: chạy `CertificationEngine` trên manifest; level < VERIFIED → warning; security fail → fail.
- **P3-01 Dependency**: check qua ecosystem registry (entry tồn tại) — injectable resolver.
## Resolution v1
- ✅ steps list + step attribute; ✅ HMAC; ✅ permission scan fail cứng; ✅ cert gate; ✅ resolver injectable.

## Critique v2
- **P1-01 Không God Object**: MarketplaceRegistry ≠ TrustChain ≠ signer — 3 class riêng.
- **P1-02 Deterministic**: sign cùng payload cùng key → cùng chữ ký (không timestamp).
- **P2-01 Registry**: packages unique (publisher_id, name); publish override với version mới.
- **P2-02 Install result**: trả InstallResult (approved bool, step, cert_level, manifest).
- **P3-01 Events**: sink best-effort `marketplace.installed`.
## Resolution v2
- ✅ 3 class; ✅ deterministic HMAC; ✅ unique + upsert; ✅ InstallResult; ✅ sink.
