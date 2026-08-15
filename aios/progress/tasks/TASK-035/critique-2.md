# TASK-035 — Critique v2 (tự phản biện)

## Vấn đề phát hiện
- **P1-01**: identity phải là entry point của mọi execution — `EnterpriseManager.require_principal` đã wrap.
- **P2-01**: capability attenuation cần test case rõ: user cấp scope `git.read:repo` → agent chỉ được quyền đó.
- **P3-01**: docstring INV-022 chưa link rõ vào `require`.

## Resolution
- ✅ `EnterpriseManager.require_principal` delegate tới `IdentityEngine.require`.
- ✅ thêm test attenuation: scopes giới hạn permission set.
- ✅ docstring cập nhật reference INV-022.
