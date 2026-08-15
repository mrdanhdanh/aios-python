# Review M4 — bởi AIOS Orchestrator (self-review, độc lập với kết quả trước)

> **Chế độ review:** **M4-Platform Edition Review** (TASK-020 Upgrade Pipeline, TASK-021 Observability & Diagnostics, TASK-022 Orchestrator v2 — đã done, 809 tests @ M4 close, full suite 1636 passed sau fix).
> **Phương pháp:** đọc thực tế code + spec + chạy test thật + chạy scanner trên cây thật. Tự phát hiện + tự sửa (tự chỉnh sửa) trước khi ghi nhận.

---

## 1. Bảng đối chiếu tiêu chí (V1–V8)

| # | Tiêu chí (nguồn: PLAN.md §Verification M4 + task specs) | Kết quả | Bằng chứng (file + trích dẫn) |
|---|---|---|---|
| V1 | Upgrade pipeline 6 bước + event + rollback | **PASS** | `backend/tests/test_upgrade_pipeline.py` — ok sequence `STARTED→COMPATIBILITY_OK→DEPENDENCIES_OK→BACKUP_CREATED→MIGRATED→HEALTH_OK→COMPLETED`; 4 fail path (compat/dep/health/migrate) + rollback. `upgrade/pipeline.py::run`. |
| V2 | Observability: metrics/prompt-history/profiler/doctor/arch-health/eval v2 | **PASS** | `test_observability_metrics.py` (duration ghép đúng + orphan), `test_observability_evaluation.py` (COMPLETED→success, FAILED+CANCELLED→failed), `test_observability_doctor.py` (worst-wins), `test_observability_arch_health.py`. |
| V3 | Orchestrator v2: advisor/supervisor/collector/goal reporter | **PASS** | `test_advisor.py` (5 rules + dedup + None quality), `test_supervisor.py` (stuck + close), `test_evaluation_collector.py`, `test_goal_reporter.py` (5 status, failed=FAILED+CANCELLED). |
| V4 | Architecture: agent→capability→tool, policy-first, DI, event-driven | **PASS** | `test_architecture.py` allow-list `upgrade/` + `observability/` active; AC9/AC10 pass. `metrics.py` event-driven (bus.subscribe). |
| V5 | API 5 GET observability + 1 POST feedback + 4 GET orchestrator-v2 | **PASS** | `test_observability_api.py` (metrics/doctor/arch-health/evaluations + feedback 404/422), `test_orchestrator_v2_api.py` (4 endpoint). |
| V6 | CLI: `aiagent upgrade` / `doctor` / `metrics` / `arch-health` / `advisor` / `supervisor` | **PASS** | `test_upgrade_cli.py` (dry-run/thật, exit codes, not wired), `test_cli.py` (doctor output giữ key kernel). |
| V7 | Process: 8-file hard gate mỗi task (TASK-020/021/022) | **PASS** | `file_search` `aios/progress/tasks/TASK-020|021|022/` → đủ spec/critique-1/critique-2/tasks/review/test/evaluation (+ implementation trong spec). |
| V8 | Tests chạy thật | **PASS** | M4 close: `809 passed, 94.92%`; sau review+fix: full suite `1636 passed, 0 fail`. |

**Tổng kết:** V1–V8 = **PASS** (sau khi tự sửa 1 P1 — xem Finding F1).

---

## 2. Architecture Compliance (mục 4.1–4.12)

| Nguyên tắc | Kết quả | Trích dẫn |
|---|---|---|
| INV-001/002 (Runtime/Execution Plane) | **PASS** | M4 không thêm agent/tool; advisor/supervisor read-only, không chạm Tool trực tiếp. |
| INV-003 Control/Execution Plane | **PASS** | `orchestrator/advisor.py` đọc qua `EvaluationStore`/`MetricsService`/`PromptHistory` (capability layer), không query infra trực tiếp. |
| INV-004 Capability-first | **PASS** | Upgrade/Supervisor không gọi Tool. |
| INV-005 DI | **PASS** | `api/wiring.py::_build_orchestrator_v2` resolve từ regs; CLI lazy import. |
| INV-007 Hard call-site (policy) | **PASS** | `arch_health.py` policy scan duy trì check `self._policy.evaluate` trong `execution.py`. |
| INV-009 Event Driven | **PASS (runtime)** | `metrics.py`, `evaluation.py`, `supervisor.py`, `pipeline.py` subscribe bus; execution emits FAILED×6 + CANCELLED×2 (xác nhận trong `test_execution_failed_events.py`). |
| INV-010 Testability / Determinism | **PASS** | Không LLM trong advisor; clock injectable; full suite pass. |
| Anti-fake-test (4.12) | **PASS** | Đọc body test: assertions cover duration pairing (`metrics.py` UPDATE latest unfinished row), failed=FAILED+CANCELLED, advisor rules, supervisor stuck; không `assert True` rỗng. |
| Architecture Health (M4) | **FAIL → FIXED** | xem Finding F1. |

---

## 3. Acceptance Traceability Matrix

| AC | Implementation | Test | Runtime Evidence | Kết quả |
|----|----------------|------|------------------|---------|
| Upgrade ok sequence (V1/AC3) | `upgrade/pipeline.py::run` | `test_upgrade_pipeline.py` | event fired đúng thứ tự | PASS |
| Metrics duration (V2/AC1) | `observability/metrics.py::_on_event` | `test_observability_metrics.py` | re-run → row mới nhất | PASS |
| Eval semantics (V2/AC6) | `observability/evaluation.py::_on_event` | `test_observability_evaluation.py` | COMPLETED→success, FAILED+CANCELLED→failed | PASS |
| Advisor 5 rules (V3/AC1) | `orchestrator/advisor.py::suggest` | `test_advisor.py` | mỗi rule sinh suggestion đúng | PASS |
| Supervisor stuck (V3/AC2) | `orchestrator/supervisor.py::snapshot` | `test_supervisor.py` | clock injectable | PASS |
| Arch health on real tree (V2/AC5) | `observability/arch_health.py::scan` | `test_observability_arch_health.py` **+ 2 test regresi mới** | chạy scanner trên `SRC_ROOT` → `healthy=True, 0 violations` (trước fix: skip silent) | PASS (sau fix) |

---

## 4. Findings

| ID | Mức | Mô tả | File liên quan | Đề xuất / Trạng thái |
|----|-----|-------|----------------|----------------------|
| **F1** | **P1** | **ArchitectureHealth.scan() bỏ qua TOÀN BỘ layer/contract check trên cây thật.** `scan(package_dir=SRC_ROOT)` với `SRC_ROOT = backend/src`, nhưng code dùng `target = package_dir / sub` (vd `backend/src / "agents"`). Thực tế `agents/` nằm dưới `backend/src/aios_core/agents` → `target.is_dir()` = False → `continue` → mọi layer/contract check bị skip **silent**. Chỉ policy check chạy (vì nó hardcode `"aios_core"` prefix). Hệ quả: tính năng "Architecture Health" M4 không quét được cây thật, luôn báo healthy giả. Thêm nữa: `rel` truyền vào `collect_imports` ở dạng **dot-form** (`"aios_core.orchestrator.planner"`) trong khi hàm expects **slash-form** (`"aios_core/orchestrator/planner"`) → `pkg_dotted` tính sai → relative import bị phân giải sai, forbidden relative import không bị bắt. | `backend/src/aios_core/observability/arch_health.py` (`scan`) | **ĐÃ TỰ SỬA**: tính `aios_root = package_dir/"aios_core" if exists else package_dir`; truyền `rel` slash-form; exempt so sánh slash-form. Thêm 2 test regresi (`test_nested_aios_core_layout_scans_layer_violations`, `test_nested_aios_core_layout_policy_check`). |
| F2 | P3 | `orchestrator/__init__.py` không export các module M4 mới (ImprovementAdvisor/ExecutionSupervisor/EvaluationCollector/GoalReporter) — trong khi `observability/__init__.py` export đầy đủ. Không phải bug (mọi nơi import từ submodule path `..orchestrator.advisor`), nhưng là inconsistency về mặt "package public API". | `backend/src/aios_core/orchestrator/__init__.py` | Ghi nhận, không sửa (nguy cơ circular import nếu thêm export tuần tự). Có thể làm sau cùng M10 freeze. |
| F3 | P3 | Advisor rule 1 (low quality) và rule 5 (slow) cùng `(kind=workflow, action=improve, target=workflow_id)` → dedup collapse thành 1 suggestion nếu 1 workflow vừa low-quality vừa slow. Theo spec dedup `(kind,target,action)` → đúng thiết kế, nhưng evidence của suggestion giữ lại chỉ 1 nhóm. Chấp nhận. | `orchestrator/advisor.py::suggest` | Không sửa (đúng spec). |

---

## 5. Kết luận

- **M4 đạt** các tiêu chí V1–V8 sau khi tự sửa F1 (P1).
- F1 là defect thực sự (không phải process gap): feature Architecture Health được quảng cáo ở M4 nhưng trên cây thật không quét được layer/contract violations do lỗi base-directory + sai định dạng module path. Đã fix + có test regresi khóa hành vi.
- F2/F3 là P3 (observation), không ảnh hưởng functional correctness.
- Toàn bộ test: `1636 passed, 0 fail` (sau fix).
