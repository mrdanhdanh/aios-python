# Milestone Review Brief — M6 (AIOS Harness)

> **Mục đích**: tài liệu tự chứa để đem cho model/người review ĐỘC LẬP đánh giá M6.
> **Cách dùng**: copy file này sang model review. Model tự đọc repo + chạy test, trả báo cáo theo mục 7 của REVIEW-BRIEF-TEMPLATE.md. KHÔNG sửa file.
> **Lưu ý reviewer**: M6 đã có 1 self-fix (F1) ghi trong `reviews/M6-review.md` — reviewer độc lập đánh giá lại từ code thực tế, không bị ảnh hưởng bởi kết luận đó.

---

## 1. Bối cảnh dự án

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình hard gate cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate.

Đọc bắt buộc:
- `docs/PLAN.md` — master plan, **đặc biệt mục "M6 – AIOS Harness (P11)"** + "Architecture Invariants" (INV-017..021; doctor INV-022).
- `AGENTS.md` — quy tắc vận hành.
- `docs/adr/0004-architecture-invariants.md` + `docs/architecture.md` §7.

## 2. Nhiệm vụ

Review milestone **M6** — AIOS Harness: Kernel (H1), Execution Verification (H2), Test & Simulation (H3), Evaluation (H4), Benchmark + Regression Gate (H4), Doctor & Readiness (H5). 5–6 invariant mới INV-017..022.
Đánh giá độc lập 4 khía cạnh: (1) đúng phạm vi, (2) đúng quy trình 8-file hard gate, (3) hồ sơ nhất quán, (4) kiến trúc & runtime correctness.

## 3. Deliverable cần kiểm tra

**Code (đọc thực tế):**
- `backend/src/aios_core/harness/` (TASK-029 H1: context, contracts, lifecycle, registry, runner, errors, __init__)
- `backend/src/aios_core/harness/execution/` (TASK-030 H2: verification, pipeline, evidence, replay, contracts, errors)
- `backend/src/aios_core/harness/testing/` (TASK-031 H3: testing, simulation, scenarios, contracts, errors)
- `backend/src/aios_core/harness/evaluation/` (TASK-032 H4: evaluation, evaluators, suites, trajectory, contracts, errors)
- `backend/src/aios_core/harness/benchmark/` (TASK-033 H4: benchmark, gate, runner, contracts, errors)
- `backend/src/aios_core/harness/doctor/` (TASK-034 H5: doctor, readiness, checks, contracts, errors)
- `backend/src/aios_core/observability/arch_health.py` (F1 self-fix: 1 M6 `harness` layer rule)

**Tests (chạy thật):**
- `backend/tests/test_harness_kernel.py`, `test_harness_execution.py`, `test_harness_testing.py`, `test_harness_evaluation.py`, `test_harness_benchmark.py`, `test_harness_doctor.py` (406 test)
- `backend/tests/test_architecture.py` (INV-017..022: `test_inv017_*`, `test_inv018_*`, `test_inv019_*`, `test_inv020_*`, `test_inv021_*`, `test_inv022_*`)
- `backend/tests/test_observability_arch_health.py` (test_m6_* — F1 self-fix, 3 test mới)

**Hồ sơ quy trình (mỗi task đủ 8 file):**
- `aios/progress/tasks/TASK-029/`..`TASK-034/` (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)

## 4. Architecture & Runtime Deep Review (TRỌNG TÂM)

Áp dụng mục 4.1–4.12 của template. Đặc biệt chú ý:
- **INV-017 Harness Isolation**: `harness/` chỉ import allow-list (`config`/`logging`/`kernel.services.state`/`kernel.services.artifacts`/`contracts.artifact`); không import `kernel.services.{execution,resource,scheduler,policy,permissions,context}` + orchestrator/models/memory/knowledge; không God Object (`def execute(` chỉ ở runner).
- **INV-018 Evidence First**: `runner.py` build `HarnessArtifact(` trong `finally` (evidence kể cả fail).
- **INV-019 Verification Before Verdict**: `execution/verification.py` persist (`_persist_verification`) TRƯỚC `raise VerificationError`; verdict FAIL xét trước INCONCLUSIVE (`pipeline.py` order).
- **INV-020 Evaluation Determinism**: `testing/`/`evaluation/` không import kernel.impl + `models`; LLM judge lưu `model/prompt_version/temperature` (`evaluators.py`); simulation/testing không side-effect (không sqlite3/httpx/socket/requests/os); loader `yaml.safe_load`.
- **INV-021 Release Gate**: `benchmark/benchmark.py` có `RegressionGate` + `GateBlockedError`; persist TRƯỚC `raise GateBlockedError`.
- **INV-022 Doctor/Readiness**: `doctor/contracts.py` đủ 13 `DoctorKind`; `readiness.py` có `RELEASE BLOCKED` + `policy_violations` (policy gate > overall).
- **4.12 Anti Fake Test**: đọc body test, không chỉ đếm pass. Đặc biệt `test_observability_arch_health.py::test_m6_*` — chạy scanner trên cây thật (`SRC_ROOT`) và confirm M6 rule thực sự FIRE (không dead rule) và không false-positive.

## 5. Tiêu chí chấp nhận (nguồn: PLAN.md §M6 DoD)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|-----------------|---------------------|
| V1 | Harness Isolation (INV-017) | `test_inv017_harness_import_allowlist` + `test_inv017_harness_no_kernel_impl` + đọc `harness/runner.py` | harness chỉ gọi Runtime qua API |
| V2 | Evidence First (INV-018) | `test_inv018_runner_builds_evidence` + đọc `runner.py` | `HarnessArtifact(` trong `finally` |
| V3 | Verification Before Verdict (INV-019) | `test_inv019_verdict_fail_raises` + `test_inv019_persist_before_verify_raise` | persist trước raise |
| V4 | Evaluation Determinism (INV-020) | `test_inv020_*` + đọc `evaluation/evaluators.py` | judge reproducible |
| V5 | Release Gate (INV-021) | `test_inv021_gate_blocks_release` + `test_inv021_persist_before_block` | gate block + persist trước block |
| V6 | Doctor & Readiness (INV-022) | `test_inv022_doctor_13_kinds` + `test_inv022_readiness_policy_gate` | 13 kinds + RELEASE BLOCKED |
| V7 | INV-017..022 enforced bằng AST tests | `tests/test_architecture.py` (29 test) | tất cả pass trên cây thật |
| V8 | Observability đầy đủ (§M6 DoD) | scanner trên `SRC_ROOT` + `test_m6_real_src_healthy` | harness scan xanh (F1 self-fix) |

## 6. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file mục 3 — không tin mô tả, phải thấy bằng chứng trong file.
2. Với mỗi tiêu chí mục 5: tìm bằng chứng → kết luận PASS/FAIL/INCONCLUSIVE kèm trích dẫn `file:đường dẫn`.
3. Áp dụng Architecture & Runtime Deep Review (mục 4.1–4.12) — mỗi mục có kết luận rõ.
4. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline`.
5. Tìm lỗ hổng chủ động: file thiếu, stub không logic, mâu thuẫn, claim không bằng chứng, **test pass nhưng không test đúng** (mục 4.12).
6. Với mỗi task: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/).
7. Phân mức findings: **P1** (sai mục tiêu/tiêu chí), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ).

## 7. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review M6 — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả (PASS/FAIL/INCONCLUSIVE) | Bằng chứng (file + trích dẫn) |

## 2. Architecture Compliance
(đối chiếu mục 4.1–4.12: Runtime-first / Contract-first / Plugin-first / Engine-independent /
Capability-first / Policy-first / DI / Event-driven / Dependency / Wiring / Security /
Performance / Event Bus / Anti-fake-test — mỗi nguyên tắc ghi PASS/FAIL/INCONCLUSIVE + trích dẫn)

## 3. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 4. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 5. Điểm mạnh (nếu có)
## 6. Gợi ý cải thiện (không bắt buộc)
```

## 8. Final Gate

Milestone chỉ được ACCEPTED khi: tất cả tiêu chí mục 5 = PASS; không có P1; không INCONCLUSIVE; test bắt buộc chạy thành công.

> Nếu có INCONCLUSIVE → không ACCEPTED cho đến khi nâng lên PASS hoặc FAIL.
