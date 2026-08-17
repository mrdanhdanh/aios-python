# TASK-084 — Tasks breakdown (checklist)

> Spec: `spec.md` v3 (12 AC). Hard gate: spec ✅ + critique-1 (11/11) ✅ + critique-2 (8/8) ✅
> ⚠️ User: làm xong từ từ, KHÔNG merge (PR #8 draft giữ nguyên)

## A. Khảo sát & tài liệu
- [ ] A1. Tạo `implementation/survey.md` — bảng phân loại `file:dòng | giá trị | loại (bump/giữ) | lý do` cho mọi `"0.1.0"`/`"1.0.0"` trong `backend/src` + `backend/tests` (gồm devkit.py + policy.py — C2-04)
- [ ] A2. Xác nhận danh sách test assert **system version** cần sửa (C2-03): `test_models.py:104`, `test_contracts_catalog.py::test_cli_contract_list`; test component version giữ nguyên (`test_ecosystem_devkit.py:31`, `test_policy.py:71`, ...)

## B. Version bump (C1)
- [ ] B1. `src/aios_core/__init__.py:3` — `__version__ = "1.1.0"` (AC1)
- [ ] B2. `src/aios_core/api/app.py:49` — `FastAPI(version="0.1.0")` → `version=__version__` (AC11)
- [ ] B3. `src/aios_core/contracts/catalog.py` — 10 contract `version="1.0.0"` → `"1.1.0"`; `deprecated_in` của plugin GIỮ `"1.0.0"` (AC2)
- [ ] B4. `src/aios_core/plugins/manager.py:68` — `aios_version: str = "1.0.0"` → `"1.1.0"` (AC4)
- [ ] B5. `src/aios_core/ecosystem/marketplace.py` — CẢ 2 chỗ: `TrustChain.__init__` (~dòng 85) + property `_aios_version` (~dòng 268) → `"1.1.0"` (AC4)

## C. Compatibility Matrix registry (C1)
- [ ] C1. Tạo `src/aios_core/upgrade/compatibility.py`: `CompatibilityEntry` (pydantic, kind/id/version/aios_min/aios_max) + `CompatibilityMatrix` (DEFAULT_ENTRIES ≥ 14 entry + `check()` fail-closed + `list()`)
- [ ] C2. `check()` dùng `check_compatibility(aios_min, aios_max or "*", aios_version)` từ `plugins/compat.py` — KHÔNG dùng `Constraint.matches()` (C2-05); kind/id lạ → error (C1-03); version ≠ entry.version → warning (C1-10)
- [ ] C3. Sửa `tests/test_architecture.py:1147` `_UPGRADE_ALLOWED_AIOS` + `"aios_core.plugins.compat"` kèm comment (C2-01 — nếu thiếu full suite FAIL)

## D. CLI
- [ ] D1. `src/aios_core/workflow/cli.py`: thêm subparser `compat` (list + check) + dispatch trong `main()` + hàm `_compat_list()` / `_compat_check()`
- [ ] D2. Output: `list` = bảng text; `check` = JSON không indent 1 dòng `{compatible, errors, warnings}`; exit 0/1 (C2-06)

## E. Tests
- [ ] E1. Tạo `tests/test_compatibility_matrix.py` — unit: entry valid/invalid, check compatible/out-of-range (min 0.9.0 fail, max "1.1.x" chấp nhận 1.1.5 + chặn 2.0.0), kind/id lạ error, warning version mismatch, list() ≥ 14 entry, `check_upgrade("1.0.0","1.1.0")` compatible
- [ ] E2. Sửa `test_models.py:104` — `"0.1.0"` → `"1.1.0"` (AC9)
- [ ] E3. Sửa `test_contracts_catalog.py::test_cli_contract_list` — `"1.0.0" in out` → `"1.1.0" in out` (AC9)
- [ ] E4. Thêm test CLI compat (main() thật + capsys + exit code) trong `test_compatibility_matrix.py`

## F. Verify & đóng task
- [ ] F1. Chạy targeted: `pytest tests/test_compatibility_matrix.py tests/test_models.py tests/test_contracts_catalog.py tests/test_architecture.py` — PASS
- [ ] F2. Chạy full suite pytest — ≥ 2052 PASS / 0 FAIL (AC9)
- [ ] F3. CLI thật: `aiagent system status`, `aiagent contract list`, `aiagent compat list`, `aiagent compat check plugin demo 1.0.0`, `compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` (exit 1), `compat check contract unknown 1.0.0` (exit 1), openapi version (AC1/2/5/6/7/8/11/12)
- [ ] F4. `aiagent arch-health` 0 violations + `aiagent doctor` healthy (AC10)
- [ ] F5. Viết `test.md` (kết quả test thật) + `evaluation.md` (đối chiếu 12 AC) + cập nhật `implementation/README.md`
- [ ] F6. Cập nhật `aios/progress/LOG.md` + `PROGRESS.md` (TASK-084 done); commit; **KHÔNG push/merge PR #8** (theo yêu cầu user — sẽ update khi user quay lại)
