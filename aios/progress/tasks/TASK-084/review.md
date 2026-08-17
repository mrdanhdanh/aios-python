# Review — TASK-084 (Pre-implementation Review)

> Task: **TASK-084 — M12-P0: Version & Compatibility Baseline (C1)** — Issue #7
> Spec: v3 (12 AC, tích hợp critique-1 11/11 + critique-2 8/8) | Nhánh: `feature/ISSUE-7-aios-1-1-compatibility`
> Reviewer: AIOS Reviewer | Ngày: 2026-08-16

## Tổng quan

C1 bump hệ thống AIOS `0.1.0 → 1.1.0` đồng bộ (package `__version__`, API app, 10 contract catalog, plugin manager, marketplace — 2 chỗ) + tạo Compatibility Matrix registry mới (`upgrade/compatibility.py`) + CLI `aiagent compat list/check` với chính sách fail-closed, tái sử dụng `check_compatibility()` từ `plugins/compat.py`.

**Kết quả đối chiếu code thật: mọi claim trong spec v3 đều khớp 100%** — từng file:line, giá trị, hành vi semantics (đã đọc trực tiếp `plugins/compat.py`, `ecosystem/marketplace.py`, `contracts/catalog.py`, `contracts/compatibility.py`, `workflow/cli.py`, `tests/test_architecture.py`, `tests/test_models.py`, `tests/test_contracts_catalog.py`, `cli/system.py`, `observability/arch_scan.py`). Không phát hiện mâu thuẫn nào giữa spec và thực tế code.

## Đối chiếu AC (đo được — pre-implement)

- [x] **AC1**: `__version__` (dòng 3 hiện `"0.1.0"`) → `"1.1.0"`; `cli/system.py:10,16` đọc `__version__` → `system status` tự phản ánh.
- [x] **AC2**: Catalog đúng 10 contract `version="1.0.0"` (dòng 98–180) → bump 10 chỗ; `_contract_list()` in cột version từ catalog → tự phản ánh. `deprecated_in="1.0.0"` giữ nguyên (R3 — vì `test_cli_contract_check_full_has_warnings` phụ thuộc plugin còn deprecated).
- [x] **AC3**: `check_upgrade("1.0.0","1.1.0")` → `compatible=True, breaking=False` (Rule 4/5) — xác minh logic khả thi.
- [x] **AC4**: `manager.py:68` + marketplace 2 chỗ (`TrustChain.__init__` ~85, property `_aios_version` ~268) — 3 vị trí xác nhận tồn tại.
- [x] **AC5**: `DEFAULT_ENTRIES` = 14 entry (10 contract id khớp catalog + plugin/demo + workflow/demo_flow + skill/agent-sprite-forge + sdk/python).
- [x] **AC6**: 3 vector kích hoạt được thật (verify `_within_min`/`_within_max`): `0.9.0` fail min, `2.0.0` fail max `"1.1.x"`, `1.1.5` pass.
- [x] **AC7**: kind/id lạ → error (fail-closed, hết mâu thuẫn WARN/error).
- [x] **AC8**: `--aios-version` override — cơ chế giống `_contract_check` hiện có; vector 2.0.0 vs `1.1.x` khả thi.
- [x] **AC9**: baseline **2052 pass = khớp STATS.md M11**; 2 test fail chắc chắn đã liệt kê đúng; allow-list fix bắt buộc đã ghi rõ (C2-01).
- [x] **AC10**: không thêm invariant; không đổi hành vi runtime (chỉ default literal).
- [x] **AC11**: `api/app.py:49` hardcode xác nhận → `version=__version__` (precedent `cli/system.py:10`).
- [x] **AC12**: CLI pattern if-chain `args.command == ...` đã xác minh; thêm `compat` khớp hoàn toàn.

## Vấn đề phát hiện

### R1 — Case `contract agent 1.0.0 --aios-version 0.9.0` sẽ kèm warnings (version ≠ entry.version) (Minor)
- Entry `contract/agent` version `1.1.0` nhưng CLI truyền `1.0.0` → warning song song với error aios_min. Test phải assert qua `json.loads` cả `errors` + `warnings`.

### R2 — Đổi default `aios_version` thành `from .. import __version__` sẽ FAIL allow-list (Minor — cảnh báo)
- `collect_imports` resolve relative import `..` → root `aios_core`, không nằm trong `_UPGRADE_ALLOWED_AIOS` → FAIL. **Chốt: giữ literal `"1.1.0"` trong `check()` default.**

### R3 — Lý do giữ `deprecated_in="1.0.0"` cần vào spec §3.2 + survey.md (Minor)
- Bump `deprecated_in` lên `1.1.0` sẽ làm plugin hết deprecated → `test_cli_contract_check_full_has_warnings` FAIL.

### R4 — Hành vi `<version>` không parse được (vd `abc`) chưa chốt (Minor)
- Chốt: error → exit 1 (fail-closed), test 1 case.

## Kết luận

- [x] **APPROVED CÓ ĐIỀU KIỆN** — sẵn sàng implement, không còn blocking
- Điều kiện (Minor, áp dụng trong lúc implement): R1 (test assert cả errors+warnings), R2 (KHÔNG import `__version__` trong upgrade/compatibility.py — giữ literal), R3 (ghi lý do deprecated_in vào spec §3.2 + survey.md), R4 (version rác → error exit 1 + test)
