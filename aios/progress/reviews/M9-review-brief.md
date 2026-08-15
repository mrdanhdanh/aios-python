# Review M9 — Autonomous (template nâng cấp v2)

> **⚠️ SNAPSHOT @M9 (2026-08-15)** — brief này chụp trạng thái M9. Số liệu test ghi trong này (1780 pytest @M9) ĐÚNG TẠI THỜI ĐIỂM M9. Khi review độc lập, model PHẢI chạy thật để lấy con số hiện tại, không dùng số trong brief làm kết luận cuối.
> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem bản review nội bộ nào trước đó.
>
> **Lưu ý cho reviewer:** Template v2.1 (hard-gate review framework) chuyển trọng tâm từ *existence review* sang **runtime correctness & architecture review**. Bắt buộc áp dụng các mục 4–22 + Acceptance Traceability (22A) + Final Gate (26) trước khi kết luận.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M9 – Autonomous (P14)" + mục "Architecture Invariants (INV-030..INV-034)"** (tiêu chuẩn nghiệm thu M9)
- `AGENTS.md` — quy tắc vận hành dự án
- `docs/architecture.md` — tài liệu kiến trúc + Architecture Invariants
- `docs/adr/` — Architecture Decision Records

## 2. Nhiệm vụ

Review milestone **M9** — Autonomous (P14): đưa AIOS từ orchestrated thành autonomous (tự lập goal, plan, act, verify, learn, recover, long-horizon).
13 task (TASK-050..062) + 5 invariant (INV-030..INV-034):
- **P1 Goal Engine/Planner/World/Loop/Governor** (TASK-050..054): GoalContract + lifecycle; keyword plan; World Model ≠ Memory; 8-step governor-gated loop; Governor budget/risk
- **P2 Recovery/Long-Horizon/Memory/Stuck** (TASK-055..057,061): circuit breaker per-fingerprint; checkpoint/resume; 6-kind memory + double gate; 7 stuck signals
- **P3 Experimentation/Evaluation** (TASK-058,060): evidence-first self-improvement; 5-rule evaluator + ProgressEstimator
- **P4 Multi-Agent/Scheduler** (TASK-059,062): 4 delegation modes; INTERVAL/DAILY proactive scheduler

Đánh giá độc lập 4 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M9 (13 task P1–P4 + 5 invariant INV-030..034)
2. **Đúng quy trình**: hard gate có được tuân thủ cho TASK-050..062 không (8-file: spec/critique-1/critique-2/tasks/review/test/evaluation/implementation/)
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế ↔ kết quả test có khớp không
4. **Đúng kiến trúc & runtime correctness**: `autonomous/` tuân thủ INV-030..034; Autonomous Layer đứng TRÊN Orchestrator (chỉ import kernel.events + kernel.services + intra-package)

## 3. Deliverable cần kiểm tra

### 3.1 Code (backend — package `autonomous` tại `backend/src/aios_core/autonomous/`)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 1 | `autonomous/goal.py` | GoalContract (extra="forbid") + lifecycle 13 state + GoalManager.advance raise on invalid |
| 2 | `autonomous/planner.py` | AutonomousPlanner.plan → bounded AutonomyPlan.steps từ world.snapshot() + capabilities |
| 3 | `autonomous/world.py` | WorldModel.snapshot() pure store; KHÔNG import memory/knowledge |
| 4 | `autonomous/loop.py` | AutonomousLoop.run_goal 8 bước, gọi governor.check_action mỗi vòng (INV-030), actor injectable |
| 5 | `autonomous/governor.py` | AutonomyGovernor.check_action fail-closed + 7 budget literals (INV-031) + risk table |
| 6 | `autonomous/recovery.py` | CircuitBreaker per-fingerprint + RecoverableLoop fallback |
| 7 | `autonomous/long_horizon.py` | ExecutionSession + checkpoint()/resume() SQLite (INV-032) |
| 8 | `autonomous/memory.py` | 6-kind AutonomousMemory + promote double gate validated AND confidence≥0.5 (INV-034) |
| 9 | `autonomous/experimentation.py` | ExperimentationEngine: evaluate_fn bắt buộc (INV-033), verdict từ evidence, deploy=canary |
| 10 | `autonomous/evaluation.py` | AutonomousEvaluator 5 rules + ProgressEstimator |
| 11 | `autonomous/stuck.py` | 7 stuck signals detection |
| 12 | `autonomous/multi_agent.py` | 4 delegation modes + topo order + aggregation |
| 13 | `autonomous/scheduler.py` | INTERVAL/DAILY trigger + persist last_run_at (sentinel -1) |
| 14 | `autonomous/contracts.py` + `errors.py` + `__init__.py` | Contracts extra="forbid" + AutonomyManager facade (compose INV-030..034) |

### 3.2 Tests (chạy thật)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 15 | `backend/tests/test_autonomous.py` | ~129 test autonomous (goal/planner/world/loop/governor/recovery/long_horizon/memory/experimentation/evaluation/stuck/multi_agent/scheduler) |
| 16 | `backend/tests/test_architecture.py` | 9 INV-030..034 tests (`test_inv030_*`..`test_inv034_*`) + `test_m9_autonomous_import_allowlist` + `test_m9_world_not_memory` + `test_m9_autonomous_no_worker_plane` + `test_m9_autonomous_no_god_object` |
| 17 | `backend/tests/test_observability_arch_health.py` | `test_m9_real_src_healthy` + `test_m9_autonomous_isolation_fires` (scanner cover autonomous) |
| 18 | Toàn bộ backend | `cd backend; .venv/Scripts/python -m pytest` — mong đợi **≥1793 tests pass** (tại M9 baseline 1780 + M5/M6/M7/M8 review additions + 3 M9 scanner regresi) |

### 3.3 Hồ sơ quy trình (hard gate)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 19 | `aios/progress/tasks/TASK-050..062/` | Mỗi folder đủ 8 file: spec, critique-1, critique-2, tasks, review, test, evaluation, **implementation/** |
| 20 | `aios/progress/PROGRESS.md` | Mục M9: TASK-050..062 done; khớp git history + LOG.md |

### 3.4 Architecture scanner

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 21 | `backend/src/aios_core/observability/arch_health.py` | `_LAYER_RULES` phải có rule `("layer", "autonomous", (...))` để scanner cover autonomous (không silent-skip như M5/M6/M7/M8 F1) |
| 22 | runtime verify | `python -c "from aios_core.observability.arch_health import ArchitectureHealth; ArchitectureHealth().scan().healthy"` → `True` |

## 4. Tiêu chí nghiệm thu (V1–V8)

| # | Tiêu chí | Nguồn |
|---|----------|-------|
| V1 | Goal Engine (P1) + INV-030 context | PLAN §M9.3 |
| V2 | Planner (P1) + INV-030 context | PLAN §M9.4 |
| V3 | World Model ≠ Memory (P1) + INV-034 context | PLAN §M9.5 |
| V4 | Loop (P1) governor-gated + INV-030 | PLAN §M9.6 |
| V5 | Governor (P1) + INV-030 + INV-031 | PLAN §M9.7 |
| V6 | Recovery + Long-Horizon (P2) + INV-032 | PLAN §M9.8 |
| V7 | Memory + Experimentation + Evaluation + Stuck + Multi-Agent + Scheduler (P2–P4) + INV-033 + INV-034 | PLAN §M9.9–M9.13 |
| V8 | Process: 8-file hard gate TASK-050..062 + Arch scanner cover autonomous | AGENTS.md hard gate |

## 5. Kết luận mong đợi

- Nếu V1–V7 PASS + INV-030..034 PASS + V8 PASS → **M9 ACCEPTED**.
- Nếu V8 FAIL do thiếu file process (không phải code bug) → **ACCEPTED with P2 remediation** (thêm scanner rule / implementation/).
- P1 code bug → **REJECTED** cho đến khi fix.
