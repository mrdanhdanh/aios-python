# TASK-087 — M12-P3: Compatibility Conformance (C4) — SPEC v3

> Milestone: M12 AIOS 1.1 Compatibility (Issue #7, nhánh `feature/ISSUE-7-aios-1-1-compatibility`)
> Nâng cấp: C4 — mở rộng `aiagent conformance` area `compatibility` + gate (KHÔNG phá 10 areas/6 gates hiện có)
> Dependency: C1 (TASK-084 ✅) → C2 (TASK-085 ✅) → C3 (TASK-086 ✅) → (C4 ∥ C5)
> v3 = tích hợp resolution critique-1 (7/7) + critique-2 (6/6)

## 1. Mục tiêu

1. **Conformance phản ánh AIOS 1.1 Compatibility**: thêm area `compatibility` (structural — CompatibilityMatrix + BackwardCompatibilitySuite) + gate release `gate_g_compatibility` — KHÔNG phá 10 areas/6 gates hiện có.
2. **`aiagent conformance` → AIOS 1.1 READY** khi tất cả areas + GS + gates pass.

## 2. Phạm vi

**In:**
- `harness/certification/checks.py` — `AreaChecks.compatibility()` (string `"compatibility"` — KHÔNG thêm enum, precedent `"verification"` C1-02) + **thêm vào `run_all()` hardcode list** (11 items — C1-01); docstring "9 area checks" → "11 area checks" (C2-03)
- `harness/certification/conformance.py` — `release_gates(areas=None)` + `gate_g_compatibility` (C2-02: reuse area precomputed, không double-run); `format_conformance` header → `"AIOS Conformance 1.1"` + result → `"AIOS 1.1 READY"` (C1-04 + C2-04); docstring
- `workflow/cli.py:111` — help conformance "10 areas + 6 gates" → "11 areas + 7 gates" (C2-03 bắt buộc)
- `tests/test_certification.py` — `test_gate_definitions` 6→7 gates (C1-03); **2 assert cụ thể** "AIOS 1.0 READY" tại :120 và :128 → 1.1 (C1-07 + C2-06); `test_9_areas` KHÔNG đổi
- Tests mới `tests/test_conformance_compat.py`

**Out:** C5 ADR-0007 + migration guide (TASK-088)

## 3. Thiết kế

### 3.1 `AreaChecks.compatibility()` (structural — component thật, R1 M10)

```
def compatibility(self) -> AreaResult:
    try:
        from ...upgrade.compatibility import CompatibilityMatrix
        from ...upgrade.backward_compat import BackwardCompatibilitySuite
        from ... import __version__
        rows = CompatibilityMatrix().list()          # ≥ 14 entry (TASK-084)
        report = BackwardCompatibilitySuite().run()  # suite checks (TASK-086)
        ok = len(rows) >= 14 and report.ok and __version__ == "1.1.0"
        return self._result("compatibility", ok,
            f"matrix={len(rows)} entries, verify={sum(1 for r in report.results if r.ok)}/{len(report.results)}, version={__version__}")
    except Exception as exc:
        return self._result("compatibility", False, str(exc))
```

> Ghi chú (C2-05): `compatibility()` KHÔNG gọi `_get_kernel()` — check thuần structural; CHỈ relative import, cấm absolute `from aios_core import __version__` (INV-017 — C2-01).

### 3.2 `release_gates(areas=None)` + `gate_g_compatibility` (C2-02)

```
def release_gates(self, areas: list[AreaResult] | None = None) -> dict[str, bool]:
    ...
    if areas is not None:
        compat = next((a for a in areas if a.area == "compatibility"), None)
        gates["gate_g_compatibility"] = compat is not None and compat.status == PassFail.PASS
    else:
        gates["gate_g_compatibility"] = (
            AreaChecks(self.kernel).compatibility().status == PassFail.PASS
        )
```

- `run()` truyền areas precomputed → gate G KHÔNG chạy lại compat verify (1 lần — C2-02)
- `test_gate_definitions` gọi `release_gates()` không areas → chạy component thật (standalone)
- exception → False (fail-closed)

### 3.3 Conformance: 11 areas + 7 gates

- `run_all()` = 11 method (thêm compatibility — C1-01)
- `format_conformance` → `"AIOS 1.1 READY"` / `"AIOS 1.1 NOT READY"` (C1-04)
- `test_gate_definitions` assert 7 gates (C1-03)

## 4. Input / Output

| Lệnh | Input | Output |
|------|-------|--------|
| `aiagent conformance` | — | 11 areas + 20 GS + 7 gates → AIOS 1.1 READY/NOT READY |

## 5. Tiêu chí chấp nhận (AC)

- [ ] AC1: `AreaChecks.compatibility()` tồn tại (string `"compatibility"` — KHÔNG đổi enum, `test_9_areas` vẫn PASS)
- [ ] AC2: area compatibility PASS khi: matrix ≥ 14 entry + compat verify 9/9 + `__version__ == "1.1.0"` (evidence chứa cả 3 số liệu)
- [ ] AC3: area compatibility FAIL (fail-closed) khi compat verify có check fail (monkeypatch Suite)
- [ ] AC4: `release_gates(areas=None)`: có areas → gate G dùng status precomputed (KHÔNG double-run — C2-02); None → chạy thật; exception → False
- [ ] AC5: conformance chạy thật → **11 areas + 20 GS + 7 gates**; `test_gate_definitions` assert 7 gates (cập nhật); 10 areas/6 gates cũ KHÔNG regression
- [ ] AC6: CLI `aiagent conformance` → exit 0 + header `"AIOS Conformance 1.1"` + `"AIOS 1.1 READY"` (C2-04) + area compatibility hiển thị ✓; help `conformance` ghi "11 areas + 7 gates" (C2-03)
- [ ] AC7: full suite ≥ 2109 PASS / 0 FAIL (baseline TASK-086 — PROGRESS.md); `test_certification.py` cập nhật PASS
- [ ] AC8: arch-health 0 violations; doctor healthy; KHÔNG thêm invariant; INV-001..035 giữ nguyên

## 6. Rủi ro & giả định

| Rủi ro | Cách xử lý |
|--------|-----------|
| `run_all()` hardcode | Thêm `compatibility()` vào list (C1-01) |
| Test cũ assert 6 gates / "AIOS 1.0 READY" | Cập nhật `test_gate_definitions` + assert version (C1-03/07) — bump chủ động |
| Conformance chậm (compat verify simulate) | Chấp nhận (TASK-086 đã redirect stdout; 1 lần) |
| `from ... import __version__` trong harness | Hợp lệ — harness không bị allow-list upgrade/ chặn |

## 7. Ghi chú triển khai

1. Thêm `compatibility()` vào `AreaChecks` + `run_all()` (11 items).
2. Thêm `gate_g_compatibility` vào `release_gates()`; đổi format → "AIOS 1.1 READY".
3. Cập nhật `test_certification.py` (test_gate_definitions 7 gates + assert version nếu có).
4. Test mới `tests/test_conformance_compat.py` (area PASS/FAIL + gate + CLI).
5. Chạy targeted + full suite + arch-health + doctor.
6. Đóng 8-file hard gate; LOG/PROGRESS; commit — KHÔNG push.