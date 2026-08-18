# TASK-087 — Tasks breakdown (checklist)

> Spec v3 (8 AC). Hard gate: spec ✅ + critique-1 (7/7) ✅ + critique-2 (6/6) ✅

## A. Area compatibility
- [ ] A1. `checks.py` — `AreaChecks.compatibility()` (string "compatibility", component thật: matrix ≥ 14 + suite verify + `__version__ == "1.1.0"`; evidence dùng len(report.results); KHÔNG gọi _get_kernel — C2-05; CHỈ relative import — C2-01)
- [ ] A2. `checks.py` — `run_all()` + `self.compatibility()` (11 items — C1-01); docstring "9" → "11" (C2-03)

## B. Gate + format
- [ ] B1. `conformance.py` — `release_gates(areas=None)` + `gate_g_compatibility` (reuse precomputed — C2-02; None → chạy thật; exception → False)
- [ ] B2. `conformance.py` — `run()` truyền areas vào release_gates; header → "AIOS Conformance 1.1" (C2-04); result → "AIOS 1.1 READY" (C1-04); docstring module "5 release gates" → "7" (R3-2)
- [ ] B3. `cli.py:111` — help conformance → "11 areas + 7 gates" (C2-03 bắt buộc); `cli.py:842` docstring `_conformance` + `contracts.py:66` docstring "AIOS 1.0 READY" → 1.1 (R2-1)

## C. Tests
- [ ] C1. `test_certification.py` — `test_gate_definitions` 6→7 gates (C1-03); 2 assert "AIOS 1.0 READY" (:120/:128) → 1.1 (C2-06); `test_9_areas` KHÔNG đổi
- [ ] C2. `tests/test_conformance_compat.py` — area PASS (evidence chứa matrix/verify/version) + area FAIL khi monkeypatch `aios_core.upgrade.backward_compat.BackwardCompatibilitySuite` (module nguồn — R3-1) + gate G (precomputed reuse + standalone) + CLI exit 0 + header/result 1.1 + help

## D. Verify & đóng task
- [ ] D1. Targeted: `pytest tests/test_conformance_compat.py tests/test_certification.py tests/test_verification.py` — PASS
- [ ] D2. Full suite — 0 regression baseline 2109 + test mới PASS
- [ ] D3. CLI thật `aiagent conformance` → exit 0 + "AIOS 1.1 READY"
- [ ] D4. `arch-health` 0 violations + `doctor` healthy
- [ ] D5. test.md + evaluation.md + implementation/README.md; LOG/PROGRESS; commit — KHÔNG push
