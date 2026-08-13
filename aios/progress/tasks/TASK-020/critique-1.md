# Critique ×1 — TASK-020 (critic subagent, vòng 1)

> 2026-08-13 | critic phản biện spec v1 — kết luận: NO, cần sửa spec.

## Vấn đề (5 P1 + 6 P2 + 4 P3) → Resolution

### P1
- **Hook protocol mâu thuẫn** (migrator không có rollback, backup thiếu nguồn payload) → **Resolve**: Migrator Protocol 4 method (read_current/migrate/rollback/write_current); payload từ read_current.
- **ComponentSpec undefined** → **Resolve**: dataclass frozen (kind, component_id, version, dependencies) + Dependency(name, version pin).
- **Event contract không khớp EventBus** (UPGRADE_COMPLETED đã có sẵn; sink string không nối bus) → **Resolve**: thêm 8 member uppercase vào EventType; tái sử dụng UPGRADE_COMPLETED; wiring wrapper EventType→Event→publish.
- **Allow-list sai** (kernel.bus không tồn tại; thiếu external) → **Resolve**: `aios_core.kernel.events` + external đầy đủ (sqlite3, pathlib, contextlib, json, dataclasses, typing, datetime, uuid, collections, logging).
- **Rollback mid-way không đặc tả** → **Resolve**: backup per-component (sau đó đơn giản hóa: chỉ root — xem critique-2), rollback reverse-topo, lỗi rollback best-effort ghi reason không raise.

### P2
- Skip check vị trí (AC8) → Resolve: sau STARTED, trước compatibility.
- Health check timing/semantics → Resolve: 1 lần sau migrate; read_current version verify + validate hook.
- Conflict mechanism/topo chuẩn → Resolve: pin cứng, DFS post-order sort (name, version).
- Exit code bảng → Resolve: success=0, skipped=0, dry-run ok=0, dry-run incompatible=1, fail=1.
- CLI vị trí → Resolve: workflow/cli.py lazy import (như _serve).
- 6 bước vs 7 events → Resolve: mapping chính xác, rollback là phản ứng.

### P3
- Double-rollback SkillManager → Resolve: ưu tiên migrator.rollback; write_current fallback.
- Lazy import AST → Resolve: ghi rõ allow-list internal/external.
- breaking flag → Resolve: ghi chú không test nhánh breaking-compatible.
- BackupStore db_path + pre-release policy → Resolve: tham số constructor + ghi chú semver rule 1.

## Trạng thái: RESOLVED 15/15 → spec v2
