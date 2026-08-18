# Critique vòng 2 — TASK-086 (M12-P2: Backward Compatibility)

> Đối chiếu code thật: `plugins/contracts.py`, `extension/matrix.py` + `contracts.py`, `workflow/cli.py` (_run_simulate), `kernel/services/execution.py` + `policy.py`, `contracts/catalog.py` + `compatibility.py`, `upgrade/migration.py` + `migration_110.py`, `tests/test_architecture.py:1145-1183`, `tests/test_cli.py`, `tests/test_plugins.py`.

## Đánh giá chung

Spec v2 **3.5/5** — resolution vòng 1 (9/9) đã xác minh khả thi trên code thật (C1-01 fix AiosRange không phá test cũ — grep toàn tests; scenario 2 runtime chứng minh chạy được — test_cli.py:14-26). Còn 2 P2 tầng tích hợp.

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C2-01 | P2 | Allow-list 6 module thiếu `aios_core.workflow.cli` (scenario 2 gọi `_run_simulate` thật) — nếu import kernel/config/services sẽ phá thiết kế control plane | **RESOLVED** — Allow-list = **7 module**: + `aios_core.workflow.cli` (import adapter CLI — precedent lazy import cli.py:538); KHÔNG kéo kernel/config |
| C2-02 | P2 | `_run_simulate` in stdout multi-line → phá AC8 "JSON 1 dòng" | **RESOLVED** — Bọc `contextlib.redirect_stdout(io.StringIO())` quanh scenario 2 trong check (`contextlib` đã trong external allow-list); AC8 thêm assert stdout ngoài JSON rỗng |
| C2-03 | P3 | Thiếu YAML fixture chuẩn; `tempfile`/`os` không trong external allow-list | **RESOLVED** — YAML fixture chuẩn trong spec §3.2 (name/version/nodes type task); cơ chế tạo file: `Path.cwd() / f"_compat_wf_{uuid4().hex}.yaml"` + `try/finally: unlink()` (pathlib + uuid đã allow) |
| C2-04 | P3 | Kiểm chứng C1-01 chỉ "parse OK", thiếu round-trip giá trị | **RESOLVED** — AC6 bổ sung: `manifest.aios.compatible == ["1.0.0","1.1.0"]` sau parse (model_validate + model_dump); AC9 thêm assert `check_compatibility("2.0.0","*","1.5.0") is False` (hành vi min/max không đổi) |
| C2-05 | P3 | AC7 fail-closed khó test với CHECKS tuple cố định | **RESOLVED** — `BackwardCompatibilitySuite.__init__(checks: Sequence[BackwardCheck] | None = None)` — default CHECKS; test truyền list có 1 check raise |
| C2-06 | P3 | AC9 "≥2098" mơ hồ (không tính test mới) + scenario 2 side-effect file db trong CWD | **RESOLVED** — AC9: "0 regression so với baseline 2098 + toàn bộ test mới PASS"; §6: scenario 2 chạy kernel → trỏ audit db vào temp (Settings override) hoặc ghi chú chấp nhận |

**Kết quả: 6/6 RESOLVED — spec nâng v3 (chỉ vài dòng bổ sung). Đủ điều kiện tasks.md + review.**
