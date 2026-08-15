# TASK-037 — Critique v1

## Vấn đề
- **P1-01**: `check_isolation` semantics: empty `tenant_classes` = unrestricted (serve all). Test cũ dùng node với non-empty để verify deny.
- **P2-01**: router phải stable sort để deterministic (fallback id).

## Resolution
- ✅ empty = all; test dùng node `["secure"]` deny `"enterprise"`.
- ✅ sort by (health, tenant_class_match, region, capability, capacity, cost, id).
