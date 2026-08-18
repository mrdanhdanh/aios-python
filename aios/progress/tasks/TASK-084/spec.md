# TASK-084 — M12-P0: Version & Compatibility Baseline (C1) — SPEC v3

> Milestone: M12 AIOS 1.1 Compatibility (Issue #7, nhánh `feature/ISSUE-7-aios-1-1-compatibility`)
> Nâng cấp: C1 — version bump 1.0→1.1 toàn hệ thống (contract/config/CLI/metadata) + Compatibility Matrix registry
> Dependency: C1 → C2 (TASK-085) → C3 (TASK-086) → (C4 TASK-087 ∥ C5 TASK-088)
> v3 = tích hợp resolution critique-1 (11/11) + critique-2 (8/8)

## 1. Mục tiêu

1. **Version bump AIOS 1.0 → 1.1 đồng bộ toàn hệ thống**: `__version__`, API app, contract catalog, plugin manager, marketplace — mọi nơi khai báo **AIOS system version** phải khớp `1.1.0`.
2. **Compatibility Matrix registry**: module mới cho phép khai báo + kiểm tra min/max AIOS version của từng thành phần (plugin/contract/workflow/skill/sdk) — nền cho C2 (migration thật) và C3 (backward compat test).
3. **KHÔNG phá backward compatibility**: minor bump theo semver; INV-001..035 giữ nguyên frozen; KHÔNG thêm invariant mới.

## 2. Phạm vi

**In:**
- `backend/src/aios_core/__init__.py` `__version__ = "0.1.0"` → `"1.1.0"`
- `backend/src/aios_core/api/app.py` `FastAPI(version="0.1.0")` → `version=__version__` (bỏ hardcode)
- Contract catalog `contracts/catalog.py`: 10 contract `version="1.0.0"` → `"1.1.0"` (minor bump; lifecycle giữ nguyên)
- `plugins/manager.py` (dòng ~68) + `ecosystem/marketplace.py` **CẢ 2 chỗ** (`TrustChain.__init__` dòng ~85 + `MarketplaceRegistry._aios_version` dòng ~269): default `"1.0.0"` → `"1.1.0"`
- Module mới `backend/src/aios_core/upgrade/compatibility.py` (CompatibilityMatrix) + CLI `aiagent compat list/check`
- Cập nhật test assert **system version** (bắt buộc liệt kê trong `tasks.md`)

**Out (task khác):**
- C2 migration 1.0→1.1 thật (TASK-085) — chỉ chuẩn bị mốc
- C3 backward compat test plugin/contract/workflow v0→v1 (TASK-086)
- C4 conformance area `compatibility` (TASK-087) — KHÔNG thêm area/gate trong C1
- C5 ADR-0007 + migration guide (TASK-088)

### 2.1 Version history & mapping (RESOLVED C1-01)

| Version | Ý nghĩa | Trạng thái |
|---------|---------|-----------|
| `0.1.0` | Dev version nội bộ (đầu M0) — chưa release | Lịch sử — C1 bump trực tiếp lên `1.1.0` |
| `1.0.0` | Mốc release M10 (AIOS 1.0 CERTIFIED — tồn tại trong PLAN/PR promotion) | Mốc nâng cấp chính thức |
| `1.1.0` | M12 (AIOS 1.1 Compatibility) | **Mục tiêu C1** |

- Đường nâng cấp chính thức: `1.0.0 → 1.1.0` (minor, backward-compatible). `check_upgrade("0.1.0","1.1.0")` = **out-of-scope** (dữ liệu dev cũ không thuộc đường hỗ trợ; `CompatibilityChecker` Rule 4 coi 0.x→1.x breaking là đúng).
- C2 (TASK-085) sẽ dùng `from_version="1.0.0"` làm mốc release chuẩn.

## 3. Thiết kế đề xuất

### 3.1 Version constants
- `aios_core/__init__.py`: `__version__ = "1.1.0"` — các provider/model/`system status` đọc từ đây (không đổi cơ chế).
- `api/app.py`: `version=__version__` — `/openapi.json` phản ánh đúng.
- **Khảo sát phân loại**: artifact `implementation/survey.md` — bảng `file:dòng | giá trị | loại (AIOS version → bump / component version → giữ) | lý do` cho toàn bộ `"0.1.0"`/`"1.0.0"` trong `backend/src` (RESOLVED C1-06). Component version → **giữ nguyên**: harness benchmark/doctor/evaluation/testing/verification `version="1.0.0"`, `enterprise/contracts.py:147`, `tools/base.py:78`, `skills/sources.py`, `rendering/workflows.py`, `ecosystem/distiller.py:173`, `upgrade/migration.py:215`, `workflow/cli.py:727` sample, **`ecosystem/devkit.py:34,108` (scaffold riêng)**, **`kernel/services/policy.py:17` `DEFAULT_POLICY_VERSION="0.1.0"` (version schema policy)** — RESOLVED C2-04.

### 3.2 Contract catalog
- 10 contract: `version="1.0.0"` → `"1.1.0"`. `contract list/check/check-full` (M10-F2) tự phản ánh (đọc từ catalog).
- Xác minh `CompatibilityChecker.check_upgrade("1.0.0", "1.1.0")` → `compatible=True, breaking=False`.

### 3.3 Compatibility Matrix registry (module mới — `upgrade/compatibility.py`)

```python
class CompatibilityEntry(BaseModel):
    kind: Literal["plugin", "contract", "workflow", "skill", "sdk"]
    id: str                    # KHÔNG prefix loại (vd "demo", "agent") — RESOLVED C1-11
    version: str               # version component (semver)
    aios_min: str              # semver thuần — mốc AIOS tối thiểu (vd "1.0.0")
    aios_max: str | None       # constraint — hỗ trợ ".x" (vd "1.1.x", "2.x"); None = không chặn (RESOLVED C1-05)

class CompatibilityMatrix:
    DEFAULT_ENTRIES: tuple[CompatibilityEntry, ...]  # liệt kê cụ thể bên dưới
    def check(self, kind, id, version, aios_version="1.1.0") -> CompatibilityResult  # ok/errors/warnings
    def list(self) -> list[dict]
```

**`DEFAULT_ENTRIES` dự kiến (RESOLVED C1-04) — ≥ 14 entry:**
- 10 contract catalog (kind=`contract`, id = `agent`, `capability`, `tool`, `workflow`, `runtime`, `event`, `artifact`, `plugin`, `model`, `memory` — version `1.1.0`, aios_min `1.0.0`, aios_max `None`)
- 1 plugin mẫu: `plugin` / `demo` / `1.0.0` / min `1.0.0` / max `None`
- 1 workflow mẫu: `workflow` / `demo_flow` / `1.0.0` / min `1.0.0` / max `1.1.x`
- 1 skill mẫu: `skill` / `agent-sprite-forge` / `1.0.0` / min `1.0.0` / max `None`
- 1 sdk mẫu: `sdk` / `python` / `1.0.0` / min `1.0.0` / max `None`

**Chính sách fail-closed (RESOLVED C1-03):**
- kind/id không tồn tại trong matrix → **error** (KHÔNG tự PASS)
- component version không parse được / aios_version ngoài `[aios_min, aios_max]` → **error** (incompatible)
- version component ≠ `entry.version` → **warning** (không chặn) — RESOLVED C1-10
- **API BẮT BUỘC (RESOLVED C2-05)**: gọi `check_compatibility(aios_min, aios_max or "*", aios_version)` (từ `plugins/compat.py`) — KHÔNG dùng `Constraint.matches()` (semantics exact-match, KHÔNG phải min-floor); `aios_max=None` → map `"*"`. Test negative: aios `0.9.0` với min `1.0.0` → error.
- **Import allow-list (RESOLVED C2-01)**: `upgrade/compatibility.py` import `plugins/compat.py` → phải thêm `aios_core.plugins.compat` vào `_UPGRADE_ALLOWED_AIOS` trong `tests/test_architecture.py` (kèm comment lý do — style entry hiện có) — nếu không, `test_inv_upgrade_import_allowlist` FAIL (P1).

### 3.4 CLI (`workflow/cli.py`)
- `aiagent compat list` → bảng text `kind | id | version | aios_min | aios_max` + tổng số entry
- `aiagent compat check <kind> <id> <version> [--aios-version X.Y.Z]` → **JSON không indent (1 dòng)** `{"compatible": bool, "errors": [...], "warnings": [...]}` — RESOLVED C2-06 (khác style `indent=2` của CLI hiện có có chủ đích: máy parse); exit 0 compatible, exit 1 fail-closed. Test CLI dùng `json.loads`, không so chuỗi chính xác.
- Tên `compat` — không trùng `contract check` (M10-F2) hay `extension/matrix.py` (M8)

### 3.5 Quan hệ & tiêu thụ (RESOLVED C1-08 + C2-08)
- Trong C1: `CompatibilityMatrix` là **registry tham chiếu** — CHỈ CLI `compat` + test tiêu thụ.
- KHÔNG đổi hành vi: plugin manager (`plugins/manager.py:187,232`) dùng `check_compatibility` riêng; marketplace `TrustChain` dùng `_in_range` tự viết (semantics LỎNG hơn — coi max `"1.1.x"` như `"1.x"`; known divergence, ghi nhận cho TASK-085/086 — KHÔNG sửa trong C1).
- C2 (TASK-085): nối upgrade pipeline vào matrix. C4 (TASK-087): nối conformance. Không wiring sớm.

## 4. Input / Output

| Lệnh | Input | Output |
|------|-------|--------|
| `aiagent compat list` | — | Bảng `kind \| id \| version \| aios_min \| aios_max` + tổng entry; exit 0 |
| `aiagent compat check plugin demo 1.0.0` | kind, id (không prefix), version (default aios=1.1.0) | JSON 1 dòng `{compatible, errors, warnings}`; exit 0 |
| `aiagent compat check plugin demo 2.0.0` | version ≠ entry.version | compatible nhưng `warnings` (version component khác) |
| `aiagent compat check contract unknown 1.0.0` | id lạ | error → exit 1 (fail-closed) |
| `aiagent compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` | override vượt max `1.1.x` | error → exit 1 (RESOLVED C2-02) |

## 5. Tiêu chí chấp nhận (AC)

- [ ] AC1: `aios_core.__version__ == "1.1.0"`; `aiagent system status` trả `1.1.0`
- [ ] AC2: contract catalog: 10 contract version `1.1.0`; `aiagent contract list` hiển thị `1.1.0`; `contract check` PASS (không breaking)
- [ ] AC3: `CompatibilityChecker.check_upgrade("1.0.0", "1.1.0")` → `compatible=True, breaking=False`
- [ ] AC4: plugin manager + marketplace (cả 2 chỗ) default `aios_version="1.1.0"`
- [ ] AC5: `DEFAULT_ENTRIES` ≥ 14 entry (10 contract + plugin + workflow + skill + sdk); `compat list` trả đúng
- [ ] AC6: `compat check` compatible → exit 0; vector out-of-range (RESOLVED C2-07): `compat check contract agent 1.0.0 --aios-version 0.9.0` → error exit 1 (aios_min) + `compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` → error exit 1 (aios_max); **`--aios-version 1.1.5` với `workflow demo_flow` (max `"1.1.x"`) → compatible exit 0** (RESOLVED C1-05)
- [ ] AC7: kind/id không có trong matrix → error (KHÔNG tự PASS)
- [ ] AC8: `--aios-version` override hoạt động (aios 2.0.0 với entry max `1.1.x` → incompatible)
- [ ] AC9: full suite pytest **≥ 2052 PASS / 0 FAIL**; test cũ assert system version đã cập nhật: `tests/test_models.py:104` ("0.1.0" → "1.1.0") + **`tests/test_contracts_catalog.py::test_cli_contract_list` ("1.0.0" → "1.1.0")** (RESOLVED C2-03); test component version giữ nguyên (kể cả `test_ecosystem_devkit.py:31`, `test_policy.py:71` — RESOLVED C2-04); `_UPGRADE_ALLOWED_AIOS` + `aios_core.plugins.compat` (RESOLVED C2-01)
- [ ] AC10: KHÔNG vi phạm INV-001..035; KHÔNG thêm invariant; `aiagent arch-health` 0 violations; `doctor` healthy
- [ ] AC11: `GET /openapi.json` (hoặc metadata API app) trả version `1.1.0` (RESOLVED C1-02)
- [ ] AC12: CLI thật chạy được (không lỗi argparse); help text đúng; `implementation/survey.md` có bảng phân loại đầy đủ

## 6. Rủi ro & giả định

| Rủi ro | Cách xử lý |
|--------|-----------|
| Test cũ assert "0.1.0"/"1.0.0" (system) | Khảo sát bước 1 → liệt kê trong `tasks.md` → cập nhật test trong cùng PR (bump chủ động) |
| Test component version "1.0.0" (~47 file) | KHÔNG sửa — chỉ sửa test assert **system version** (survey.md phân loại) |
| pydantic `extra=forbid` model cũ | KHÔNG sửa model cũ; `CompatibilityEntry` là model mới riêng |
| Bump `__version__` ảnh hưởng model providers (version header) | Chỉ đọc `__version__` — không đổi hành vi; test providers PASS |
| Conformance assert version? | **KHÔNG có** — AreaChecks/GS/gates không assert system version (khảo sát thật); `golden.py` hardcode = component data → giữ nguyên (RESOLVED C1-09) |
| Trùng tên cơ chế compatibility | `upgrade/compatibility.py` ≠ `contracts/compatibility.py` ≠ `plugins/compat.py` ≠ `extension/matrix.py`; §3.5 nêu rõ quan hệ |
| Tương tác C2/C3 | Matrix độc lập, không chặn; C2/C3 chỉ tiêu thụ sau khi nối (TASK-085/087) |

## 7. Ghi chú triển khai

1. Khảo sát `grep -rn "0.1.0\|1.0.0" backend/src backend/tests` → tạo `implementation/survey.md` (bảng phân loại bump/giữ — gồm devkit.py + policy.py).
2. Bump: `__init__.py` → `"1.1.0"`; `api/app.py` → `version=__version__`; contract catalog 10 contract → `"1.1.0"`; plugin manager + marketplace (2 chỗ) → `"1.1.0"`.
2.5. **Sửa allow-list (RESOLVED C2-01)**: thêm `aios_core.plugins.compat` vào `_UPGRADE_ALLOWED_AIOS` trong `tests/test_architecture.py` kèm comment lý do — nếu không full suite FAIL.
3. Viết `upgrade/compatibility.py` (CompatibilityEntry + CompatibilityMatrix + DEFAULT_ENTRIES — dùng `check_compatibility(aios_min, aios_max or "*", aios_version)`) + test `tests/test_compatibility_matrix.py`.
4. Thêm CLI `compat list/check` vào `workflow/cli.py` (JSON không indent) + test CLI.
5. Cập nhật test assert system version (`test_models.py:104`, `test_cli_contract_list`).
6. Chạy full suite + `arch-health` + `doctor` + `contract check` + CLI thật.
7. Ghi `aios/progress/LOG.md` song song; đóng 8-file hard gate.
