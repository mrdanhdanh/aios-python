# TASK-040 — Critique v1

## Vấn đề
- **P1-01**: `_assert_scope` phải check tenant → project → capability → scopes đúng thứ tự.
- **P2-01**: `require_sandbox` chỉ enforce với untrusted (trusted = system/agent verified).

## Resolution
- ✅ scope check thứ tự; mismatch → CredentialError.
- ✅ trusted principal bypass sandbox (documented).
