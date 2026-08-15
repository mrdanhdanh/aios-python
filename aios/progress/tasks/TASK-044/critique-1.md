# TASK-044 — Critique v1

## Phản biện
- **P1-01 Reuse thật sự**: nếu chỉ copy 10-state mà không dùng chung `assert_transition` thì vẫn là "hệ thống lifecycle thứ hai". Bắt buộc import `SkillState` + `assert_transition` từ `skills.base`.
- **P1-02 Compat range**: `min`/`max` phải parse an toàn (`2.x` → major 2; `*` → any; semver đầy đủ); range invalid phải fail-fast ở resolve, không chờ install.
- **P2-01 Provides đúng state**: provides index phải loại bỏ plugin bị disable/unload/remove — chỉ plugin active (enabled/reloaded) xuất hiện trong `provides()`.
- **P2-02 Dependency remove**: remove plugin có dependent phải chặn (mirror R1 skills) — kể cả dependent đang disabled.
- **P2-03 Upgrade history**: rollback phải phục hồi đúng manifest cũ (không chỉ version string).
- **P3-01 Events**: mọi transition phát event `plugin.<op>`; event_sink best-effort.
- **P3-02 Optimistic**: mutation phải `UPDATE ... WHERE state=old` và raise khi rowcount=0.

## Resolution
- ✅ `plugins.base` alias `PluginState = SkillState` và dùng `assert_transition` trực tiếp từ `skills.base`; không định nghĩa bảng transitions mới.
- ✅ `compat.py` parse range fail-fast (ValueError → PluginCompatibilityError ở resolve).
- ✅ provides index tính từ trạng thái active; rebuild từ DB khi khởi tạo.
- ✅ dependent check trong remove/rollback quét toàn bộ plugins còn non-REMOVED.
- ✅ upgrade push full manifest+version vào history; rollback pop và ghi đè.
- ✅ event_sink gọi sau mỗi transition thành công.
- ✅ `_transition()` dùng `UPDATE ... WHERE state=?` + rowcount check.
