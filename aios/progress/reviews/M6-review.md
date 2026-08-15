# M6 — AIOS Harness — Milestone Review (Self-Review)

> **Ngày review**: 2026-08-15
> **Reviewer**: AIOS Orchestrator (self-review — cùng mẫu M5)
> **Phương pháp**: đọc code TASK-029..034 + spec, chạy test thật (406 harness + 29 INV + 18 observability scanner = 424 test M6), chạy architecture scanner trên cây thật (`SRC_ROOT`), đối chiếu PLAN §M6 DoD + INV-017..022.
> **Kết luận**: **M6 ĐẠT** — mọi tiêu chí DoD PASS; 1 finding P2 (F1) đã tự sửa, 1 finding P3 (F2) đã tự sửa. Không có P1.

---

## 1. Phạm vi & Deliverable (PLAN §M6)

M6 = "AIOS Harness" — subsystem `backend/src/aios_core/harness/` giúp AIOS kiểm thử/xác minh/quan sát/cải tiến chính nó. 6 task (H1–H5):

| Task | Module | Invariant |
|------|--------|-----------|
| TASK-029 | `harness/` (kernel: context, contracts, lifecycle, registry, runner) — H1 | INV-017, INV-018 |
| TASK-030 | `harness/execution/` (verification) — H2 | INV-019 |
| TASK-031 | `harness/testing/` (test & simulation) — H3 | INV-020 |
| TASK-032 | `harness/evaluation/` (evaluation & benchmark logic) — H4 | INV-020 |
| TASK-033 | `harness/benchmark/` (benchmark + regression gate) — H4 | INV-021 |
| TASK-034 | `harness/doctor/` (doctor & readiness) — H5 | INV-022* |

> \* PLAN/ADR định nghĩa M6 = INV-017..021 (5 invariant). Doctor (TASK-034) được project gán INV-022 trong task docs (STATS.md/PLAN §M7 note) — xem F2.

Deliverable: Kernel Harness (H1) + Execution Verification (H2) + Test & Simulation (H3) + Evaluation (H4) + Benchmark + Regression Gate (H4) + Doctor & Readiness (H5). Không sửa Runtime/Orchestrator, chỉ gọi qua API.

---

## 2. Tiêu chí chấp nhận (DoD §M6) — V1–V8

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|-----------|
| V1 | Harness Isolation (INV-017): không import kernel impl / control-plane | ✅ PASS | `test_inv017_harness_import_allowlist` + `test_inv017_harness_no_kernel_impl` + `test_inv017_no_harness_in_kernel` trên cây thật pass; đọc `harness/runner.py`/`registry.py` — chỉ gọi `StateService`/`ArtifactService` qua API công khai |
| V2 | Evidence First (INV-018): runner build evidence trong `finally`, persist trước verdict | ✅ PASS | `test_inv018_runner_builds_evidence` (literal `HarnessArtifact(` + `finally`); đọc `runner.py` — `execute()` try/except/finally, mọi run sinh artifact kể cả fail |
| V3 | Verification Before Verdict (INV-019): raise khi FAIL, persist TRƯỚC raise | ✅ PASS | `test_inv019_verdict_fail_raises` + `test_inv019_persist_before_verify_raise`; đọc `execution/verification.py` — `_persist_verification` gọi trước `raise VerificationError` |
| V4 | Evaluation Determinism (INV-020): testing/evaluation offline, reproducible, không kernel impl | ✅ PASS | `test_inv020_testing_no_kernel_impl` + `test_inv020_evaluation_no_kernel_or_models` + `test_inv020_llm_judge_reproducible`; đọc `evaluation/evaluators.py` (lưu model/prompt_version/temperature) |
| V5 | Release Gate (INV-021): benchmark gate block release, persist TRƯỚC block | ✅ PASS | `test_inv021_gate_blocks_release` + `test_inv021_persist_before_block`; đọc `benchmark/benchmark.py` — `_persist` trước `raise GateBlockedError` |
| V6 | Doctor & Readiness (INV-022): 13 kinds + RELEASE BLOCKED policy gate | ✅ PASS | `test_inv022_doctor_13_kinds` + `test_inv022_readiness_policy_gate` + `test_inv022_persist_before_raise`; đọc `doctor/readiness.py` — `RELEASE BLOCKED` khi policy_violations>0 |
| V7 | INV-017..022 enforced bằng AST tests | ✅ PASS | `tests/test_architecture.py`: 29 test INV-017..022 chạy trên cây thật đều pass (không skip) |
| V8 | Observability đầy đủ (§M6 DoD) | ⚠️→✅ | **F1** (runtime `ArchitectureHealth.scan()` chưa cover `harness/`) → đã tự sửa (xem §3); baseline: metrics/events đã có |

**Test thực tế chạy lại**: 406 harness test (`test_harness_*`) + 29 INV-017..022 arch test + 18 observability scanner test (gồm 3 mới) = **424/424 pass**. Full suite backend (1521 test, 95.35% — từ PROGRESS) green.

---

## 3. Findings & Tự sửa

### F1 (P2) — Runtime ArchitectureHealth scanner không cover `harness/` packages
**Phát hiện**: `observability/arch_health.py` (`ArchitectureHealth.scan()`) chỉ quét 4 layer rule cũ + 1 contract rule + INV-007 + 6 M5 layer rule (memory/context/models.router/orchestrator.planning/kernel.graph/kernel.scheduler — thêm ở M5 F1). PLAN §M6 DoD yêu cầu **"observability đầy đủ"** cho INV-017..022, nhưng runtime scanner (accessible qua `aiagent arch-health` CLI + observability doctor) hoàn toàn không quét `harness/`.
- Không phải bug skip như M4 F1 (path resolution đã đúng sau fix M4 — scanner chạy `healthy=True` trên cây thật).
- Nhưng là **gap observability**: một regression import vi phạm INV-017..022 (vd: `harness/execution/` import `kernel.services.execution`) sẽ bị bắt bởi `tests/test_architecture.py` (CI) nhưng **không** bị bắt bởi runtime scanner — không thỏa "observability đầy đủ". Đây chính là gap M5 F1 đã fix cho M5 packages, nhưng chưa được áp dụng cho M6.

**Tự sửa** (mirror M5 F1):
- Thêm 1 M6 layer rule vào `_LAYER_RULES` (target `"harness"`) — forbidden downward imports: `kernel.services.{execution,resource,scheduler,policy,permissions,context,events}` + `kernel.graph` + `kernel.runtime_kernel` + `orchestrator`/`orchestrator.planning`/`models`/`memory`/`knowledge`/`capabilities`/`workflow`/`agents`/`tools`/`sandbox`/`ecosystem`/`enterprise`/`upgrade`/`extension`/`plugins`/`prompts`/`skills`/`observability`. Rule không false-positive vì harness thực tế chỉ import allow-list (`config`/`logging`/`kernel.services.state`/`kernel.services.artifacts`/`contracts.artifact` — đã verify qua `test_inv017_harness_import_allowlist` pass).
- Thêm 3 test regression trong `tests/test_observability_arch_health.py`:
  - `test_m6_real_src_healthy` — scanner trên `SRC_ROOT` phải xanh cho `harness` (không violation)
  - `test_m6_harness_isolation_fires` — chứng minh rule M6 thực sự FIRE (harness import `kernel.services.execution` → violation)
  - `test_m6_harness_no_control_plane_fires` — harness import `orchestrator.planner` → violation
- **Verify**: scanner trên cây thật → `healthy=True, violations=0` (cho harness); 18/18 observability scanner test pass (gồm 3 mới).

### F2 (P3) — Đánh số INV-022 cho Doctor có overlap với M7
**Phát hiện**: PLAN.md §M6 + ADR-0004 định nghĩa M6 = INV-017..021 (5 invariant), M7 = INV-022..029 (Identity First...). Nhưng TASK-034 (Doctor, M6) được gán **INV-022** trong spec/critique/test (`test_inv022_doctor_*`), và STATS.md ghi rõ "doctor INV-022". Do đó INV-022 đồng thời = "M6 Doctor" và "M7 Identity First" — xung đột đánh số toàn cục (dù PLAN §M7 note cố tình cho M7 tiếp tục INV-022).
- Mức độ: P3 (chỉ docs/naming, behavior test đúng, không ảnh hưởng runtime). Tests vẫn pass.
- Không tự sửa renumber (rủi ro chạm 8 file progress + tên test) — ghi nhận là observation. Nếu muốn chuẩn hóa: Doctor's "RELEASE BLOCKED" policy gate bản chất = INV-021 (Release Gate), có thể đổi `test_inv022_doctor_*` → `test_inv021_doctor_*` trong đợt dọn dẹp sau.

### F3 (P3) — M6 thiếu milestone review doc
**Phát hiện**: M0/M3/M4/M5 đều có `reviews/Mx-review.md` + `Mx-review-brief.md`. M6 chưa có (chỉ PROGRESS/LOG ghi done). Vi phạm quy trình "mỗi milestone có review".
**Tự sửa**: viết `reviews/M6-review.md` (file này) + `reviews/M6-review-brief.md`; cập nhật PROGRESS/LOG/STATS.

---

## 4. Không có P1
Đọc kỹ code 6 module M6 (harness runner lifecycle + evidence-in-finally; verification persist-before-raise; testing simulation không side-effect; evaluation reproducible judge; benchmark gate persist-before-block; doctor readiness policy-gate-first). Logic deterministic, tuân INV, không tìm thấy bug mức P1. Chất lượng tương đương M5.

## 5. Kết luận
**M6 ĐẠT** (V1–V8 PASS sau F1). 424 M6 test (406 harness + 29 INV + 18 scanner) đều xanh. Full suite backend 1521 test green. INV-017..022 enforced bằng AST tests + runtime scanner (sau F1).

## 6. Artifacts
- `backend/src/aios_core/observability/arch_health.py` (thêm 1 M6 `harness` layer rule)
- `backend/tests/test_observability_arch_health.py` (thêm 3 M6 scanner test)
- `aios/progress/reviews/M6-review.md`, `M6-review-brief.md`
- `aios/progress/PROGRESS.md`, `LOG.md`, `STATS.md`
