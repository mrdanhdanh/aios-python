# TASK-046 — Ecosystem Registry (M8-E4)

## Mục tiêu
Registry v2 lưu đủ metadata cho mọi thành phần hệ sinh thái (Agents, Capabilities, Tools, Skills, Workflows, Models, Providers, Plugins, Integrations, Extensions) + discovery qua tìm kiếm (`aios search github`). MCP là adapter — không phải abstraction chính.

## Phạm vi
- `ecosystem/contracts.py`: `EntryKind` (10 loại), `Publisher`, `EcosystemEntry` (identity, metadata, contract, permissions, dependencies, compatibility, security, capabilities, artifacts, publisher, signature — extra=forbid).
- `ecosystem/registry.py`: `EcosystemRegistry` — SQLite persist, index_entry/update/remove, search(keyword, kind=None, namespace=None), get by (kind,id), count.
- Discovery pipeline note: System Knowledge → Ecosystem Registry → Capability Discovery → Plugin (chỉ ghi chú trong docstring).

## Input/Output
- Input: entry dict/`EcosystemEntry`; query keyword.
- Output: `EcosystemEntry` records, search results list.

## Tiêu chí chấp nhận
1. Entry 10 kinds, extra=forbid.
2. registry index/update/remove + persist qua restart.
3. search theo keyword (id/name/description) + filter kind.
4. search trả sorted deterministic.
5. Duplicate (kind,id) → update, không lỗi.
6. Import allow-list: ecosystem/ chỉ pydantic/stdlib + semver + metadata.
7. CLI `aiagent ecosystem search <query>`.
8. Test: index/search/filter/persist/update/remove.
