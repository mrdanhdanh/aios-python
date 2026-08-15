# TASK-044 — Evaluation

## Đối chiếu acceptance criteria

1. **Đạt** — `PluginState = SkillState` + `assert_transition` từ `skills.base`; không state machine thứ hai (arch test literal).
2. **Đạt** — `compat.py` parse `*`/`2.x`/semver fail-fast; resolve + validate check aios range → `PluginCompatibilityError`.
3. **Đạt** — dependency check: missing → `PluginDependencyError`, REMOVED → reject, chưa install → reject, version < constraint → reject.
4. **Đạt** — upgrade yêu cầu version mới > hiện tại; rollback phục hồi full manifest (history stack chứa manifest dict).
5. **Đạt** — remove/rollback chặn khi còn dependent (kể cả dependent disabled).
6. **Đạt** — provides index chỉ chứa ENABLED/RELOADED; rebuild từ DB khi restart; `PluginRegistry.provides(kind)`.
7. **Đạt** — `UPDATE ... WHERE state=old` + rowcount check (test stale view); events `plugin.resolved/installed/updated/removed` → EventBus (4 EventType mới).
8. **Đạt** — 4 arch tests: import allow-list (chỉ skills.base/errors + semver + metadata), reuse machine, compat fail-fast, provides active-only.
9. **Đạt** — `PluginSettings` (enabled/db_path/strict) + `config.yaml` + wiring `regs["plugins"]` + `regs["plugin_registry"]`.
10. **Đạt** — 20 plugin tests + full regression 1584 (chỉ 1 flaky timing có sẵn).

## Kết luận
**TASK-044 DONE** — Plugin Runtime đạt đủ 10/10 AC. Plugin là record passive (không chạm Runtime/Registry/DB trực tiếp), lifecycle dùng chung 10-state với Skills, compat + dependency fail-fast, provides index deterministic. Nền tốt cho TASK-045 Extension Contracts và TASK-046 Ecosystem Registry.

## Bài học
- Range semantics của max `2.x` là upper bound (`< 3.0.0`), không phải literal match — cần test boundary ngay từ đầu.
- `SkillStateError` từ skills phải được map sang `PluginStateError` ở biên plugin để người dùng plugin không thấy lỗi internal.
- Test concurrency nên dùng stale view (override `_get_row`) thay vì sửa DB trực tiếp — UPDATE trong cùng connection luôn khớp state.
