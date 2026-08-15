# M5 — Core Intelligence — Milestone Review (Self-Review)

> **Ngày review**: 2026-08-15
> **Reviewer**: AIOS Orchestrator (self-review — cùng mẫu M4)
> **Phương pháp**: đọc code TASK-023..028 + spec, chạy test thật, chạy architecture scanner trên cây thật (`SRC_ROOT`), đối chiếu PLAN §M5 DoD + INV-011..016.
> **Kết luận**: **M5 ĐẠT** — mọi tiêu chí DoD PASS; 1 finding P2 (F1) đã tự sửa, 1 finding P3 (F2) đã tự sửa. Không có P1.

---

## 1. Phạm vi & Deliverable (PLAN §M5)

M5 = "bộ não vận hành" — 6 task nâng cấp Core Intelligence (không thêm agent/UI):

| Task | Module | Invariant |
|------|--------|-----------|
| TASK-023 Memory Coordinator | `memory/coordinator.py` | INV-011 |
| TASK-024 Context Optimizer | `context/optimizer.py` | INV-012 |
| TASK-025 Model Router | `models/router/` (8 file) | INV-013 |
| TASK-026 Planning Engine | `orchestrator/planning/` (11 file) | INV-014 |
| TASK-027 Execution Graph | `kernel/graph/` (6 file) | INV-015 |
| TASK-028 Parallel Scheduler | `kernel/scheduler/` (5 file) | INV-016 |

Deliverable: Memory Coordinator + Context Optimizer + Model Router + Planning Engine + Execution Graph + Parallel Scheduler.

---

## 2. Tiêu chí chấp nhận (DoD §M5) — V1–V8

| # | Tiêu chí | Kết quả | Bằng chứng |
|---|----------|---------|-----------|
| V1 | Memory không truy cập trực tiếp từ Agent (INV-011) | ✅ PASS | `test_inv011_memory_isolation` + `test_inv_memory_import_allowlist` trên cây thật pass; đọc `memory/coordinator.py` — coordinator là pure orchestrator, agents chỉ qua ContextService (EXECUTION scope) |
| V2 | Context có budget + priority (INV-012) | ✅ PASS | `context/optimizer.py`: 7 tier P0–P6, `MemoryBudget` per-kind, per-tier cap + total budget cut (bottom-up), P0/P1 exempt; `test_inv_context_import_allowlist` pass |
| V3 | Model routing theo policy + fallback (INV-013) | ✅ PASS | `models/router/`: `RoutingPolicy` fail-fast, `FallbackResolver` re-filter rule, `ModelSelector` filter→rank→pick + tie-break; `test_inv013_selection_via_router_only` pass |
| V4 | Planner tạo task graph (INV-014) | ✅ PASS | `orchestrator/planning/engine.py` validate trước khi trả (AST gate `self._validator.validate(`); `validation.py` 8 hạng mục; `test_inv014_*` (4 test) pass |
| V5 | Graph hỗ trợ dependency + parallel (INV-015) | ✅ PASS | `kernel/graph/`: `validate_dag(` literal trong `contracts.py` + `executor.py`; wave loop + READY persist + parallel worker; `test_inv015_*` (5 test) pass |
| V6 | Scheduler không sở hữu Resource/Execution (INV-016) | ✅ PASS | `kernel/scheduler/scheduler.py` WRAP `GraphExecutor` (gated runner), chỉ gọi `acquire_slot_wait/release_slot`; `execution_runner.py` adapter 1-node plan; `test_inv016_*` (6 test) pass |
| V7 | INV-011..016 enforced bằng AST tests | ✅ PASS | `tests/test_architecture.py`: 17 test INV-011..016 chạy trên cây thật đều pass (không skip) |
| V8 | Observability đầy đủ (§M5 DoD) | ⚠️→✅ | **F1** (runtime `ArchitectureHealth.scan()` chưa cover M5) → đã tự sửa (xem §3); baseline: metrics/events đã có |

**Test thực tế chạy lại**: 256 test M5 (`test_memory_coordinator`, `test_context_optimizer`, `test_model_router`, `test_planning_engine`, `test_execution_graph`, `test_parallel_scheduler`, `test_context`) **pass**; 17 INV-011..016 arch test **pass**; 335 arch+M5 test **pass**.

---

## 3. Findings & Tự sửa

### F1 (P2) — Runtime ArchitectureHealth scanner không cover M5 packages
**Phát hiện**: `observability/arch_health.py` (`ArchitectureHealth.scan()`) chỉ quét 4 layer rule cũ (agents/workflow/orchestrator/capabilities) + 1 contract rule + INV-007. PLAN §M5 DoD yêu cầu **"observability đầy đủ"** cho INV-011..016, nhưng runtime scanner (accessible qua `aiagent arch-health` CLI + observability doctor) hoàn toàn không quét `memory/`, `context/`, `models/router/`, `orchestrator/planning/`, `kernel/graph/`, `kernel/scheduler/`.
- Đây KHÔNG phải bug skip như M4 F1 (path resolution đã đúng sau fix M4 — scanner chạy `healthy=True` trên cây thật).
- Nhưng là **gap observability**: một regression import vi phạm INV-011..016 sẽ bị bắt bởi `tests/test_architecture.py` (CI) nhưng **không** bị bắt bởi runtime scanner — không thỏa "observability đầy đủ".

**Tự sửa**:
- Thêm 6 M5 layer rule vào `_LAYER_RULES` (forbidden downward imports, mirror allow-list của `test_architecture.py`, không false-positive vì M5 packages hiện không import các module bị cấm).
- Thêm 6 test regresi trong `tests/test_observability_arch_health.py`:
  - `test_m5_real_src_healthy` — scanner trên `SRC_ROOT` phải xanh (gồm M5)
  - `test_m5_memory_isolation_fires` / `test_m5_context_no_knowledge_fires` / `test_m5_planning_no_models_fires` / `test_m5_graph_no_orchestrator_fires` / `test_m5_scheduler_no_orchestrator_fires` — chứng minh rule M5 thực sự FIRE (không phải dead rule).
- **Verify**: scanner trên cây thật → `healthy=True, violations=0`; 15/15 arch-health test pass (gồm 6 mới).

### F2 (P3) — M5 thiếu milestone review doc
**Phát hiện**: M0/M3/M4 đều có `reviews/Mx-review.md` + `Mx-review-brief.md`. M5 chưa có (chỉ có PROGRESS/LOG ghi done). Vi phạm quy trình "mỗi milestone có review độc lập".
**Tự sửa**: viết `reviews/M5-review.md` (file này) + `reviews/M5-review-brief.md`; cập nhật PROGRESS/LOG/STATS.

---

## 4. Không có P1
Đọc kỹ code 6 module M5 (memory coordinator pipeline, context optimizer 3-level compress + budget cut, model router selection/fallback, planning 8-rule validation, graph wave executor, scheduler gated runner) — logic đúng, deterministic, tuân INV. Không tìm thấy bug mức P1. Chất lượng tương đương M4.

## 5. Kết luận
**M5 ĐẠT** (V1–V8 PASS sau F1). 256 M5 test + 17 INV test + 6 M5 scanner test mới đều xanh. Full suite backend hiện có 38 fail/17 error **KHÔNG liên quan M5** — nằm ở `autonomous/` (M9 in-progress, working tree đang dang dở: `autonomous/__init__.py:135` NameError `objective`). M5 commit riêng, không đụng M9.

## 6. Artifacts
- `backend/src/aios_core/observability/arch_health.py` (thêm 6 M5 layer rule)
- `backend/tests/test_observability_arch_health.py` (thêm 6 M5 test)
- `aios/progress/reviews/M5-review.md`, `M5-review-brief.md`
- `aios/progress/PROGRESS.md`, `LOG.md`, `STATS.md`
