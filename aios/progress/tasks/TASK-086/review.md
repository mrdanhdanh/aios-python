# Review — TASK-086 (M12-P2: Backward Compatibility v0→v1 trên 1.1 — Issue #7)

> Review TRƯỚC implement — đối chiếu spec v3 (10 AC) + tasks.md với code thật trên nhánh `feature/ISSUE-7-aios-1-1-compatibility`. Module `upgrade/backward_compat.py` chưa tồn tại (xác nhận bằng listing) — đúng trạng thái.

## Tổng quan

Task xây dựng **bộ test chéo cũ→mới** (9 check, 5 kind) chạy trên runtime 1.1.0 qua module mới `upgrade/backward_compat.py` + CLI `aiagent compat verify`, kèm 1 fix parse-only: thêm `compatible: list[str]` vào `AiosRange` (lỗ hổng thật do TASK-085 `migrate_plugin_100_110` tạo ra — append `"1.1.0"` vào `aios.compatible` mà `AiosRange` hiện `extra="forbid"` không có field này → `PluginManifest` sẽ raise ValidationError).

Spec v3 khớp code thật ở mức cao: mọi signature/API được viện dẫn (đã xác minh từng cái, chi tiết bên dưới). Còn 1 mâu thuẫn chưa ai phát hiện (R1 — `io` không trong external allow-list) + 1 quyết định thiết kế nên làm rõ (R2 — BaseException).

## Đối chiếu tiêu chí chấp nhận

*(Đánh giá khả năng đo — chưa chạy test vì chưa implement)*

- [x] AC1 (9 check, 5 kind): **đo được** — danh sách 9 scenario cố định, kind đếm được qua `len(CHECKS)` + set kind. Khớp kind phân bổ workflow×2/plugin×2/contract×2/extension×1/migrated×2.
- [x] AC2 (workflow-v0-parse): **đo được** — verified `WorkflowDefinition` (definition.py:38-63): `extra="forbid"`, node thiếu `timeout_s` → default `None` → hợp lệ; `version "0.1.0"` qua `parse_version` OK (test_cli.py:14-26 dùng YAML version 0.1.0 chạy thật PASS); `nodes min_length=1`, `validate_dag` OK với 1 node không dep; `type="task"` = `PlanNodeType.TASK` (execution_plan.py:14); `MockCompiler.compile` (compiler.py:30-50) merge `timeout_s` node→definition 300.0 OK.
- [x] AC3 (plugin-v0-load): **đo được** — verified `PluginManifest.validate_manifest(**fixture)` (contracts.py:83-99): id/name/version/deps/permissions đều pass; `AiosRange(min="1.0.0",max="*")` là string thuần — pass ngay cả không qua `validate_range`. `check_compatibility("1.0.0","*","1.1.0")` (compat.py:95-99): 1.1.0 ∈ [1.0.0, *] → **True** (đã trace `_within_min/_within_max`).
- [x] AC4 (contract-v0-compat): **đo được** — verified `is_compatible("1.1.0","1.0.0")` → True (compatibility.py rule 2: required không mới hơn; rule 3: major bằng nhau); `check_upgrade("1.0.0","1.1.0").compatible` → True.
- [x] AC5 (extension-v0-matrix 2 chiều): **đo được** — verified `assert_namespace_allowed(namespace: ApiNamespace|str, allowed)` (matrix.py:96-103) nhận string; `"extension"` ∈ ALLOWED → PASS; `"internal"` ∉ → raise `CompatibilityViolation` → runner bắt → check FAIL. ApiNamespace có EXTENSION/INTERNAL (extension/contracts.py:17-21) khớp 4 namespace M8.
- [x] AC6 (migrated-110-data + round-trip): **đo được** — sau fix C1-01, `PluginManifest.model_validate` giữ `aios.compatible == ["1.0.0","1.1.0"]` qua `model_dump` (list[str] không bị biến đổi); workflow v1.1.0 + contract v1.1.0 parse OK.
- [x] AC7 (fail-closed với Suite(checks=...)): **khả thi** — `__init__(checks: Sequence[BackwardCheck] | None = None)` (C2-05) cho phép test inject 1 check raise; runner bắt → `(False, str(exc))`; "check khác vẫn chạy" đo bằng cách assert results chứa cả 2. ⚠️ Phần "CLI exit 1" **chưa rõ cơ chế test** — CLI luôn chạy CHECKS mặc định, không inject được checks → phải monkeypatch `BackwardCompatibilitySuite.run()` trả report ok=False rồi `main(["compat","verify"])` → exit 1 (xem R3-1). ⚠️ Loại exception bắt: xem R2.
- [x] AC8 (CLI stdout rỗng ngoài JSON): **đo được bằng capsys** — `out = capsys.readouterr().out` → assert `out.strip()` == đúng 1 dòng JSON. Điều kiện tiên quyết: `redirect_stdout(io.StringIO())` phải nằm **TRONG check scenario 2** (spec §3.1 đã ghi đúng) thì suite silent. `main()` chỉ `reconfigure` stdout (không ghi). `compat list/check` không bị phá: subparser `verify` thêm cùng cấp với list/check (cli.py:198-206) + dispatch thêm 1 nhánh if (pattern sẵn có dòng 301-304).
- [x] AC9 (0 regression baseline 2098 + fix parse-only): **có nguồn** — baseline 2098 verified trong PROGRESS.md dòng TASK-085 ✅. Fix C1-01 verified **không phá test cũ**: không test nào assert set field của `AiosRange`; `test_manifest_extra_forbidden` (test_plugins.py:294-298) dùng unknown field **top-level** → vẫn reject; MANIFEST_BASE aios {"min","max"} parse OK với default mới; test_migration_110.py chỉ test transform ở mức dict (không parse qua model) → không ảnh hưởng. `check_compatibility("2.0.0","*","1.5.0")` → **False** (1.5.0 < 2.0.0 — đã trace) — assert "min/max không đổi" hợp lệ.
- [x] AC10 (arch-health + doctor): **đo được** — ngoại trừ R1 bên dưới (io) sẽ làm FAIL allow-list test nếu không xử lý.

## Vấn đề phát hiện

### R1 — `io` không nằm trong `_UPGRADE_ALLOWED_EXTERNAL` (Blocking: phải sửa spec trước implement)

Spec §3.1/§3.2 scenario 2 bắt buộc `contextlib.redirect_stdout(io.StringIO())` trong `upgrade/backward_compat.py`. Nhưng `collect_imports` (arch_scan.py:45-83) bắt **mọi external top-level import** của mọi file trong `upgrade/`, và `_UPGRADE_ALLOWED_EXTERNAL` (test_architecture.py:1157-1167) hiện chỉ có: `sqlite3, pathlib, contextlib, json, dataclasses, typing, datetime, uuid, collections, logging, pydantic` — **không có `io`**. Resolution C2-02 chỉ kiểm tra `contextlib`, bỏ sót `io`.

→ `import io` (hoặc `from io import StringIO`) trong backward_compat.py sẽ làm `test_inv_upgrade_import_allowlist` FAIL → AC10/E4 fail chắc chắn.

**Fix (1 trong 2, khuyến nghị làm cả 2 cho chắc):**
1. Thêm `"io"` vào `_UPGRADE_ALLOWED_EXTERNAL` kèm comment `# backward_compat.py redirect_stdout (TASK-086)` và ghi vào spec §3.4/§7 — HOẶC
2. Tránh `io` hoàn toàn: định nghĩa sink class nội bộ trong backward_compat.py, ví dụ:
   ```python
   class _NullSink:
       def write(self, s: str) -> int: return len(s)
   ```
   rồi `contextlib.redirect_stdout(_NullSink())` — không cần sửa allow-list. `contextlib`/`dataclasses`/`uuid`/`pathlib`/`typing` đều đã allow ✅.

### R2 — Runner bắt exception: nên dùng `except BaseException` (Major: nên sửa)

Spec C1-07 ghi "runner bắt mọi exception → `(False, str(exc))`". Nếu implement bằng `except Exception`, **SystemExit/KeyboardInterrupt (BaseException) lọt qua** → fail-closed không trọn vẹn. Đã verify `_run_simulate` (cli.py:1233-1257) KHÔNG raise SystemExit (chỉ `main()`/`parser.error` raise, không được gọi trong check) nên rủi ro thấp, nhưng với một suite fail-closed thì nên chặt: `except BaseException` + thêm test AC7 với 1 check raise `SystemExit` để chứng minh.

### R3-1 — Cơ chế test "CLI exit 1" của AC7 chưa rõ (Minor)

CLI `compat verify` luôn chạy CHECKS mặc định — không thể inject check fail qua CLI. Ghi rõ vào tasks.md D3: test CLI exit 1 bằng `monkeypatch` `BackwardCompatibilitySuite.run` → report ok=False → `main(["compat","verify"])` == 1. (Tiền lệ: `_compat_check` cli.py:1136-1149 trả 0/1, `sys.exit(main())` ở cuối file.)

### R3-2 — Map `_run_simulate` (trả int) → `(ok, detail)` chưa ghi trong spec (Minor)

Spec scenario 2 ghi "exit 0 (completed)" nhưng chưa ghi công thức check. Đề xuất bổ sung: `rc = _run_simulate(str(path)); return rc == 0, f"exit code {rc}"` (trong `try/finally: unlink()`). `_run_simulate` trả `0 if result.status.value == "completed" else 1` (cli.py:1257) — không raise, không in (đã bọc redirect). Audit db: **không cần làm thêm** — `_run_simulate` đã tự `Settings(audit=AuditSettings(db_path=f"{tmp}/audit.db"))` bên trong `TemporaryDirectory` (cli.py:1241-1246) — C2-06 thỏa bởi code hiện có.

### R3-3 — Typo "6 module" trong spec §7 (Minor)

§7.4 ghi "Allow-list + 6 module" nhưng §3.4 và tasks.md C1 đều là **7 module** (`workflow.definition, workflow.compiler, workflow.cli, plugins.contracts, contracts.catalog, contracts.compatibility, extension.matrix`) → sửa thành 7.

### Xác minh các mối lo khác (không phải vấn đề)

- **Allow-list 7 module có kéo import phụ?** Không — allow-list test chỉ quét file trong `upgrade/` (UPGRADE_DIR.rglob, test_architecture.py:1174-1183); `workflow.cli` top-level chỉ import argparse/json/sys/tempfile (cli.py:7-11), import nặng (config/kernel/services) đều lazy bên trong `_run_simulate` → an toàn control plane.
- **`extension.contracts` có cần thêm?** Không — scenario 7 dùng string `"extension"`/`"internal"`, `assert_namespace_allowed` nhận `str`. Nếu implementer muốn dùng `ApiNamespace` enum thì phải thêm `aios_core.extension.contracts` (module thứ 8) — lưu ý khi implement.
- **Scenario 9 khả thi** — verified `MigrationFormats` (migration.py:191-218): config → dict-check `max_duration_seconds` ✅; workflow → thêm `timeout_s=300.0` → `WorkflowDefinition.model_validate` PASS ✅; plugin → thêm `compatible=[min]` → parse PASS **sau fix C1-01** ✅. Import `..upgrade.migration` là self-import (bị loại khỏi check vì startswith `aios_core.upgrade`).
- **Scenario 6 khả thi** — `ContractDefinition` (catalog.py:39-87): id "agent" lowercase ✅, version "1.0.0" SEMVER_RE ✅, lifecycle "stable" = `ContractLifecycle.STABLE` ✅, `schema_exists()` import `aios_core.agents.base` + `Assistant` (tồn tại, agents/base.py:45) ✅.
- **`migrated-110-data` contract v1.1.0**: SEMVER_RE nhận "1.1.0" ✅.

## Chất lượng tổng thể

- Đúng spec: **Có** (v3 tích hợp 15/15 resolution critique; 1 mâu thuẫn sót: io — R1)
- Test phủ: **Đủ** — 10 AC đều map được tới test cụ thể (D1-D4 + E1-E5); mỗi scenario có fixture chuẩn trong spec §3.2
- Code sạch: **Không áp dụng** (chưa implement) — thiết kế dataclass + 9 check đơn giản, không chạm runtime ngoài fix parse-only (đúng nguyên tắc Mục tiêu 3)

## Kết luận

- [x] APPROVED CÓ ĐIỀU KIỆN — đủ điều kiện implement khi xử lý:
  - **R1 (bắt buộc trước implement)**: bổ sung `io` vào `_UPGRADE_ALLOWED_EXTERNAL` (kèm comment) HOẶC dùng sink class nội bộ thay `io.StringIO()`; cập nhật spec §3.2/§3.4/§7 cho nhất quán.
  - **R2 (trong implement)**: runner dùng `except BaseException` + test AC7 có check raise SystemExit.
  - **R3 (ghi chú implement)**: R3-1 cơ chế test CLI exit 1 (monkeypatch run()); R3-2 công thức `rc == 0 → (ok, detail)`; R3-3 sửa typo "6 module" → "7 module" (spec §7.4).
- Thứ tự implement đề xuất: A1-A2 (fix AiosRange + test) → B1-B4 (suite) — **chạy `test_inv_upgrade_import_allowlist` ngay sau B** để bắt sớm R1 → C1-C2 (allow-list + CLI) → D1-D4 (tests) → E1-E5 (verify + đóng task). Cấu trúc hiện tại hợp lý.
