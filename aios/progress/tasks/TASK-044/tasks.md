# TASK-044 — Implementation checklist

- [x] Chốt phạm vi Plugin Runtime + reuse 10-state skills.
- [x] Spec + critique v1 resolve.
- [x] Critique v2 resolve độc lập.
- [x] Review trước implement.
- [x] Implement `plugins/contracts.py` (PluginManifest, PluginType, Plugin, PluginState alias).
- [x] Implement `plugins/errors.py`.
- [x] Implement `plugins/compat.py` (aios range parse/check).
- [x] Implement `plugins/schema.py`.
- [x] Implement `plugins/manager.py` (lifecycle + concurrency + provides + deps).
- [x] Implement `plugins/registry.py` + `plugins/__init__.py`.
- [x] Config `PluginSettings` + `config.yaml` + wiring.
- [x] Test `tests/test_plugins.py` + arch allow-list test.
- [x] Chạy full backend regression + cập nhật progress + commit.
