# Critique vòng 1 — TASK-087 (M12-P3: Compatibility Conformance)

> Đối chiếu code thật: `harness/certification/{contracts,checks,conformance}.py`, `upgrade/{compatibility,backward_compat}.py`, `tests/test_certification.py`.

## Đánh giá chung

Mức sẵn sàng v1: **2.5/5**. Khảo sát code thật cho thấy vài giả định của spec SAI: `AreaChecks.run_all()` HARDCODE danh sách (không dynamic); `CertificationArea` enum chỉ có 9 giá trị — M11 thêm area `verification` bằng STRING trực tiếp (không thêm enum); `format_conformance` in "AIOS 1.0 READY".

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C1-01 | P1 | `AreaChecks.run_all()` hardcode danh sách 10 method (checks.py:190-195) — thêm area compatibility phải sửa CẢ list (không tự động) | **RESOLVED** — Thêm `self.compatibility()` vào cuối `run_all()` (11 items) |
| C1-02 | P1 | `CertificationArea` enum KHÔNG có `verification` (M11 precedent: area check dùng string trực tiếp, enum giữ 9) — spec AC1 yêu cầu thêm enum sẽ lệch precedent + phá `test_9_areas` (assert 9 giá trị) | **RESOLVED** — KHÔNG thêm enum; `AreaChecks.compatibility()` dùng string `"compatibility"` như precedent `"verification"`; `test_9_areas` KHÔNG đổi |
| C1-03 | P1 | `test_certification.py::test_gate_definitions` assert ĐÚNG 6 gates (A–F) — thêm gate G phải cập nhật test này (nếu không full suite FAIL) | **RESOLVED** — Cập nhật `test_gate_definitions` assert 7 gates (A–G) — bump chủ động cùng PR |
| C1-04 | P2 | `format_conformance` in `"Result: AIOS 1.0 READY"` — chưa phản ánh 1.1 | **RESOLVED** — Đổi thành `"AIOS 1.1 READY"` (thuộc C4 — conformance version) |
| C1-05 | P2 | Area check phải dùng component thật (R1 M10 — không hardcode PASS) — spec chưa nói evidence | **RESOLVED** — `compatibility()`: chạy `CompatibilityMatrix().list()` (≥ 14) + `BackwardCompatibilitySuite().run()` (9/9) + `__version__ == "1.1.0"`; exception → FAIL kèm str(exc) |
| C1-06 | P3 | Gate G nên đồng bộ với area (không duplicate logic) | **RESOLVED** — `gate_g_compatibility` = `AreaChecks.compatibility()` PASS + verify ok (gọi component thật, fail-closed exception → False) |
| C1-07 | P3 | CLI conformance test cũ có thể assert "AIOS 1.0 READY" | **RESOLVED** — Grep test; cập nhật assert sang 1.1 nếu có |

**Kết quả: 7/7 RESOLVED — spec nâng v2. Đủ điều kiện critique vòng 2.**
