# TASK-029 — Test Results (Harness Kernel, H1)

**Ngày**: 2026-08-15 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `1124 passed, 0 failed` (baseline 1086 → +38 test mới)
- **Coverage**: 95.20% (threshold 80% cứng — pass)
- **Arch tests**: 47/47 pass (gồm 5 test INV-017/018 mới)

## Test mới (38)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_harness_kernel.py` | 31 | contracts (extra=forbid, defaults, round-trip, safe_run_id B4/R3-5), lifecycle (happy/error chain, 8×8 matrix, terminal, COMPLETED→FAILED C1-02, CREATED→FAILED B1), context (no sink in dump, emit, sink raise C2-05, no-sink), registry (register/get/list, duplicate, unknown, abstract TypeError C3-04), runner (happy + evidence 2 artifact + refs checksum + B5 ids, failure DIAGNOSED, on_failure raise → report C1-03, catch-all ngoài hook B1, duplicate run_id, sanitize `a?b` B4, no artifact in-memory B1, deterministic trừ timestamps+ref B2, get_evidence unknown [], restart fallback B3, evidence files parseable B11), INV-018 behavioral (success+failure đều ≥2 artifact), INV-017 duck-typed stub |
| `tests/test_architecture.py` | +5 | `test_inv017_harness_import_allowlist` (rglob C3-07, external collections B7, KHÔNG kernel.events C3-05), `test_inv017_harness_no_kernel_impl` (rglob), `test_inv017_harness_no_god_object` (contracts leaf import-based C2-04), `test_inv018_runner_builds_evidence` (literal + finally C1-03), `test_inv017_no_harness_in_kernel` |
| `tests/test_config.py` | +1 | harness block defaults + env override |
| `tests/test_runtime_kernel.py` | +1 | `test_harness_wired` (resolve + shared StateService/ArtifactService + e2e evidence) |

## Kiểm chứng AC (10/10 — xem spec §6)
- **AC1-AC5** ✅ Contracts/lifecycle/context/registry/runner unit — 8×8 matrix, evidence, determinism
- **AC6** ✅ INV-018: mọi run (success + failure) ≥ 2 artifact (events + report), checksum ref, file parseable
- **AC7** ✅ get_run/get_result/get_evidence; restart-safe fallback qua ArtifactService sidecars
- **AC8** ✅ INV-017: allow-list + no kernel impl + no god object + no harness in kernel
- **AC9** ✅ Wiring shared instances + e2e; 1124 pass / 95.20%
- **AC10** ✅ Deterministic (trừ timestamps + ref — B2)

## Ghi chú / Deviations
1. **HarnessContext nằm trong context.py** (không phải contracts.py) — runner/registry/__init__ import từ context.
2. **Runner phải có `execute`** (public API chính) — no_god_object test chỉ cấm registry/lifecycle/context định nghĩa execute.
3. **run_id default** `harness:{harness_id}:{time_ns:x}` (không uuid) — vẫn deterministic-ish, đủ unique.
4. **verify được xử lý riêng** (cần payload) — không nằm trong vòng for prepare/validate/run.
5. **ArtifactContract 9 field** qua `_evidence_contract` helper (id `harness:{run_id}:{kind}` ≠ HarnessArtifact.id `{run_id}:{kind}` — B5).

## Kết luận
- [x] Tất cả 10 AC pass
- [x] Full suite 1124 pass, coverage 95.20%
- [x] INV-017 (AST 5 test + behavioral duck-typed) + INV-018 (evidence mọi run) enforced
