# TASK-048 — Test + Evaluation

## Test
`tests/test_ecosystem_marketplace.py` (12 tests): signature deterministic + tamper detect, trust chain full pass (qua registry install_flow), fail từng bước (signature/manifest/dependency/compat/security/no-permission), publisher key không serialize (raw bytes check), install package missing, publish upsert, short key rejected.

## Evaluation
Đạt 10/10 AC. Trust Model 9 bước đúng PLAN; HMAC-SHA256 canonical JSON (sort_keys); raw key không bao giờ persist (chỉ fingerprint); offline-first dependency (default resolver local-satisfied, injectable để enforce); InstallResult luôn trả kèm step. Fix: pydantic không nhận positional args; `compare()` thay vì `VersionInfo` so sánh trực tiếp.
**TASK-048 DONE**
