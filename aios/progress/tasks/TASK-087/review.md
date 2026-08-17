# Review — TASK-087 (M12-P3: Compatibility Conformance C4)

> Reviewer: AIOS Reviewer — trước khi implement. Đối chiếu spec v3 (8 AC) + tasks.md + code thật.
> Ngày: 2026-08-16

## Tổng quan

Task mở rộng `aiagent conformance` cho AIOS 1.1 Compatibility: thêm area `compatibility` (structural — CompatibilityMatrix + BackwardCompatibilitySuite + version) vào `AreaChecks.run_all()` (10→11), thêm gate `gate_g_compatibility` vào `release_gates()` (6→7), bump format `"AIOS Conformance 1.0"`/`"AIOS 1.0 READY"` → `"AIOS Conformance 1.1"`/`"AIOS 1.1 READY"`, cập nhật help CLI + test cũ. KHÔNG phá 10 areas/6 gates hiện có.

Spec v3 đã tích hợp 7/7 (critique-1) + 6/6 (critique-2). **Tôi đối chiếu lại toàn bộ resolution bằng code thật — tất cả đều đúng, không còn mâu thuẫn sót.** Mức sẵn sàng: **4.5/5**.

## Đối chiếu tiêu chí chấp nhận (đo được không?)

- [x] **AC1** — đo được ✅. Precedent `verification()` dùng string `"verification"` (checks.py:186); enum `CertificationArea` giữ 9 giá trị (contracts.py:16-26) → `test_9_areas` không đổi. `run_all()` hardcode 10 method (checks.py:190-195) — thêm `compatibility()` là 11.
- [x] **AC2** — đo được ✅. `__version__ = "1.1.0"` (aios_core/__init__.py:4); `CompatibilityMatrix().list()` ≥ 14 entry mặc định (compatibility.py:54-55); `BackwardCompatibilitySuite` có **đúng 9 CHECKS** (backward_compat.py:206-235) → evidence "verify=9/9" khớp thực tế, `report.ok` + `report.results[].ok` đúng spec 3.1. Test assert cả 3 số liệu trong evidence.
- [x] **AC3** — đo được ✅. `compatibility()` import function-local (`from ...upgrade.backward_compat import ...`) → mỗi lần gọi re-getattr → monkeypatch attribute trên module nguồn `aios_core.upgrade.backward_compat.BackwardCompatibilitySuite` sẽ có hiệu lực (precedent: `test_gate_b_high_fail_blocks` patch `sec.SecurityChecker`). FakeSuite trả `ok=False` → area FAIL, fail-closed. **Lưu ý: KHÔNG patch `checks.BackwardCompatibilitySuite` (không tồn tại — import function-local)** → R3-1.
- [x] **AC4** — đo được ✅. Grep toàn repo: `release_gates` chỉ có **2 caller, cả 2 no-arg** (conformance.py:102, test_certification.py:69) → đổi signature `areas: list[AreaResult] | None = None` **không phá caller nào**. "KHÔNG double-run" testable bằng call-counter trên Suite/AreaChecks. Branch exception → False trivially thỏa (compatibility() tự catch → FAIL result → gate False). Fail-closed khi areas thiếu `compatibility` → gate False (đúng thiết kế).
- [x] **AC5** — đo được ✅. `run()` → 11 areas (run_all) + 20 GS + 7 gates; `test_gate_definitions` (test_certification.py:69-77) assert set 6 gates + `all(gates.values())` → cập nhật 7 gates; 10 areas/6 gates cũ không regression.
- [x] **AC6** — đo được ✅. `_conformance()` = `return 0 if report.ready else 1` (cli.py:847) → exit 0 **thực sự phụ thuộc** compat area + gate G PASS thật (TASK-084/086 đã done nên hợp lệ). Help `cli.py:111` "10 areas + 6 gates" → "11 areas + 7 gates". Header `"AIOS Conformance 1.0"` (conformance.py:117) + result `"AIOS 1.0 READY"` (conformance.py:130) → 1.1.
- [x] **AC7** — đo được ✅. Baseline **2109 PASS** đúng (PROGRESS.md:15, TASK-086). Test mới + cập nhật → ≥ 2109.
- [x] **AC8** — đo được ✅. **Tôi đã chạy `test_inv017_harness_import_allowlist` → PASS (1 passed)**. Lý do: `collect_imports` resolve relative import với off-by-one (module_rel gồm cả tên module) → import từ `certification/checks.py` resolve thành `aios_core.harness.*` → bị filter khỏi `aios_mods`. **Kiểm chứng ngược**: absolute `from aios_core import __version__` → `aios_core` KHÔNG trong `_HARNESS_ALLOWED_AIOS` (test_architecture.py:651-657) → **vi phạm thật** → ràng buộc C2-01 "CHỈ relative import" là BẮT BUỘC, spec đúng. Không thêm invariant; INV-001..035 giữ nguyên.

## Vấn đề phát hiện

### R2-1 — tasks.md B3 thiếu docstring cli.py:842 + contracts.py:66 (Major: nên sửa)

Resolution C2-03 cam kết: *"cập nhật cli.py:111 (bắt buộc) + các docstring"* — critique-2 nêu rõ 4 chỗ: cli.py:111, **cli.py:842**, checks.py "9 area checks", **contracts.py:66**. tasks.md A2/B2 đã cover checks.py + conformance.py, B3 chỉ ghi cli.py:111 → **cli.py:842** (`"""AIOS conformance — 10 areas + 20 GS + 6 release gates (M10 + M11)."""`) và **contracts.py:66** (docstring `ready`: "AIOS 1.0 READY chỉ khi...") **chưa vào checklist**. Không phá test nhưng lệch cam kết critique. → Thêm vào B3: `cli.py:842 docstring + contracts.py:66 docstring → 11 areas/7 gates/1.1`.

### R3-1 — tasks.md C2 chưa nêu target monkeypatch AC3 (Minor)

Ghi rõ: patch `aios_core.upgrade.backward_compat.BackwardCompatibilitySuite` (module nguồn — import function-local nên re-getattr mỗi lần gọi), dùng `monkeypatch.setattr`. Tránh nhầm patch `checks.BackwardCompatibilitySuite` (không tồn tại).

### R3-2 — conformance.py:1 module docstring đã stale từ M11 (Minor)

`"""... conformance runner + 5 release gates (M10-F5)."""` — đã sai từ M11 (6 gates), task này thành 7. Nhân tiện sửa trong B2 (đang cover "docstring").

### Điểm cần lưu ý khi implement (không phải vấn đề)

- `conformance.py` cần thêm `AreaResult` vào import từ `.contracts` (hiện chỉ import `ConformanceReport, GoldenScenario, PassFail`) cho annotation `list[AreaResult] | None`.
- 2 assert "AIOS 1.0 READY" nằm đúng tại test_certification.py **:120** (test_cli_conformance) và **:128** (test_format_conformance) — grep xác nhận, spec ghi đúng. Ngoài ra không còn nơi nào khác trong code/test assert chuỗi này (các nơi còn lại là progress docs lịch sử — không sửa).
- `test_cli_conformance` còn assert `"gate_a_architecture" in out` (không đổi) — không ảnh hưởng.
- `test_all_areas_pass`/`test_ready_requires_all`/`test_gate_definitions`/`test_cli_conformance` sẽ chạy compat verify thật nhiều lần (suite 9 check, trong đó 1 check simulate) — chấp nhận theo risk table; TASK-086 đã redirect stdout.

## Chất lượng tổng thể

- Đúng spec: **có** (mọi resolution C1/C2 kiểm chứng lại bằng code thật + chạy test INV-017)
- Test phủ: **đủ** (area PASS/FAIL + gate reuse/standalone + CLI + help + không regression)
- Code sạch: **tốt** (thiết kế reuse areas precomputed, fail-closed, không double-run)

## Kết luận

- [x] **APPROVED CÓ ĐIỀU KIỆN** — không có R1 (blocking). Điều kiện:
  - Bổ sung R2-1 vào tasks.md B3 trước/khi implement (cli.py:842 + contracts.py:66 docstring)
  - Lưu ý R3-1 (monkeypatch target) + R3-2 (module docstring) khi implement
