# Critique vòng 1 — TASK-085 (M12-P1: Migration 1.0→1.1 thật, Issue #7)

> Đối chiếu code thật: `upgrade/migration.py`, `upgrade/pipeline.py`, `upgrade/backup.py`, `upgrade/compatibility.py` (TASK-084), `workflow/cli.py` (migrate), `tests/test_migration.py`, `tests/test_upgrade_cli.py`, `tests/test_architecture.py:1145`.

## Đánh giá chung

Mức sẵn sàng v1: **2/5**. Nhiều điểm thiết kế không khả thi/sai lệch code thật. Các xác minh ĐÚNG của spec: `MigrationStep.kind` không chặn `contract`; CLI rẽ nhánh 1.0.0→1.1.0 không đụng test cũ; allow-list đã có `plugins.compat` + `contracts`; `dry_run` không gọi fn; journal idempotent.

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C1-01 | P1 | `MigrationEngine.apply` gọi `self._backup.backup(f"migration:...")` sai signature (1 arg vs 4 arg) → TypeError khi inject backup; `apply` không trả backup_id | **RESOLVED** — `Aios110Migrator.apply` tự gọi `BackupStore.backup(kind, component_id, version, payload)` TRƯỚC `engine.apply`, giữ backup_id và trả trong kết quả; SỬA BUG `engine.apply`: bỏ đoạn call sai (caller chịu trách nhiệm backup) + test hồi quy |
| C1-02 | P1 | Pre-check "component ngoài range [1.0.0,1.1.0]" không khả thi: matrix chỉ fail khi aios_version hằng ngoài range; kind `config` không có trong ComponentKind → matrix.check("config") luôn fail | **RESOLVED** — 2 tầng: (a) range check bằng `semver.compare(payload_version, "1.0.0") >= 0 and compare(payload_version, "1.1.0") <= 0`; (b) matrix check chỉ cho kind/id có entry; kind config = skip matrix (ghi policy) |
| C1-03 | P1 | Stub CLI cũ `{"id": "p"}` không có entry matrix → pre-check fail; CLI cũ bỏ qua `--input` | **RESOLVED** — Stub 1.1 khớp matrix: plugin `{"id":"demo",...}`, workflow `{"name":"demo_flow","version":"1.0.0",...}`; nhánh mới ĐỌC `--input` nếu cấp (JSON file), ngược lại dùng stub |
| C1-04 | P1 | Transform workflow nhắm `definition.version` nhưng dữ liệu thật là `version` top-level (WorkflowDefinition) | **RESOLVED** — bump `data["version"]` top-level 1.0.0→1.1.0; stub workflow đúng model (name/version/nodes có type) |
| C1-05 | P1 | `aios.compatible = [min,"1.1.0"]` xung đột quy ước v0→v1 (`compatible = [min]` — test_migration.py:169) | **RESOLVED** — Chuẩn 1.1: `compatible = [min, max]` (range 2 phần tử); KHÔNG sửa `plugin_v0_to_v1` cũ (giữ test cũ); ghi divergence trong survey/notes |
| C1-06 | P2 | Post-check vô hiệu (plugin không đổi version → post = pre) | **RESOLVED** — Post-check = assertion thật trên payload: workflow/contract `version == "1.1.0"`, plugin `"1.1.0" in aios.compatible`, config no-op + matrix check |
| C1-07 | P2 | Rollback không biết giá trị do transform ghi → đảo sai | **RESOLVED** — Rollback guard: chỉ đảo khi giá trị hiện tại == giá trị transform ghi (compatible == [min,"1.1.0"] mới xóa; version == "1.1.0" mới hạ) |
| C1-08 | P2 | Shallow copy trong engine → nested mutate hỏng payload gốc | **RESOLVED** — MỌI transform 110 deep-copy input (json round-trip — KHÔNG import copy, C1-14); test "input không mutate" cho cả 4 |
| C1-09 | P2 | Return type apply mơ hồ | **RESOLVED** — Dataclass `Aios110Result`: `{payload, backup_id, journal_status, matrix: {pre, post}}` — dùng chung dry_run/apply/rollback |
| C1-10 | P2 | Fail case "payload ngoài range" không reachable; AC5 sai cơ chế | **RESOLVED** — AC5 đổi: "payload có id không có entry matrix (plugin/p, workflow không demo_flow) → từ chối, journal không start" |
| C1-11 | P2 | "Dữ liệu thật" mơ hồ: không write-back, component_id không rõ | **RESOLVED** — Phạm vi C2 = **luồng thật, dữ liệu demo**: journal SQLite + backup snapshot + CLI output; KHÔNG write-back persistence. component_id: plugin/contract `data["id"]`, workflow `data["name"]`, config `"config"` |
| C1-12 | P3 | `PLANS_110["bogus"]` KeyError | **RESOLVED** — `PLANS_110.get(kind)` + lỗi rõ ràng exit 1; giữ yêu cầu chọn `--dry-run`/`--apply` |
| C1-13 | P3 | Config transform "ghi metadata" không định nghĩa | **RESOLVED** — Config: thêm `data["migration"] = {"from": "1.0.0", "to": "1.1.0"}` nếu chưa có; rollback xóa nếu đúng giá trị; AC6 per-kind |
| C1-14 | P3 | `import copy` không nằm trong `_UPGRADE_ALLOWED_EXTERNAL` | **RESOLVED** — Deep copy bằng json round-trip (đã allow); import `AIOS_VERSION` từ `upgrade.compatibility` (internal) thay vì hardcode "1.1.0" |
| C1-15 | P3 | Baseline 2071 cần verify lại; journal thật bị ghi khi test CLI | **RESOLVED** — Verify baseline ngay trước implement; test CLI mới luôn truyền `--journal` vào tmp_path |

**Kết quả: 15/15 RESOLVED — spec nâng v2. Đủ điều kiện critique vòng 2.**
