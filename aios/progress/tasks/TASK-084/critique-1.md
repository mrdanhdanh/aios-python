# Critique vòng 1 — TASK-084

> Phản biện spec TASK-084 (M12-P0 — Version & Compatibility Baseline, Issue #7)
> Đối chiếu code thật: `__init__.py`, `contracts/catalog.py`, `contracts/compatibility.py`, `plugins/compat.py`, `plugins/manager.py`, `ecosystem/marketplace.py`, `workflow/cli.py`, `upgrade/migration.py`, `extension/matrix.py`, `harness/certification/conformance.py`, `api/app.py`, `docs/PLAN.md` §M12.

## Đánh giá chung

Spec có nền tốt: mục tiêu + phạm vi In/Out rõ, AC kiểm chứng được, fail-closed được nhấn mạnh, tái sử dụng `plugins/compat.py` là quyết định đúng. Tuy nhiên có **3 vấn đề P1**: (1) mâu thuẫn version thật `0.1.0` với mốc `1.0.0` — nhảy thẳng `0.1.0 → 1.1.0` là breaking theo chính `CompatibilityChecker`; (2) bỏ sót hardcode `api/app.py`; (3) mâu thuẫn nội bộ fail-closed (WARN vs error).

**Mức sẵn sàng v1: 3/5 — cần sửa trước khi implement.**

## Các vấn đề

| Mã | Mức | Vấn đề |
|----|-----|--------|
| C1-01 | P1 | Nhảy `0.1.0 → 1.1.0` bỏ mốc `1.0.0`; `CompatibilityChecker` Rule 4 coi 0.x khác minor là breaking → trái tuyên bố "minor bump backward-compatible"; C2 migration `from_version="1.0.0"` cần mốc rõ. |
| C1-02 | P1 | Bỏ sót `api/app.py:49` hardcode `FastAPI(version="0.1.0")` — sau bump `/openapi.json` vẫn trả `0.1.0`. |
| C1-03 | P1 | §3.3 mâu thuẫn fail-closed: `DEFAULT_ENTRIES` nói "thiếu entry → WARN" vs "→ error" vs AC7. |
| C1-04 | P2 | `DEFAULT_ENTRIES` không liệt kê cụ thể; AC5 (≥4 entry) không bao phủ 10 contract → AC7 có thể "tự bắn" AC2. |
| C1-05 | P2 | `aios_min`/`aios_max` mô tả "semver" nhưng tái dùng `parse_constraint` (`.x`) — max `"1.1.0"` chặn mọi patch `1.1.x`. |
| C1-06 | P2 | `"1.0.0"` ở ~19 file src không phân loại bump/giữ; `marketplace.py` có 2 chỗ aios_version (constructor + property dòng 269). |
| C1-07 | P2 | `test_models.py:104` (`assert "0.1.0" in meta.version`) chắc chắn fail sau bump — spec không liệt kê test cụ thể. |
| C1-08 | P2 | Matrix mới là cơ chế compatibility thứ 4 — chưa tuyên bố ai tiêu thụ, tạo 2 nguồn sự thật với plugin manager/marketplace. |
| C1-09 | P2 | Rủi ro "conformance assert version 1.0" là giả định sai — AreaChecks/GS/gates không assert version; golden.py hardcode là component data. |
| C1-10 | P3 | CLI `compat check`: output "JSON/dòng" chưa chốt; `<version>` chưa rõ có đối chiếu `entry.version`. |
| C1-11 | P3 | `kind` trùng prefix `id`; lookup `(kind,id)` vs `id` đầy đủ chưa rõ. |

---

## Resolution (đã resolve — 2026-08-16, bởi AIOS Orchestrator)

| Mã | Resolution |
|----|-----------|
| C1-01 | **RESOLVED** — Bổ sung §2.1 "Version history & mapping": `0.1.0` = dev version nội bộ (chưa release), `1.0.0` = mốc release M10 (đã tồn tại trong PLAN/PR promotion), `1.1.0` = M12. C1 bump `__version__` → `"1.1.0"` trực tiếp (dev→release mốc, không cần 2 bước trong code); tuyên bố rõ `check_upgrade("0.1.0","1.1.0")` = out-of-scope (dữ liệu dev cũ không phải đường nâng cấp hỗ trợ — đường hỗ trợ chính thức là `1.0.0 → 1.1.0`). C2 sẽ dùng `from_version="1.0.0"` là mốc release chuẩn. AC3 giữ `check_upgrade("1.0.0","1.1.0")` compatible=True. |
| C1-02 | **RESOLVED** — Thêm `api/app.py` vào danh sách bump: `FastAPI(version=__version__)` (bỏ hardcode). Thêm AC: `GET /openapi.json` trả `1.1.0`. |
| C1-03 | **RESOLVED** — Chốt chính sách fail-closed: **kind/id không có trong matrix → error (không PASS)**. Bỏ chữ "WARN" khỏi mô tả `DEFAULT_ENTRIES`; `warnings` chỉ dùng cho case "version component ≠ entry.version" (C1-10). |
| C1-04 | **RESOLVED** — Liệt kê `DEFAULT_ENTRIES` cụ thể trong §3.3: 10 contract catalog (agent, capability, tool, workflow, runtime, event, artifact, plugin, model, memory — version `1.1.0`, aios_min `1.0.0`, aios_max None) + plugin mẫu (`plugin.demo` 1.0.0 / min 1.0.0) + workflow mẫu + skill mẫu. AC5 nâng: "≥ 14 entry (10 contract + 1 plugin + 1 workflow + 1 skill + 1 sdk)". |
| C1-05 | **RESOLVED** — `aios_min` = semver thuần (mốc tối thiểu); `aios_max` = constraint (hỗ trợ `.x`, mặc định `None` = không chặn). Thêm case test max `"1.1.x"` (1.1.5 compatible) vào AC6. |
| C1-06 | **RESOLVED** — Yêu cầu artifact `implementation/survey.md`: bảng phân loại `file:dòng | giá trị | loại (AIOS version → bump / component version → giữ) | lý do` cho ~19 file. Sửa CẢ 2 chỗ marketplace: `TrustChain.__init__` (dòng 85) + `MarketplaceRegistry._aios_version` (dòng 269). `upgrade/migration.py:215` + `workflow/cli.py:727` = component/sample data → giữ nguyên. |
| C1-07 | **RESOLVED** — `tasks.md` liệt kê test cần sửa: `tests/test_models.py:104` (assert "0.1.0" → "1.1.0") + mọi test assert system version; test component version (`"1.0.0"` ở harness/enterprise/tools/skills...) GIỮ NGUYÊN. AC9 bổ sung tên file test đã cập nhật. |
| C1-08 | **RESOLVED** — Thêm §3.5 "Quan hệ & tiêu thụ": trong C1 matrix là **registry tham chiếu** — chỉ CLI `compat` + test tiêu thụ; KHÔNG đổi hành vi plugin manager/marketplace (chúng vẫn dùng `check_compatibility` riêng). C2 (TASK-085) sẽ nối upgrade pipeline vào matrix; C4 (TASK-087) nối conformance. |
| C1-09 | **RESOLVED** — Sửa §6: "conformance (AreaChecks/GS/gates) KHÔNG assert system version → không cần cập nhật ngưỡng; `golden.py` hardcode `1.0.0` = component data → giữ nguyên". |
| C1-10 | **RESOLVED** — Chốt output: `compat list` = bảng text; `compat check` = JSON 1 dòng (`{"compatible": bool, "errors": [...], "warnings": [...]}` — dùng `json.dumps` như CLI hiện có). Version component ≠ `entry.version` → **warning, không chặn**. |
| C1-11 | **RESOLVED** — Chốt: `id` KHÔNG prefix loại (vd `"demo"`), lookup theo cặp `(kind, id)` chuẩn hóa lowercase; sửa ví dụ §3.3 + §4 cho khớp CLI input `<kind> <id> <version>`. |

**Kết quả: 11/11 RESOLVED — spec nâng lên v2. Đủ điều kiện chạy critique vòng 2.**
