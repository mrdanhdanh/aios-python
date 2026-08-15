# TASK-044 — Pre-implementation review

## Kết luận
**APPROVED có điều kiện** — implement Plugin Runtime.

## Kiểm tra
- Lifecycle tái dùng `SkillState` + `assert_transition` từ `skills.base` (không state machine thứ hai) ✅
- Compat range fail-fast tại resolve ✅
- Provides index chỉ chứa plugin active ✅
- Dependent check trên remove/rollback ✅
- Import allow-list cứng (không kernel/services/registries) ✅
- Config + wiring theo convention M7/M6 ✅

## Điều kiện bắt buộc khi implement
1. plugins/ chỉ import `skills.base`, `skills.errors`, `semver`, `metadata` + pydantic/stdlib.
2. `strict` mặc định True; raise fail-fast.
3. Upgrade/rollback thao tác full manifest (history stack), không chỉ version.
4. Chạy `tests/test_plugins.py` + toàn bộ backend pytest trước khi đánh dấu done.
