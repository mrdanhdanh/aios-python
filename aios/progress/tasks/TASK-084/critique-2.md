# Critique vòng 2 — TASK-084

> Phản biện SPEC v2 (đã tích hợp resolution critique-1 11/11)
> Đối chiếu code thật: `plugins/compat.py`, `ecosystem/marketplace.py`, `api/app.py`, `upgrade/`, `workflow/cli.py`, `contracts/catalog.py`, `contracts/check.py`, `contracts/compatibility.py`, `observability/arch_health.py`, `tests/test_architecture.py`, `tests/test_contracts_catalog.py`, `tests/test_models.py`, `tests/test_ecosystem_devkit.py`, `tests/test_policy.py`

## Đánh giá chung

Spec v2 xử lý tốt 11/11 vòng 1 — đã xác minh từng resolution trên code thật:
- **C1-05 khả thi THẬT**: `parse_constraint("1.1.x")` → `Constraint(major=1, minor=1, patch=None)`; `check_compatibility("1.0.0","1.1.x","1.1.5")` → True; `("1.0.0","1.1.x","2.0.0")` → False. KHÔNG có lỗ hổng P1 ở đó.
- **C1-02 đúng**: `api/app.py:49` hardcode thật; `version=__version__` khả thi (precedent `cli/system.py:10`).
- **C1-04 đúng**: catalog đúng 10 contract, id khớp danh sách §3.3.
- **C1-06 đúng**: marketplace có ĐÚNG 2 chỗ hardcode (`TrustChain.__init__` ~85 + `MarketplaceRegistry._aios_version` ~269).
- **AC3 khả thi**: `check_upgrade("1.0.0","1.1.0")` → compatible=True, breaking=False.

Vòng 2 phát hiện **1 lỗ hổng P1** (import allow-list INV của `upgrade/`) + 3 vấn đề P2 + 3 P3.

**Mức sẵn sàng v2: 3/5 — cần sửa trước khi implement.**

## Các vấn đề

### C2-01 — `upgrade/compatibility.py` import `plugins/compat.py` sẽ FAIL `test_inv_upgrade_import_allowlist` (P1)
- **Vị trí**: §3.3 ("Tái sử dụng `plugins/compat.py`") + §7 bước 6.
- **Vấn đề**: `tests/test_architecture.py:1145-1181` — `_UPGRADE_ALLOWED_AIOS = {aios_core.contracts, aios_core.semver, aios_core.kernel.events, aios_core.skills.errors}`. Module mới `upgrade/compatibility.py` import `from ..plugins.compat import ...` → `aios_core.plugins` KHÔNG trong allow-list → FAIL. Đây là test INV (TASK-020 control plane) — spec v2 không liệt kê việc sửa allow-list.
- **Đề xuất**: bổ sung `aios_core.plugins.compat` vào `_UPGRADE_ALLOWED_AIOS` kèm comment lý do (style giống hiện có), ghi rõ trong `tasks.md` + `survey.md`; HOẶC đặt module ở nơi không tạo import chéo.

### C2-02 — §4 ví dụ `contract agent --aios-version 2.0.0` mâu thuẫn DEFAULT_ENTRIES (P2)
- **Vấn đề**: entry `contract/agent` có `aios_max=None` → `--aios-version 2.0.0` compatible → exit 0. Nhưng §4 ghi "ngoài range → error → exit 1". Chỉ entry `workflow/demo_flow` (max `"1.1.x"`) kích hoạt được case này.
- **Đề xuất**: sửa §4 thành `compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` → error exit 1 (khớp AC8).

### C2-03 — AC9 liệt kê test thiếu — `test_cli_contract_list` chắc chắn fail sau bump catalog (P2)
- **Vấn đề**: `tests/test_contracts_catalog.py:200-203` `test_cli_contract_list` assert `"1.0.0" in out` trên output thật → sau bump lên `1.1.0` → FAIL. Spec không liệt kê.
- **Đề xuất**: thêm vào AC9; quét `backend/tests` lần cuối (189 match ở 47 file — đa số fixture component → giữ; chỉ sửa assert SYSTEM version).

### C2-04 — Khảo sát §3.1 thiếu 2 file "0.1.0": `ecosystem/devkit.py` + `kernel/services/policy.py` (P2)
- **Vấn đề**: `ecosystem/devkit.py:34,108` (`version = "0.1.0"` scaffold template) + `kernel/services/policy.py:17` (`DEFAULT_POLICY_VERSION = "0.1.0"`) — KHÔNG xuất hiện trong danh sách §3.1 → nguy cơ bỏ sót/bump nhầm. Test liên quan: `test_ecosystem_devkit.py:31`, `test_policy.py:71` — phải GIỮ.
- **Đề xuất**: thêm 2 file vào bảng survey với loại = **component version → giữ nguyên** + lý do.

### C2-05 — Spec phải pin API reuse: cấm `Constraint.matches()`, chốt `aios_max=None → "*"` (P2)
- **Vấn đề**: `Constraint.matches()` có semantics exact-match (patch null → chỉ so major/minor, KHÔNG min-floor), trong khi `_within_min`/`_within_max` (dùng bởi `check_compatibility`) mới là min/max đúng. Dùng nhầm → mọi aios > 1.0.0 bị TỪ CHỐI. `check_compatibility` yêu cầu max là string — `None` phải map `"*"`.
- **Đề xuất**: ghi rõ §3.3: "BẮT BUỘC gọi `check_compatibility(aios_min, aios_max or "*", aios_version)`; KHÔNG dùng `Constraint.matches()`".

### C2-06 — "JSON 1 dòng như CLI hiện có" sai dữ kiện (P3)
- **Vấn đề**: CLI thật MỌI output JSON dùng `print(json.dumps(out, indent=2))`. Không có precedent "1 dòng".
- **Đề xuất**: chốt JSON không indent (1 dòng — máy parse); test phải `json.loads` output, không so chuỗi chính xác.

### C2-07 — AC6 "aios_min > 1.1.0" không kích hoạt được qua CLI (P3)
- **Vấn đề**: mọi entry min=1.0.0 → case out-of-range chỉ trigger bằng `--aios-version < 1.0.0` (vd 0.9.0) hoặc entry max "1.1.x" + `--aios-version 2.0.0`.
- **Đề xuất**: viết lại AC6 vector cụ thể: `compat check contract agent 1.0.0 --aios-version 0.9.0` → error exit 1 (aios_min) và `compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` → error exit 1 (aios_max).

### C2-08 — §3.5 sai dữ kiện: marketplace KHÔNG dùng `check_compatibility` (P3)
- **Vấn đề**: chỉ `plugins/manager.py:187,232` dùng `check_compatibility`; `TrustChain` dùng `_in_range` tự viết — với max `"1.1.x"` chỉ check major → coi "1.1.x" như "1.x" (aios 1.5.0 PASS). Divergence semantics.
- **Đề xuất**: sửa câu chữ §3.5 đúng thực tế + ghi divergence là known-issue cho TASK-085/086.

---

## Resolution (đã resolve — 2026-08-16, bởi AIOS Orchestrator)

| Mã | Resolution |
|----|-----------|
| C2-01 | **RESOLVED** — Giữ module `upgrade/compatibility.py`; **thêm `aios_core.plugins.compat` vào `_UPGRADE_ALLOWED_AIOS`** trong `tests/test_architecture.py` (kèm comment lý do — style giống entry hiện có; đây là mở rộng deliberate của upgrade package: matrix tái sử dụng parser compat đã tồn tại, không viết lại semver). Ghi vào §7 bước 2.5 + tasks.md + survey.md. AC9 phủ. |
| C2-02 | **RESOLVED** — §4 sửa hàng cuối: `compat check workflow demo_flow 1.0.0 --aios-version 2.0.0` → error exit 1. |
| C2-03 | **RESOLVED** — AC9 bổ sung `tests/test_contracts_catalog.py::test_cli_contract_list` (assert "1.0.0" → "1.1.0"). |
| C2-04 | **RESOLVED** — Survey bổ sung: `ecosystem/devkit.py:34,108` + `kernel/services/policy.py:17` = **component version → giữ nguyên** (devkit = scaffold riêng; policy = version schema policy). AC9 xác nhận `test_ecosystem_devkit.py`/`test_policy.py` KHÔNG bị sửa. |
| C2-05 | **RESOLVED** — §3.3 chốt: "BẮT BUỘC gọi `check_compatibility(aios_min, aios_max or "*", aios_version)`; KHÔNG dùng `Constraint.matches()`" + test negative aios 0.9.0. |
| C2-06 | **RESOLVED** — Chốt JSON **không indent** (1 dòng, máy parse); test dùng `json.loads`. |
| C2-07 | **RESOLVED** — AC6 viết lại vector: `--aios-version 0.9.0` → error (aios_min) + `workflow demo_flow --aios-version 2.0.0` → error (aios_max); thêm case `--aios-version 1.1.5` với `workflow demo_flow` → compatible (max "1.1.x"). |
| C2-08 | **RESOLVED** — §3.5 sửa câu chữ: "plugin manager dùng `check_compatibility`; marketplace `TrustChain` dùng `_in_range` riêng (semantics lỏng hơn — known divergence, ghi nhận cho TASK-085/086)". |

**Kết quả: 8/8 RESOLVED — spec nâng lên v3. Đủ điều kiện viết tasks.md + review.**
