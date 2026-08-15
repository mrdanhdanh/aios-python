# TASK-044 — Plugin Runtime (M8-E2)

## Mục tiêu
Plugin Runtime với lifecycle **tái sử dụng đúng 10-state machine của Skills Manager** (M2/M4) — không xây state machine thứ hai. Plugin khai báo manifest (id, version, aios range, provides, permissions, dependencies) và được quản lý qua SQLite + optimistic concurrency, tuân INV-030-style boundary: plugin KHÔNG import kernel/services/registry/db/filesystem/network.

## Phạm vi
- Package `backend/src/aios_core/plugins/`: contracts, compat, errors, manager, registry, schema, `__init__`.
- `PluginState = SkillState` (alias từ `skills.base`) + `assert_transition` dùng chung — DISCOVERED/LOADED/RUNNING chỉ là runtime_status quan sát, không phải state machine cạnh tranh.
- PluginManager: resolve → validate → install → enable → disable → unload → reload → upgrade → rollback → remove.
- Compat check AIOS range (`min`/`max`, hỗ trợ `2.x`, `*`).
- Dependency plugin check (dependent chặn remove/rollback).
- Provides index (kind → plugin ids) cập nhật theo lifecycle.
- Config `PluginSettings` + wiring `regs["plugins"]` / `regs["plugin_registry"]`.
- Ngoài phạm vi: marketplace, signing, CLI scaffold, plugin code execution thật.

## Input/Output
- Input: manifest dict từ plugin (yaml/dict), aios version hiện tại, dependency plugin records.
- Output: Plugin read model (id, name, version, type, state, manifest, history, timestamps), events `plugin.*`, provides map.
- Persistence: SQLite bảng `plugins`.

## Tiêu chí chấp nhận
1. Plugin lifecycle dùng chung `SkillState` + `assert_transition` từ `skills.base` (không định nghĩa state machine mới).
2. resolve + validate kiểm aios range (min/max, `2.x`, `*`); sai range → `PluginCompatibilityError`.
3. validate/install kiểm dependency plugin (đã resolve, không REMOVED, version ≥ constraint).
4. upgrade yêu cầu version mới > hiện tại; rollback khôi phục manifest/version cũ (history stack).
5. remove/rollback chặn khi còn plugin phụ thuộc (dependent check).
6. provides index (kind → ids) đúng theo trạng thái; `PluginRegistry.provides(kind)` trả plugin active.
7. Mọi mutation optimistic concurrency (`UPDATE ... WHERE state=old`), events `plugin.*`.
8. plugins/ không import kernel/services/orchestrator/models/memory/knowledge/tools/agents/capabilities/workflow/harness — enforce bằng architecture test allow-list.
9. Config `PluginSettings` (enabled, db_path, strict) + `config.yaml` + wiring.
10. Test phủ: lifecycle 10 trạng thái, compat range, dependency, provides, concurrency, registry, events.
