# TASK-086 — M12-P2: Backward Compatibility v0→v1 trên 1.1 (C3) — SPEC v3

> Milestone: M12 AIOS 1.1 Compatibility (Issue #7, nhánh `feature/ISSUE-7-aios-1-1-compatibility`)
> Nâng cấp: C3 — plugin v0→v1 · contract v0→v1 · workflow v0→v1 chạy trên 1.1 + test chéo cũ→mới
> Dependency: C1 (TASK-084 ✅) → C2 (TASK-085 ✅) → C3 → (C4 ∥ C5)
> v3 = tích hợp resolution critique-1 (9/9) + critique-2 (6/6)

## 1. Mục tiêu

1. **Chứng minh backward compatibility bằng bộ test chéo (cross-version suite)**: dữ liệu/component format cũ (v0/v1) chạy được trên AIOS 1.1.0 — plugin manifest v0/v1, workflow definition v0, contract payload v0, extension contract cũ, dữ liệu đã migrate 1.0→1.1.
2. **Module + CLI kiểm tra chéo có thật**: `aiagent compat verify` — chạy toàn bộ scenario cũ→mới trên runtime 1.1, fail-closed.
3. **KHÔNG sửa hành vi runtime** — ngoại lệ duy nhất: **thay đổi parse-only** để đảm bảo tương thích (C1-01: thêm field `compatible` vào `AiosRange` — lỗ hổng THẬT do TASK-085 tạo ra, fix parse-only không đổi hành vi check).

## 2. Phạm vi

**In:**
- **FIX parse-only**: `plugins/contracts.py` — `AiosRange` thêm `compatible: list[str] = Field(default_factory=list)` (C1-01; `validate_manifest`/check min-max KHÔNG đổi)
- Module mới `backend/src/aios_core/upgrade/backward_compat.py` — `BackwardCompatibilitySuite` (9 check, 5 kind)
- CLI `aiagent compat verify` (subcommand dưới `compat` — không phá list/check)
- Allow-list: thêm module cần thiết vào `_UPGRADE_ALLOWED_AIOS` kèm comment (C1-03)
- Tests: unit + CLI thật

**Out:** C4 conformance area (TASK-087), C5 ADR + guide (TASK-088)

## 3. Thiết kế

### 3.1 `upgrade/backward_compat.py`

```
@dataclass
class BackwardCheck:
    id: str; kind: Literal["workflow","plugin","contract","extension","migrated"]
    description: str
    run: Callable[[], tuple[bool, str]]    # ĐƯỢC PHÉP raise (C1-07) — runner bắt → (False, str(exc))

class BackwardCompatibilitySuite:
    CHECKS: tuple[BackwardCheck, ...]      # đúng 9 check, 5 kind (C1-09)
    def __init__(self, checks: Sequence[BackwardCheck] | None = None)   # default CHECKS (C2-05)
    def run(self) -> BackwardCompatibilityReport
@dataclass
class BackwardCompatibilityReport:
    ok: bool; results: list[BackwardCheckResult]; fail_closed: bool = True
```

**9 scenario (đúng 5 kind — C1-09):**
1. `workflow-v0-parse` (workflow) — WorkflowDefinition v0 (nodes KHÔNG timeout_s → default 300.0) → `model_validate` + MockCompiler.compile OK
2. `workflow-v0-run-simulate` (workflow) — workflow v0 version `"0.1.0"` + nodes task → `_run_simulate` trả exit 0 (completed) — chấp nhận kernel-sim 1 lần dữ liệu nhỏ (C1-05); **bọc `contextlib.redirect_stdout(io.StringIO())`** (C2-02); audit db trỏ temp (C2-06)
3. `plugin-v0-load` (plugin) — `PluginManifest.validate_manifest(**manifest_v0)` + `check_compatibility("1.0.0","*","1.1.0")` True (không chạy resolve/DB — C1-08)
4. `plugin-v1-compatible-field` (plugin) — PluginManifest v1 (có `aios.compatible=["1.0.0","1.1.0"]`) parse OK (kiểm chứng fix C1-01; thay scenario TrustChain — C1-04)
5. `contract-v0-compat` (contract) — `is_compatible(installed="1.1.0", required="1.0.0")` True + `check_upgrade("1.0.0","1.1.0").compatible is True` (C1-08)
6. `contract-v0-catalog` (contract) — payload contract v0 fixture chuẩn → ContractDefinition parse + schema_exists (C1-08)
7. `extension-v0-matrix` (extension) — test 2 CHIỀU: `assert_namespace_allowed("extension", ALLOWED)` PASS + `assert_namespace_allowed("internal", ALLOWED)` → CompatibilityViolation → check FAIL (kiểm chứng gate thật; ALLOWED do check định nghĩa theo PLAN §M8-E3 — C1-06)
8. `migrated-110-data` (migrated) — payload TASK-085 output (plugin compatible ["1.0.0","1.1.0"], workflow version 1.1.0, contract version 1.1.0) → `PluginManifest.model_validate`/`WorkflowDefinition.model_validate`/`ContractDefinition` parse OK (sau fix C1-01)
9. `migrated-v0-formats` (migrated) — `MigrationFormats`: config v0→v1 → dict-check `max_duration_seconds`; workflow v0→v1 → `WorkflowDefinition.model_validate` PASS; plugin v0→v1 → `PluginManifest.model_validate` PASS (C1-02)

**Fail-closed**: check được phép raise; runner bắt mọi exception → `(False, str(exc))` (C1-07); `report.ok = all(results.ok)`.

### 3.2 Fixture chuẩn v0 (C1-08 + C2-03)

- plugin v0: `{"id":"demo","name":"demo","version":"1.0.0","aios":{"min":"1.0.0","max":"*"}}`
- workflow v0: `{"name":"demo_flow","version":"0.1.0","nodes":[{"id":"n1","type":"task","name":"n1"}]}` (không timeout_s)
- workflow v0 **YAML** (scenario 2 — C2-03): `name: demo_flow\nversion: 0.1.0\nnodes:\n  - id: n1\n    type: task\n    name: n1` — tạo file bằng `Path.cwd() / f"_compat_wf_{uuid4().hex}.yaml"` + `try/finally: unlink()` (pathlib + uuid đã allow)
- contract v0: `{"id":"agent","name":"Agent Contract","version":"1.0.0","schema_ref":("aios_core.agents.base","Assistant"),"lifecycle":"stable"}`
- extension cũ: namespace `"extension"` (hợp lệ) + `"internal"` (vi phạm)

### 3.3 CLI `aiagent compat verify`

- Subparser `verify` dưới `compat`; output JSON 1 dòng: `{"ok": bool, "fail_closed": true, "results": [{id, kind, ok, detail}], "summary": {"passed": N, "failed": M}}`; exit 0/1

### 3.4 Allow-list (C1-03 + C2-01)

Thêm vào `_UPGRADE_ALLOWED_AIOS` (kèm comment) — **7 module**: `workflow.definition`, `workflow.compiler`, `workflow.cli` (scenario 2 gọi `_run_simulate` — C2-01), `plugins.contracts`, `contracts.catalog`, `contracts.compatibility`, `extension.matrix`. KHÔNG cần `ecosystem.marketplace`/`kernel`/`config` (giữ thiết kế control plane).

## 4. Input / Output

| Lệnh | Input | Output |
|------|-------|--------|
| `aiagent compat verify` | — | JSON 1 dòng `{ok, fail_closed, results[], summary{passed, failed}}`; exit 0/1 |

## 5. Tiêu chí chấp nhận (AC)

- [ ] AC1: Suite có **đúng 9 check, đủ 5 kind** (workflow×2, plugin×2, contract×2, extension×1, migrated×2)
- [ ] AC2: `workflow-v0-parse`: WorkflowDefinition v0 (không timeout_s) parse + compile OK
- [ ] AC3: `plugin-v0-load`: `validate_manifest` v0 + `check_compatibility("1.0.0","*","1.1.0")` True
- [ ] AC4: `contract-v0-compat`: `is_compatible("1.1.0","1.0.0")` True + `check_upgrade("1.0.0","1.1.0")` compatible
- [ ] AC5: `extension-v0-matrix`: 2 chiều (extension PASS, internal FAIL — gate thật)
- [ ] AC6: `migrated-110-data`: payload TASK-085 output parse lại OK qua model thật; **round-trip**: `manifest.aios.compatible == ["1.0.0","1.1.0"]` sau model_validate + model_dump (C2-04)
- [ ] AC7: fail-closed: Suite nhận `checks` có 1 check raise → `report.ok=False`, các check khác vẫn chạy, CLI exit 1 (C2-05)
- [ ] AC8: CLI `aiagent compat verify` → exit 0 + JSON đúng cấu trúc + summary passed = 9; **stdout ngoài JSON rỗng** (C2-02); `compat list/check` không bị phá
- [ ] AC9: **FIX parse-only**: `AiosRange.compatible` parse OK (`test_aios_range_compatible_field`); `validate_manifest`/check min-max KHÔNG đổi (assert `check_compatibility("2.0.0","*","1.5.0") is False` — C2-04); full suite **0 regression so với baseline 2098** (PROGRESS.md TASK-085) + toàn bộ test mới PASS; allow-list test PASS
- [ ] AC10: arch-health 0 violations; doctor healthy; KHÔNG thêm invariant; INV-001..035 giữ nguyên

## 6. Rủi ro & giả định

| Rủi ro | Cách xử lý |
|--------|-----------|
| Module mới import ngoài allow-list | Thêm 7 module vào `_UPGRADE_ALLOWED_AIOS` kèm comment (precedent C2-01 TASK-084) |
| Scenario 2 chạy kernel-sim | Chấp nhận 1 lần, dữ liệu nhỏ (C1-05); redirect_stdout (C2-02); audit db trỏ temp (C2-06) |
| `AiosRange` thêm field phá test cũ | Parse-only + default_factory → không phá; test hồi quy `test_plugins.py` PASS |
| `assert_namespace_allowed` semantics | Test 2 chiều đúng API (allowed truyền vào) |
| Contract fixture schema_ref import thật | Dùng `schema_exists()` — module `aios_core.agents.base` import được |

## 7. Ghi chú triển khai

1. Fix `AiosRange.compatible` (plugins/contracts.py) + test hồi quy.
2. Tạo `upgrade/backward_compat.py` (9 check + Suite + Report).
3. CLI `compat verify` (JSON 1 dòng, exit 0/1).
4. Allow-list + 6 module.
5. Test `tests/test_backward_compat.py` (unit + fail-closed + CLI + AiosRange fix).
6. Chạy targeted + full suite + arch-health + doctor.
7. Đóng 8-file hard gate; LOG/PROGRESS; commit — KHÔNG push.
