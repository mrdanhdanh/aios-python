# TASK-044 — Critique v2

## Phản biện độc lập (vòng 2)
- **P1-01 Boundary import**: plugins/ chỉ được import `skills.base`, `skills.errors`, `semver`, `metadata` (aios) — KHÔNG chạm `kernel/services/*`, `tools`, `capabilities`, `agents`, `workflow`, `harness`, `enterprise`, `memory`, `knowledge`, `models`, `orchestrator`. Test allow-list phải chứng minh điều này.
- **P1-02 Strict flag**: `PluginSettings.strict=True` mặc định — resolve/validate lỗi phải raise; chỉ khi strict=False mới trả về kết quả lỗi thay vì raise (nhất quán harness convention).
- **P2-01 Tên bảng cột**: `plugins` table phải có đủ state/history/manifest/installed_at để registry và rollback hoạt động không cần đọc lại manifest dict lạ.
- **P2-02 Dep constraint**: dependency của plugin phải hỗ trợ `id` hoặc `id@>=X.Y.Z` giống skills; parse lỗi → PluginDependencyError.
- **P2-03 resolve idempotent**: resolve plugin đã tồn tại (cùng id) → PluginError "already exists" (không ghi đè).
- **P3-01 Registry list_by_kind**: registry phải có `list_by_kind(kind)` và `provides(kind)` phân biệt rõ.
- **P3-02 PluginType**: enum đủ 9 loại PLAN (agent, capability, tool, skill, workflow, model_provider, memory, ui, integration).

## Resolution
- ✅ Allow-list cứng trong `test_architecture.py` (`_PLUGINS_ALLOWED_AIOS`).
- ✅ `strict` flag trong manager (mặc định True); lỗi validate khi strict=False → trả về Plugin kèm lỗi field.
- ✅ schema đủ cột: id, name, version, type, state, manifest_json, history_json, installed_at, created_at, updated_at.
- ✅ `_parse_dependency` chung với skills semantics (`id` / `id@>=X.Y.Z`).
- ✅ resolve INSERT + IntegrityError → PluginError already exists.
- ✅ registry: `get/list/list_by_state/list_by_kind/provides`.
- ✅ `PluginType` 9 giá trị đúng PLAN.
