# TASK-020 — M4-P7: Upgrade Pipeline (Compatibility → Dependencies → Backup → Migration → Health Check → Rollback)

**Metadata**: TASK-020 | M4/P7 | 2026-08-13 | v4 (sau review — 1 R1 + 3 R2 resolved) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/upgrade/` (control plane)

## 1. Mục tiêu
Triển khai P7 theo PLAN.md: "Upgrade pipeline: Compatibility Check (contract version) → Dependency Resolution → Backup → Migration → Health Check → Rollback if failed". Nâng cấp component theo 6 bước có kiểm soát, deterministic (INV-010), rollback an toàn, event cho từng bước (INV-009).

## 2. Phạm vi
**In**: `backend/src/aios_core/upgrade/` (pipeline.py, dependency.py, backup.py, migrator.py, errors.py) + `kernel/events.py` (thêm EventType members) + `workflow/cli.py` (subcommand `upgrade`, lazy import) + `tests/test_architecture.py` (allow-list).
**Out**: không đổi behavior module cũ; không auto nâng cấp pip; không migration dữ liệu cross-version DB AIOS.

## 3. Kiến trúc

```
upgrade/
├── __init__.py
├── pipeline.py      # UpgradePipeline.run() — 6 bước + event + rollback
├── dependency.py    # ComponentSpec, Dependency, DependencyResolver, Resolution
├── backup.py        # BackupStore (SQLite) + BackupRecord
└── migrator.py      # Migrator Protocol + DictMigrator
```

### 3.1 dependency.py
```python
@dataclass(frozen=True)
class Dependency:
    name: str          # component_id
    version: str       # version PIN (deterministic — không range)

@dataclass(frozen=True)
class ComponentSpec:
    kind: str          # skill | workflow | prompt | capability | contract
    component_id: str
    version: str       # version HIỆN TẠI của component
    dependencies: tuple[Dependency, ...] = ()

@dataclass(frozen=True)
class Resolution:
    ok: bool
    ordered: tuple[ComponentSpec, ...]   # topo order: dependencies trước
    reason: str | None
```
- Hook `lookup(kind, component_id) -> ComponentSpec | None` (DI; test dùng dict).
- DFS post-order từ root, children sort (name, version) — deterministic.
- **missing** (lookup None) → fail kèm tên dep; **cycle** → fail kèm path; **conflict** (2 dep cùng name khác version) → fail.

### 3.2 backup.py
- SQLite `backups(id INTEGER PK AUTOINCREMENT, kind TEXT, component_id TEXT, version TEXT, payload TEXT, created_at TEXT)` — pattern chuẩn (`with closing(...) as conn, conn:`, `PRAGMA busy_timeout=5000`, `db_path.parent.mkdir`).
- `BackupRecord(id, kind, component_id, version, created_at)` dataclass.
- API: `backup(kind, component_id, version, payload: dict) -> int`; `restore(backup_id) -> dict`; `list(kind=None, component_id=None) -> list[BackupRecord]`.
- `db_path` tham số constructor.

### 3.3 migrator.py
```python
class Migrator(Protocol):
    def read_current(self, kind: str, component_id: str) -> dict | None: ...
    def migrate(self, kind: str, component_id: str, new_version: str) -> None: ...
    def rollback(self, kind: str, component_id: str) -> None: ...
    def write_current(self, kind: str, component_id: str, payload: dict) -> None: ...
```
- `DictMigrator(store: dict[str, dict])`: read_current/migrate/write_current hoạt động; **rollback = raise NotImplementedError** (pipeline fallback write_current).
- `SkillMigrator(skill_manager)`: read_current = `get(id)` (`None` → trả None) → `skill.model_dump(mode="json")` (Skill là BaseModel — C2-05 fixed); migrate = `upgrade(id, new_version)` — catch `SkillError`/`SkillStateError` (import `..skills.errors` — R1-1) → raise `UpgradeError` với message rõ; rollback = `rollback(id)` (cùng map lỗi); write_current = NotImplementedError.
- `errors.py`: `class UpgradeError(Exception)` — exception duy nhất của module upgrade.
- **Rollback quy ước**: pipeline thử `migrator.rollback(kind, id)`; `NotImplementedError` → `write_current(kind, id, backup_payload)`. Không gọi cả hai.

### 3.4 pipeline.py
```python
UpgradePipeline(migrator, backup_store, resolver,
                checker=CompatibilityChecker,
                validate: Callable[[str, str, str], str | None] | None = None,  # (kind, id, new_version) -> None|reason
                emit: Callable[[str, dict], None] | None = None)

@dataclass(frozen=True)
class UpgradeResult:
    status: str                     # ok | skipped | failed
    step: str | None                # compatibility | dependencies | backup | migrate | health
    backup_id: int | None
    reason: str | None
    plan: tuple[ComponentSpec, ...]  # topo order (resolution.ordered) — CLI in kế hoạch

run(kind, component_id, new_version, dry_run: bool = False) -> UpgradeResult
```

**QUYẾT ĐỊNH (C2-03 resolved): chỉ migrate ROOT component.** Dependency chỉ được resolve + kiểm tra tồn tại/không conflict (bước 2). Không bao giờ migrate dependency — tránh vỡ với `SkillManager.upgrade` (dep đang ở version cao hơn new_version của root → raise). Backup cũng chỉ root.

**Luồng:**
| # | Bước | Điều kiện | Event (payload mỗi event: kind, component_id, version, **step**, ...) |
|---|------|-----------|-------|
| 0 | START | luôn | `UPGRADE_STARTED` |
| 0.1 | **read current** | `read_current(kind, root)` — **đọc 1 lần, tái dùng cả pipeline**; `None` → fail ngay `step=compatibility, reason="component not found: <id>"` | — |
| 0.5 | skip check | `compare(new, current) <= 0` (invalid version → ValueError propagate — caller validate) | `UPGRADE_SKIPPED` → trả skipped (step=None) |
| 1 | compatibility | `checker.check_upgrade(current, new)`; compatible=False → fail | `UPGRADE_COMPATIBILITY_OK` |
| 2 | dependencies | `resolver.resolve`; ok=False → fail | `UPGRADE_DEPENDENCIES_OK` |
| — | **dry-run dừng tại đây** | `dry_run=True` → trả result(ok, plan) — KHÔNG backup/migrate/health | (không event thêm) |
| 3 | backup | `backup_store.backup` với payload đã đọc (raise → fail step=backup, KHÔNG rollback — chưa migrate gì) | `UPGRADE_BACKUP_CREATED` (kèm backup_id) |
| 4 | migrate | `migrator.migrate(kind, root, new_version)` (raise → rollback) | `UPGRADE_MIGRATED` |
| 5 | health | `read_current` (gọi lại) version == new_version (verify áp dụng thật) + `validate` hook (nếu có); fail → rollback | `UPGRADE_HEALTH_OK` |
| 6 | complete | — | `UPGRADE_COMPLETED` |

**Rollback (phản ứng)**: trigger = migrate raise / health fail / validate fail. Gọi `migrator.rollback` (NotImplementedError → write_current backup). Lỗi rollback → best-effort ghi vào reason, KHÔNG raise. Event `UPGRADE_ROLLED_BACK` (payload: kind, component_id, version, rolled_back: bool, errors: list[str]).

**Events (kernel/events.py — members uppercase, value pattern `"upgrade.<snake>"` như `UPGRADE_COMPLETED="upgrade.completed"` sẵn có):** `UPGRADE_STARTED`, `UPGRADE_SKIPPED`, `UPGRADE_COMPATIBILITY_OK`, `UPGRADE_DEPENDENCIES_OK`, `UPGRADE_BACKUP_CREATED`, `UPGRADE_MIGRATED`, `UPGRADE_HEALTH_OK`, `UPGRADE_ROLLED_BACK` + tái sử dụng `UPGRADE_COMPLETED`. Sink: pipeline emit `(type_str, payload)` với **type_str = member NAME** (vd. `"UPGRADE_STARTED"`); wrapper chuyển `EventType[type_str]` → `Event(type=..., payload=...)` → `EventBus.publish`. Wrapper là test-only helper (đặt trong test file, không phải module production — allow-list không bị ảnh hưởng). CLI emit=None (không nối bus — in console).

## 4. AC
- AC1: DependencyResolver — topo đúng (dep trước, sort (name, version)); missing → fail tên dep; cycle → fail kèm path; conflict (cùng name khác version) → fail; deterministic
- AC2: BackupStore — backup/restore/list đúng; persist 2 instance; list lọc kind/component_id
- AC3: Pipeline thành công — event sequence đúng: STARTED → COMPATIBILITY_OK → DEPENDENCIES_OK → BACKUP_CREATED → MIGRATED → HEALTH_OK → COMPLETED; status=ok; backup_id set; plan = topo order
- AC4: compatibility fail (**upgrade major breaking**: 1.0.0 → 2.0.0 — new > current qua skip-check, major khác → incompatible) → dừng bước 1, KHÔNG backup/migrate, step=compatibility, reason rõ
- AC5: dependency fail (missing) → dừng bước 2, step=dependencies
- AC6: health fail (version không áp dụng / validate trả reason) → rollback, status=failed, step=health, event UPGRADE_ROLLED_BACK
- AC7: migrate raise → rollback, step=migrate; rollback lỗi → ghi reason không raise
- AC8: same/older version → skipped (sau STARTED, trước compatibility, step=None), không lỗi; component không tồn tại → failed sớm step=compatibility reason "component not found" (bước 0.1)
- AC9: `dry_run=True` → chạy bước 0→2, trả plan, KHÔNG backup/migrate/health; CLI `aiagent upgrade <kind> <id> --version X [--dry-run]`: lazy import; **CLI v1 chỉ wire skill** (SkillMigrator + SkillManager từ `settings.skills.db_path`) — kind khác → exit 1 "not wired"; **lookup cho skill kind**: `SkillManager.get(id)` → `ComponentSpec(kind="skill", component_id=id, version=skill.version, dependencies=convert(manifest.dependencies))` — convert constraint `"name@>=1.2"` → `Dependency(name, version="1.2")` (chỉ lấy version, conflict check chỉ so pin khai báo — R2-3); exit code: success=0, skipped=0, dry-run ok=0, dry-run incompatible/missing=1, fail=1, version invalid=1 (bắt ValueError)
- AC10: allow-list AST upgrade/ — internal full path: `{"aios_core.contracts", "aios_core.semver", "aios_core.kernel.events", "aios_core.skills.errors"}` (SkillMigrator catch SkillError — R1-1) (+ intra-package exclusion aios_core.upgrade); external: `{sqlite3, pathlib, contextlib, json, dataclasses, typing, datetime, uuid, collections, logging}`; `test_inv_upgrade_import_allowlist`; toàn bộ pytest pass + coverage đo bằng `python -m pytest --cov=aios_core.upgrade --cov-report=term-missing` ≥ 80% (mục tiêu 95%)

## 5. Test
- `tests/test_upgrade_dependency.py` — topo, cycle, missing, conflict, deterministic
- `tests/test_upgrade_backup.py` — backup/restore/list, persist, payload fidelity
- `tests/test_upgrade_pipeline.py` — ok + events (DictMigrator); 4 fail path (compat/dep/health/migrate); rollback (DictMigrator qua write_current + migrator có rollback); skip; dry-run; backup-fail; component-not-found; read_current version verify
- `tests/test_upgrade_skill.py` — SkillMigrator wrap thật: upgrade ok + rollback; event 2 luồng (skill.updated + UPGRADE_*) — C2-15
- `tests/test_upgrade_cli.py` — dry-run/thật skill, exit codes, not wired, lazy import
- `tests/test_architecture.py` — allow-list upgrade/

## 6. Ghi chú (quyết định qua critique ×2 + review)
- Chỉ migrate ROOT; dependency chỉ resolve (C2-03)
- Dry-run: bước 0→2, plan trong result (C2-01)
- validate hook ở constructor (C2-02); health = read_current version check + validate (C2-04)
- Skill payload = model_dump(mode="json") (C2-05); rollback fallback write_current khi NotImplementedError (C2-06)
- CLI v1 chỉ wire skill (C2-08); backup-fail → step=backup, không rollback, orphan rows chấp nhận (C2-09)
- Không có step=rollback trong UpgradeResult; skipped → step=None (C2-10/R3-6); version invalid → ValueError propagate, CLI bắt exit 1 (C2-11)
- Component not found → fail sớm bước 0.1 (R2-2); read_current đọc 1 lần tái dùng (R2-2)
- AC4 case = upgrade major breaking (R2-1); allow-list gồm aios_core.skills.errors (R1-1)
- Exports `upgrade/__init__.py`: UpgradePipeline, UpgradeResult, DependencyResolver, BackupStore, DictMigrator, SkillMigrator, UpgradeError (R3-6)
- Pre-release mismatch → incompatible (semver rule 1); breaking luôn incompatible (không test nhánh breaking-compatible)
- Deterministic: không thread nền, không network, không real sleep
