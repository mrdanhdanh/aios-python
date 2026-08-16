# Critique vòng 2 — TASK-087 (M12-P3: Compatibility Conformance C4)

> Đối chiếu code thật: `harness/certification/{checks,conformance,contracts}.py`, `workflow/cli.py`, `upgrade/{compatibility,backward_compat}.py`, `tests/test_certification.py`, `tests/test_architecture.py` (INV-017), `aios_core/__init__.py`.

## Đánh giá chung

Spec v2 xử lý ĐÚNG 7/7 resolution vòng 1 (kiểm chứng code thật). Không còn P1; 1 P2 (double-run) + 5 P3. Mức sẵn sàng v2: **4/5**.

## Kiểm chứng resolution vòng 1

- C1-01 ✅ run_all hardcode 10 method
- C1-02 ✅ test_9_areas assert 9 enum; verification() dùng string
- C1-03 ✅ test_gate_definitions assert 6 gates + all(gates.values()) → gate G phải PASS thật
- C1-04 ⚠️ thiếu header "AIOS Conformance 1.0" (conformance.py:117) → C2-04
- C1-07 ✅ ĐÚNG 2 assert "AIOS 1.0 READY" (test_certification.py:120 + :128) → C2-06

## Các vấn đề + Resolution

| Mã | Mức | Vấn đề | Resolution |
|----|-----|--------|-----------|
| C2-01 | P3 | "harness không bị allow-list chặn" sai cơ chế — `from ... import __version__` an toàn nhờ resolver lọc prefix `aios_core.harness.*`; absolute import → vi phạm INV-017 | **RESOLVED** — Ghi chú triển khai: CHỈ relative import; cấm absolute `from aios_core import __version__` |
| C2-02 | P2 | Gate G chạy `compatibility()` LẦN 2 (run_all + release_gates) — 2x cost trái risk table | **RESOLVED** — `release_gates(areas: list[AreaResult] | None = None)`: khi có areas precomputed → gate G dùng status area "compatibility" (không chạy lại); khi None (test trực tiếp) → chạy component thật |
| C2-03 | P3 | Docstring/help user-facing stale: cli.py:111 ("10 areas + 6 gates"), cli.py:842, checks.py "9 area checks", contracts.py:66 | **RESOLVED** — Thêm scope: cập nhật cli.py:111 (bắt buộc) + các docstring |
| C2-04 | P3 | Header "AIOS Conformance 1.0" mâu thuẫn "AIOS 1.1 READY" | **RESOLVED** — Header → "AIOS Conformance 1.1"; thêm assert trong test_format_conformance |
| C2-05 | P3 | `compatibility()` không cần kernel — dễ bị implementer thêm `_get_kernel()` | **RESOLVED** — Ghi chú triển khai: compatibility() KHÔNG gọi `_get_kernel()` (check thuần structural) |
| C2-06 | P3 | "nếu có" thay vì xác định; evidence `/9` hardcode | **RESOLVED** — Ghi rõ 2 assert cần sửa (test_certification.py:120/:128); evidence dùng `len(report.results)` (không hardcode 9) |

**Kết quả: 6/6 RESOLVED — spec nâng v3. Đủ điều kiện tasks.md + review.**
