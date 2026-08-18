# TASK-087 — Implementation artifacts

## Deliverables

| File | Nội dung |
|------|----------|
| `backend/src/aios_core/harness/certification/checks.py` | `AreaChecks.compatibility()` (string "compatibility" — precedent M11; matrix ≥ 14 + suite verify + AIOS_VERSION 1.1.0; KHÔNG _get_kernel; KHÔNG import root — layer rule) + `run_all()` 11 items + docstring |
| `backend/src/aios_core/harness/certification/conformance.py` | `release_gates(areas=None)` + `gate_g_compatibility` (reuse precomputed — không double-run; None → chạy thật; exception → False); header "AIOS Conformance 1.1" + "AIOS 1.1 READY"; docstrings |
| `backend/src/aios_core/harness/certification/contracts.py` | Docstring "AIOS 1.1 READY" |
| `backend/src/aios_core/workflow/cli.py` | Help conformance "11 areas + 7 gates" |
| `backend/tests/test_certification.py` | `test_gate_definitions` 7 gates; 2 assert 1.1 READY + header |
| `backend/tests/test_conformance_compat.py` | **MỚI** — 9 test (area PASS/FAIL-closed, gate G reuse/standalone/exception, 11 areas 7 gates, CLI) |

## Kết quả

- Full suite: **2118 PASS / 0 FAIL** (2109 + 9 mới), coverage 92.98%
- CLI thật: `conformance` → 11 areas + 20 GS + 7 gates → **AIOS 1.1 READY** exit 0
- arch-health 0 violations (fix: không import root aios_core từ harness)

## Ghi chú kiến trúc

- `compatibility()` KHÔNG gọi `_get_kernel()` (check thuần structural)
- `release_gates(areas)` reuse kết quả area precomputed — compat verify chạy 1 lần/conformance
