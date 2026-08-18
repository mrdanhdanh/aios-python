# ADR-0007: Compatibility & Migration Policy — AIOS 1.1

- **Status**: accepted
- **Date**: 2026-08-16
- **Extends**: [ADR-0005](0005-branching-model.md) (branching model), [ADR-0006](0006-issue-pr-workflow.md) (issue-driven development) — quy định về **version / compatibility / migration** của hệ thống

## Context

AIOS đạt AIOS 1.0 CERTIFIED (M10, INV-001..034 frozen) và M11 (INV-035). M12 (Issue #7) nâng cấp hệ thống lên **AIOS 1.1 Compatibility**: bump version `0.1.0 → 1.1.0`, tạo Compatibility Matrix, migration 1.0→1.1 thật, backward compatibility suite, conformance area/gate mới. Cần một chính sách chính thức định nghĩa: version nghĩa là gì, component tương thích thế nào, nâng cấp an toàn ra sao — để mọi thành phần (runtime, CLI, plugin, workflow, SDK, conformance) nói chung một ngôn ngữ.

## Decision

### 1. Version policy (semver)

- AIOS dùng **semver** (`MAJOR.MINOR.PATCH`).
- `0.1.0` = dev version nội bộ (M0) — **lịch sử, KHÔNG thuộc đường nâng cấp** (`CompatibilityChecker` Rule 4 coi 0.x→1.x là breaking — đúng).
- `1.0.0` = mốc release M10 (AIOS 1.0 CERTIFIED).
- `1.1.0` = mốc M12 (AIOS 1.1 Compatibility) — version hiện tại (`aios_core.__version__`, `system status`, `/openapi.json`).
- **Đường nâng cấp chính thức: `1.0.0 → 1.1.0`** (minor bump = backward-compatible; `check_upgrade("1.0.0","1.1.0")` → compatible, không breaking).

### 2. Compatibility Matrix (`upgrade/compatibility.py`)

- Registry khai báo khoảng AIOS version hỗ trợ cho từng component: `(kind, id, version, aios_min, aios_max)` — kind ∈ {plugin, contract, workflow, skill, sdk}.
- `DEFAULT_ENTRIES` ≥ 14 entry (10 contract catalog + plugin + workflow + skill + sdk).
- **Fail-closed**: kind/id không có entry → error; version không parse được → error; aios_version ngoài `[aios_min, aios_max]` → error; version component lệch entry.version → **warning (không chặn)**.
- `aios_min` = semver thuần; `aios_max` = constraint (hỗ trợ `.x`, vd `1.1.x`); `None` = không chặn.
- CLI: `aiagent compat list` / `compat check <kind> <id> <version> [--aios-version]`.

### 3. Migration 1.0→1.1 (`upgrade/migration_110.py`)

- Plan chuẩn per component — `migration_id = aios-1.0-to-1.1-{kind}-{component_id}` → **idempotent per component** (apply lần 2 cùng component bị từ chối).
- Pipeline: matrix **pre-check** (range + entry) → **backup trước apply** (`BackupStore`) → `MigrationEngine.apply` (journal SQLite từng bước) → **post-check** (assertion per-kind + matrix) → fail → rollback.
- Rollback có guard: chỉ đảo khi giá trị hiện tại == giá trị do transform ghi.
- `config` **SKIP matrix** (không có version) — chỉ transform marker.
- CLI: `aiagent migrate <kind> 1.0.0 1.1.0 --dry-run|--apply [--input file.json] [--journal path]`.

### 4. Backward Compatibility Suite (`upgrade/backward_compat.py`)

- 9 check chéo cũ→mới (5 kind: workflow/plugin/contract/extension/migrated) — dữ liệu v0/v1 chạy được trên 1.1.
- **Fail-closed bắt `BaseException`** — 1 check fail → report không ok → CLI exit 1.
- CLI: `aiagent compat verify`.

### 5. Conformance & release gate

- `aiagent conformance`: **11 areas + 20 Golden Scenarios + 7 release gates (A–G)** — trong đó area `compatibility` (matrix + backward suite + version) và `gate_g_compatibility`.
- Kết quả: **"AIOS 1.1 READY"** khi tất cả areas + GS + gates pass.
- **`gate_g_compatibility` vi phạm = release blocker** (cùng hàng với Gate A–F).

### 6. Parse-only mở rộng

- Model được phép **mở rộng parse-only** (thêm field có default, không đổi hành vi check/validate hiện có).
- Precedent: `AiosRange.compatible` (TASK-086) — field `compatible: list[str]` do migration ghi; behavior `min`/`max` (`check_compatibility`) KHÔNG đổi.

## Consequences

- Mọi bump version tương lai phải: cập nhật `__version__` + contract catalog + matrix entries + verify suite + conformance — theo đúng chuỗi C1→C2→C3→C4.
- Người dùng nâng cấp 1.0→1.1 làm theo `docs/guides/migration-1.0-to-1.1.md`.
- Plugin manifest có thể chứa `aios.compatible` (danh sách version đã xác nhận) — được parse, không bắt buộc.
- Vi phạm fail-closed của matrix/verify/gate_g = không đạt conformance = không release.
