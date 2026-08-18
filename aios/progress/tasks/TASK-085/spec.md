# TASK-085 — M12-P1: Migration 1.0→1.1 thật (C2) — SPEC v3

> Milestone: M12 AIOS 1.1 Compatibility (Issue #7, nhánh `feature/ISSUE-7-aios-1-1-compatibility`)
> Nâng cấp: C2 — upgrade pipeline end-to-end (plan → backup → dry-run → validate → rollback)
> Dependency: C1 (TASK-084 ✅) → C2 → C3 (TASK-086) → (C4 ∥ C5)
> v3 = tích hợp resolution critique-1 (15/15) + critique-2 (9/9)

## 1. Mục tiêu

1. **Migration 1.0→1.1 chạy được end-to-end**: luồng THẬT (plan chuẩn → backup snapshot → dry-run → validate → apply → rollback) trên đường `1.0.0 → 1.1.0` (mốc release chính thức — TASK-084 §2.1). Phạm vi = **luồng thật, dữ liệu demo** (journal SQLite + backup + CLI output; KHÔNG write-back persistence — RESOLVED C1-11).
2. **Nối Compatibility Matrix vào pipeline** (PLAN §M12 + TASK-084 §3.5): pre-check + post-check fail-closed.
3. **KHÔNG phá v0→v1 cũ**: MigrationEngine/MigrationFormats giữ nguyên; CLI `migrate` tái dùng, rẽ nhánh an toàn.

## 2. Phạm vi

**In:**
- Module mới `backend/src/aios_core/upgrade/migration_110.py` — transforms thật + `PLANS_110` (4 kind) + `Aios110Migrator`
- Sửa bug `MigrationEngine.apply` (call backup sai signature — RESOLVED C1-01) kèm test hồi quy
- CLI `aiagent migrate`: thêm kind `contract`; rẽ nhánh `from=1.0.0, to=1.1.0` → `Aios110Migrator` (đọc `--input` nếu cấp)
- Tests: unit transforms + matrix gate + rollback + CLI (`--journal` tmp_path — C1-15)

**Out:** C3 (TASK-086), C4 (TASK-087), C5 (TASK-088)

## 3. Thiết kế

### 3.1 `upgrade/migration_110.py` (module mới)

```
from .compatibility import AIOS_VERSION          # internal — tránh hardcode 2 nơi (C1-14)
from .migration import MigrationEngine, MigrationPlan, MigrationStep, MigrationJournal
AIOS_100 = "1.0.0"

def _deep(data): return json.loads(json.dumps(data))   # json round-trip — KHÔNG import copy (C1-14)

# -- transforms (pure, deep-copy input — C1-08; idempotent) --
def migrate_config_100_110(data) -> dict
    # thêm data["migration"] = {"from":"1.0.0","to":"1.1.0"} nếu chưa có (C1-13)
def rollback_config_100_110(data) -> dict
    # xóa data["migration"] CHỈ khi == {"from":"1.0.0","to":"1.1.0"} (guard C1-07)
def migrate_workflow_100_110(data) -> dict
    # bump data["version"] top-level "1.0.0"→"1.1.0" (C1-04); version khác → no-op
def rollback_workflow_100_110(data) -> dict
    # hạ CHỈ khi version == "1.1.0" (guard)
def migrate_plugin_100_110(data) -> dict
    # compatible thiếu → seed [aios.get("min","1.0.0")] rồi append "1.1.0" nếu chưa có (C2-03 + R4); aios thiếu → setdefault + min="1.0.0"
def rollback_plugin_100_110(data) -> dict
    # xóa "1.1.0" khỏi compatible (khôi phục trạng thái trước transform — C2-03)
def migrate_contract_100_110(data) -> dict      # bump data["version"] "1.0.0"→"1.1.0"
def rollback_contract_100_110(data) -> dict

def build_110_plan(kind, component_id) -> MigrationPlan
    # migration_id = f"aios-1.0-to-1.1-{kind}-{component_id}" (C2-04 + R2 — idempotent per component)
    # from="1.0.0"; to=AIOS_VERSION; backup_required=True
    # steps = [MigrationStep(kind, f"{kind}-100-to-110", fn, rollback_fn)]

PLANS_110: dict[str, ...]  # registry kind → TEMPLATE (steps + kind) — validate kind + sinh plan (R2)
# get_plan(kind, component_id) -> MigrationPlan | None  — plan thật LUÔN qua build_110_plan(kind, component_id)

PLANS_110: dict[str, MigrationPlan] = {k: build_110_plan(k) for k in ("config","workflow","plugin","contract")}
```

### 3.2 `Aios110Migrator` (matrix-gated)

```
@dataclass
class Aios110Result:
    payload: dict; backup_id: int | None; journal_status: str | None
    matrix: dict  # {"pre": "ok"|"blocked", "post": "ok"|"blocked"|"skipped"}

class Aios110Migrator:
    def __init__(self, matrix=None, engine=None, backup_store=None)   # defaults real
    def component_id(self, kind, payload) -> str   # plugin/contract=data["id"], workflow=data["name"], config="config" (C1-11)
    def _pre_check(self, kind, payload) -> None    # (1) range: semver 1.0.0 <= version <= 1.1.0 — CHỈ plugin/workflow/contract (C2-01)
                                                   # (2) matrix: chỉ kind có entry (plugin/demo, workflow/demo_flow, contract/*) — config SKIP (C1-02b + C2-01)
                                                   #     fail → raise MigrationError (journal KHÔNG start)
    def _post_check(self, kind, payload) -> None   # assertion thật (C1-06 + C2-03): workflow/contract version=="1.1.0";
                                                   # plugin "1.1.0" in aios.compatible; config migration marker; + matrix check
    def dry_run(self, kind, payload) -> Aios110Result   # pre_check → engine.dry_run (không side effect)
    def apply(self, kind, payload) -> Aios110Result     # pre_check → backup_store.backup(...) TRƯỚC (C1-01) → engine.apply → post_check
                                                         # post_check fail → engine.rollback(plan, RESULT) (C2-06) + journal rolled_back → raise
    def rollback(self, kind, payload) -> Aios110Result  # engine.rollback(plan, result)
```

- `Aios110Result.matrix` = `{"pre": "ok"|"blocked"|"skipped", "post": "ok"|"blocked"|"skipped", "warnings": [...]}` — `ok` = compatible (warning không chặn — C2-09).
- Backup (C1-01): `Aios110Migrator.apply` gọi `BackupStore.backup(kind, component_id, version, payload)` trực tiếp; SỬA `MigrationEngine.apply` bỏ đoạn `self._backup.backup(f"migration:...")` sai signature (caller chịu trách nhiệm) — test hồi quy C2-08 (inject backup fake → engine không gọi backup, journal completed; giữ param `backup_store` — ghi chú dead).

### 3.3 CLI `aiagent migrate` (rẽ nhánh an toàn)

- choices kind giữ free-form (R1 — argparse `choices` sẽ SystemExit(2) làm vỡ `test_cli_migrate_invalid_kind`): validate TRONG `_migrate` bằng kind set/`PLANS_110` → None → in lỗi + return 1; vẫn yêu cầu chọn `--dry-run` hoặc `--apply`.
- **`--input` default → `None`** (C2-02 — kiểm tra test cũ an toàn); `None` → stub khớp matrix (C1-03): plugin `{"id":"demo","version":"1.0.0","aios":{"min":"1.0.0"}}`, workflow `{"name":"demo_flow","version":"1.0.0","nodes":[{"id":"n1","type":"task","name":"n1"}]}`, contract `{"id":"agent","version":"1.0.0"}`, config `{}`. Có giá trị → đọc JSON file; file lỗi/không tồn tại → exit 1 rõ ràng.
- Output: text style hiện có + `matrix: pre/post` + `backup_id:` + `journal:` status (+ warnings nếu có — C2-09).
- Các from/to khác → nhánh cũ giữ nguyên (MigrationFormats v0→v1).

## 4. Input / Output

| Lệnh | Input | Output |
|------|-------|--------|
| `aiagent migrate config 1.0.0 1.1.0 --dry-run` | — (stub) | plan steps + matrix pre ok; KHÔNG side effect |
| `aiagent migrate plugin 1.0.0 1.1.0 --apply` | — (stub demo) | backup_id + steps + matrix pre/post ok + journal completed; exit 0 |
| `aiagent migrate contract 1.0.0 1.1.0 --apply --input f.json` | payload file | như trên (payload từ file) |
| `aiagent migrate plugin 1.0.0 1.1.0 --apply --input p.json` (id=p) | id không có entry | matrix pre blocked → từ chối, journal không start; exit 1 |
| `aiagent migrate workflow 0.5.0 1.0.0 --apply` | — | nhánh cũ (v0→v1) — không đổi |

## 5. Tiêu chí chấp nhận (AC)

- [ ] AC1: `build_110_plan(kind, component_id)` — migration_id gồm component_id (C2-04); đủ 4 kind; `from=1.0.0, to="1.1.0", backup_required=True`, ≥ 1 step có rollback_fn
- [ ] AC2: `migrate_plugin_100_110` **append** `"1.1.0"` vào `aios.compatible` khi chưa có (giữ phần tử gốc — C2-03); idempotent; rollback **xóa `"1.1.0"`** (khôi phục đúng); input không mutate
- [ ] AC3: `migrate_workflow_100_110` bump `data["version"]` top-level 1.0.0→1.1.0; version khác no-op; rollback hoàn nguyên (guard)
- [ ] AC4: `migrate_contract_100_110` bump version; `migrate_config_100_110` thêm `migration` marker; cả 4 transform deep-copy (input không mutate)
- [ ] AC5: pre-check fail (id không có entry matrix — plugin/p hoặc workflow/khác demo_flow) → từ chối, journal KHÔNG start
- [ ] AC6: `apply` thành công → journal `completed` + backup_id có + **per-kind** (C2-07): plugin → `"1.1.0" in aios.compatible` (version giữ nguyên); workflow/contract → `version == "1.1.0"`; config → migration marker; matrix pre/post ok
- [ ] AC7: step fail giữa chừng → auto-rollback → journal `failed`/`rolled_back` (R3) + payload khôi phục (rollback guard); post-check fail → rollback(plan, RESULT) → payload == bản gốc + `journal_status="rolled_back"` + backup_id giữ lại (C2-06)
- [ ] AC8: CLI `migrate contract 1.0.0 1.1.0 --apply` (--journal tmp) → exit 0 + backup + journal; `--dry-run` không side effect; `--input` file lỗi → exit 1 (C2-02); `migrate config ... --apply` payload tùy ý qua pre-check (C2-01)
- [ ] AC9: CLI `migrate plugin 1.0.0 1.1.0 --apply` → matrix post ok (CompatibilityMatrix thật); `migrate workflow ... --input p.json` id lạ → exit 1; cùng kind apply lần 2 (component khác) KHÔNG bị idempotent chặn (C2-04)
- [ ] AC10: full suite pytest ≥ 2071 PASS / 0 FAIL (verify baseline trước implement — C1-15); test cũ (`test_migration.py`, `test_upgrade_cli.py`) vẫn PASS
- [ ] AC11: allow-list không vi phạm (module mới chỉ import nội bộ upgrade/* + semver + plugins.compat + contracts; KHÔNG import copy)
- [ ] AC12: arch-health 0 violations; doctor healthy; KHÔNG thêm invariant; INV-001..035 giữ nguyên

## 6. Rủi ro & giả định

| Rủi ro | Cách xử lý |
|--------|-----------|
| Sửa bug `engine.apply` phá test cũ | Test hồi quy C2-08 (backup fake không được gọi); xác minh `test_migration.py` không inject backup có assert backup call |
| Stub khác dữ liệu thật | Dữ liệu demo được khai báo rõ trong spec; payload từ `--input` cho dữ liệu người dùng |
| Matrix check config | Policy: config SKIP matrix + range (C2-01) — ghi trong code + survey |
| `aios.compatible` 2 quy ước | Chuẩn 1.1 = **append** `"1.1.0"` vào list (tương thích v0→v1 `[min]` — C2-03); `plugin_v0_to_v1` cũ giữ nguyên |
| Journal ghi vào DB thật khi test | Unit test inject `:memory:`/tmp; CLI test truyền `--journal` tmp_path (C1-15 + C2-05) |

## 7. Ghi chú triển khai

1. Sửa bug `MigrationEngine.apply` (bỏ backup call sai) + test hồi quy C2-08.
2. Tạo `upgrade/migration_110.py` (transforms + `build_110_plan(kind, component_id)` + Aios110Migrator + Aios110Result).
3. CLI `migrate`: choices thêm contract; `--input default=None` (C2-02); rẽ nhánh 1.0.0→1.1.0 (stub mới, PLANS_110.get guard).
4. Test mới `tests/test_migration_110.py` (unit inject `:memory:`/tmp + matrix gate + rollback + CLI --journal tmp).
5. Chạy targeted + full suite (verify baseline) + arch-health + doctor.
6. Đóng 8-file hard gate; LOG/PROGRESS; commit — KHÔNG push (user xử lý dần, PR #8 draft giữ nguyên).
