# Milestone Review Brief — M5 (Core Intelligence)

> **Mục đích**: tài liệu tự chứa để đem cho model/người review ĐỘC LẬP đánh giá M5.
> **Cách dùng**: copy file này sang model review. Model tự đọc repo + chạy test, trả báo cáo theo mục 7 của REVIEW-BRIEF-TEMPLATE.md. KHÔNG sửa file.
> **Lưu ý reviewer**: M5 đã có 1 self-fix (F1) ghi trong `reviews/M5-review.md` — reviewer độc lập đánh giá lại từ code thực tế, không bị ảnh hưởng bởi kết luận đó.

---

## 1. Bối cảnh dự án

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình hard gate cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate.

Đọc bắt buộc:
- `docs/PLAN.md` — master plan, **đặc biệt mục "M5 – Core Intelligence (P9–P10)"** + "Architecture Invariants" (INV-011..016).
- `AGENTS.md` — quy tắc vận hành.
- `docs/adr/0004-architecture-invariants.md` + `docs/architecture.md` §7.

## 2. Nhiệm vụ

Review milestone **M5** — Core Intelligence: Memory Coordinator + Context Optimizer + Model Router + Planning Engine + Execution Graph + Parallel Scheduler. 6 invariant mới INV-011..016.
Đánh giá độc lập 4 khía cạnh: (1) đúng phạm vi, (2) đúng quy trình 8-file hard gate, (3) hồ sơ nhất quán, (4) kiến trúc & runtime correctness.

## 3. Deliverable cần kiểm tra

**Code (đọc thực tế):**
- `backend/src/aios_core/memory/coordinator.py` (TASK-023)
- `backend/src/aios_core/context/optimizer.py` (TASK-024)
- `backend/src/aios_core/models/router/` (TASK-025: router/selector/policy/cost/health/availability/fallback/contracts)
- `backend/src/aios_core/orchestrator/planning/` (TASK-026: engine/validation/goal_analyzer/task_decomposer/dependency_analyzer/capability_resolver/risk_analyzer/execution_planner/templates/contracts)
- `backend/src/aios_core/kernel/graph/` (TASK-027: contracts/converter/errors/executor/state_machine)
- `backend/src/aios_core/kernel/scheduler/` (TASK-028: contracts/errors/execution_runner/scheduler)
- `backend/src/aios_core/observability/arch_health.py` (F1 self-fix: 6 M5 layer rule)

**Tests (chạy thật):**
- `backend/tests/test_memory_coordinator.py`, `test_context_optimizer.py`, `test_model_router.py`, `test_planning_engine.py`, `test_execution_graph.py`, `test_parallel_scheduler.py`, `test_context.py`
- `backend/tests/test_architecture.py` (INV-011..016: `test_inv011_memory_isolation`, `test_inv_memory_import_allowlist`, `test_inv_context_import_allowlist`, `test_inv_planning_import_allowlist`, `test_inv014_*`, `test_inv_graph_import_allowlist`, `test_inv015_*`, `test_inv016_*`, `test_inv013_*`)
- `backend/tests/test_observability_arch_health.py` (test_m5_*)

**Hồ sơ quy trình (mỗi task đủ 8 file):**
- `aios/progress/tasks/TASK-023/`, `TASK-024/`, `TASK-025/`, `TASK-026/`, `TASK-027/`, `TASK-028/` (spec, critique-1, critique-2, tasks, review, test, evaluation)

## 4. Architecture & Runtime Deep Review (TRỌNG TÂM)

Áp dụng mục 4.1–4.12 của template. Đặc biệt chú ý:
- **INV-011 Memory Isolation**: Agent không import `memory`/`knowledge` trực tiếp; coordinator là pure orchestrator, agents chỉ qua ContextService (EXECUTION scope).
- **INV-012 Context Budget**: `MemoryBudget` per-kind + 7-tier priority P0–P6, per-tier cap + total budget cut (bottom-up), P0/P1 exempt.
- **INV-013 Model Routing Policy**: selection CHỈ qua `ModelRouter`; fallback theo RoutingPolicy (fail-fast, re-filter rule).
- **INV-014 Plan Validation**: `engine.py` validate plan TRƯỚC khi trả (AST gate `self._validator.validate(`); 8 hạng mục (CONTRACT/CAPABILITY/PERMISSION/POLICY/DEPENDENCY/RESOURCE/CYCLE/TIMEOUT).
- **INV-015 Graph Acyclicity**: `validate_dag(` literal trong `contracts.py` + `executor.py`; worker start-guard; wave loop.
- **INV-016 Scheduler Separation**: scheduler WRAP `GraphExecutor` (gated runner), chỉ gọi `acquire_slot_wait/release_slot`; `execution_runner.py` adapter 1-node plan; không ThreadPoolExecutor, không `def execute(`.
- **4.12 Anti Fake Test**: đọc body test, không chỉ đếm pass. Đặc biệt `test_observability_arch_health.py::test_m5_*` — chạy scanner trên cây thật (`SRC_ROOT`) và confirm M5 rule thực sự FIRE (không phải dead rule) và không false-positive.

## 5. Tiêu chí chấp nhận (nguồn: PLAN.md §M5 DoD)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|-----------------|---------------------|
| V1 | Memory không truy cập trực tiếp từ Agent (INV-011) | `test_inv011_memory_isolation` + đọc `memory/coordinator.py` | agents chỉ qua ContextService |
| V2 | Context có budget + priority (INV-012) | `test_inv_context_import_allowlist` + đọc `context/optimizer.py` | 7-tier + per-kind budget |
| V3 | Model routing theo policy + fallback (INV-013) | `test_inv013_*` + đọc `models/router/` | selection chỉ qua router |
| V4 | Planner tạo task graph (INV-014) | `test_inv014_*` + đọc `planning/engine.py` | validate trước khi trả |
| V5 | Graph hỗ trợ dependency + parallel (INV-015) | `test_inv015_*` + đọc `kernel/graph/` | validate_dag literal |
| V6 | Scheduler không sở hữu Resource/Execution (INV-016) | `test_inv016_*` + đọc `kernel/scheduler/` | wrap executor, chỉ acquire/release |
| V7 | INV-011..016 enforced bằng AST tests | chạy `test_architecture.py` INV-011..016 | 17 test pass trên cây thật |
| V8 | Observability đầy đủ (§M5 DoD) | runtime `ArchitectureHealth.scan(SRC_ROOT)` + `test_m5_real_src_healthy` | healthy=True gồm M5 (sau F1 fix) |

## 6. Phương pháp review (bắt buộc)

1. Đọc thực tế từng file mục 3 — không tin mô tả.
2. Với mỗi tiêu chí mục 5: tìm bằng chứng → PASS/FAIL/INCONCLUSIVE + trích dẫn `file:line`.
3. Áp dụng mục 4.1–4.12, kết luận từng nguyên tắc.
4. Cross-check PROGRESS.md ↔ LOG.md ↔ `git log --oneline`.
5. Tìm lỗ hổng chủ động: stub, claim không bằng chứng, test pass nhưng không test đúng (4.12), **runtime arch-health báo healthy giả do KHÔNG quét M5** (F1).
6. Đếm đủ 8 file mỗi task (6 task M5).
7. Phân mức: P1 (sai mục tiêu/tiêu chí), P2 (thiếu sót đáng sửa), P3 (góp ý nhỏ).

## 7. Format báo cáo (giống template mục 7)

```markdown
# Review M5 — bởi <reviewer>
## 1. Bảng đối chiếu tiêu chí (V1–V8)
## 2. Architecture Compliance (INV-011..016)
## 3. Findings (P1/P2/P3 + đề xuất)
## 4. Kết luận (đạt/không đạt + điều kiện)
```
