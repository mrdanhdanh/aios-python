# Milestone Review Brief — M4 (Platform Edition)

> **Mục đích**: tài liệu tự chứa để đem cho model/người review ĐỘC LẬP đánh giá M4.
> **Cách dùng**: copy file này sang model review. Model tự đọc repo + chạy test, trả báo cáo theo mục 7 của REVIEW-BRIEF-TEMPLATE.md. KHÔNG sửa file.
> **Lưu ý reviewer**: M4 đã có 1 self-fix (F1) ghi trong `reviews/M4-review.md` — reviewer独立 đánh giá lại từ code thực tế, không bị ảnh hưởng bởi kết luận đó.

---

## 1. Bối cảnh dự án

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình hard gate cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate.

Đọc bắt buộc:
- `docs/PLAN.md` — master plan, **đặc biệt mục "M4 – Platform Edition (P7–P8)"** + mục "Architecture Health (kế hoạch M4 — P8)".
- `AGENTS.md` — quy tắc vận hành.
- `docs/adr/` — ADR-0004 (architecture invariants).

## 2. Nhiệm vụ

Review milestone **M4** — Platform Edition: Upgrade Pipeline (P7) + Observability & Diagnostics + Orchestrator v2 (P8).
Đánh giá độc lập 4 khía cạnh: (1) đúng phạm vi, (2) đúng quy trình 8-file hard gate, (3) hồ sơ nhất quán, (4) kiến trúc & runtime correctness.

## 3. Deliverable cần kiểm tra

**Code (đọc thực tế):**
- `backend/src/aios_core/upgrade/` (pipeline.py, dependency.py, backup.py, migrator.py, errors.py)
- `backend/src/aios_core/observability/` (metrics.py, prompt_history.py, profiler.py, doctor.py, arch_scan.py, arch_health.py, evaluation.py)
- `backend/src/aios_core/orchestrator/` (advisor.py, supervisor.py, evaluation_collector.py, goals/reporting.py)
- `backend/src/aios_core/kernel/services/execution.py` (FAILED/CANCELLED emits)
- `backend/src/aios_core/api/routers/observability.py`, `api/routers/orchestrator_v2.py`, `api/wiring.py`
- `backend/src/aios_core/workflow/cli.py` (upgrade/doctor/metrics/arch-health/advisor/supervisor)

**Tests (chạy thật):**
- `backend/tests/test_upgrade_*.py`, `test_observability_*.py`, `test_execution_failed_events.py`, `test_advisor.py`, `test_supervisor.py`, `test_evaluation_collector.py`, `test_goal_reporter.py`, `test_orchestrator_v2_api.py`, `test_architecture.py`

**Hồ sơ quy trình (mỗi task đủ 8 file):**
- `aios/progress/tasks/TASK-020/`, `TASK-021/`, `TASK-022/` (spec, critique-1, critique-2, tasks, review, test, evaluation)

## 4. Architecture & Runtime Deep Review (TRỌNG TÂM)

Áp dụng mục 4.1–4.12 của template. Đặc biệt chú ý:
- **4.5 Layer Isolation**: agent/observer không gọi Tool/infra trực tiếp.
- **4.7 Event Review**: xác minh `execution.py` thực sự emit WORKFLOW_FAILED (6 nhánh) + WORKFLOW_CANCELLED (2 nhánh); metrics/evaluation/supervisor subscribe đúng.
- **4.12 Anti Fake Test**: đọc body test, không chỉ đếm pass. Đặc biệt test `arch_health` — chạy scanner trên cây thật (`SRC_ROOT`) và confirm nó thực sự quét được layer/contract (KHÔNG chỉ báo healthy giả do skip silent).
- **M4-specific**: ArchitectureHealth.scan() phải hoạt động trên layout thật `backend/src/aios_core/...` (nested), không chỉ trên flat test fixture.

## 5. Tiêu chí chấp nhận (nguồn: PLAN.md §M4 + task specs)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|-----------------|---------------------|
| V1 | Upgrade pipeline 6 bước + event + rollback | đọc `pipeline.py` + `test_upgrade_pipeline.py` | sequence event đúng, 4 fail path + rollback |
| V2 | Observability đầy đủ | đọc `metrics.py`/`evaluation.py`/`doctor.py`/`arch_health.py` + tests | duration ghép đúng, failed=FAILED+CANCELLED, arch-health scan cây thật |
| V3 | Orchestrator v2 | đọc `advisor.py`/`supervisor.py`/`evaluation_collector.py`/`reporting.py` + tests | 5 rules, stuck, collect_all, 5 status |
| V4 | Architecture: capability-first/policy/DI/event | `test_architecture.py` allow-list + đọc wiring | INV-009/010 giữ |
| V5 | API observability + orchestrator-v2 | `test_observability_api.py` + `test_orchestrator_v2_api.py` | 5 GET + 1 POST + 4 GET |
| V6 | CLI upgrade/doctor/metrics/arch-health/advisor/supervisor | `test_upgrade_cli.py` + `test_cli.py` | exit codes, output |
| V7 | 8-file hard gate | `file_search` tasks/TASK-020/021/022 | đủ spec/critique-1/critique-2/tasks/review/test/evaluation |
| V8 | Tests chạy thật | chạy pytest backend | ≥ 809 passed (M4 close) |

## 6. Phương pháp review (bắt buộc)

1. Đọc thực tế từng file mục 3 — không tin mô tả.
2. Với mỗi tiêu chí mục 5: tìm bằng chứng → PASS/FAIL/INCONCLUSIVE + trích dẫn `file:line`.
3. Áp dụng mục 4.1–4.12, kết luận từng nguyên tắc.
4. Cross-check PROGRESS.md ↔ LOG.md ↔ `git log --oneline`.
5. Tìm lỗ hổng chủ động: stub, claim không bằng chứng, test pass nhưng không test đúng (4.12), **arch-health báo healthy giả do skip silent trên cây thật**.
6. Đếm đủ 8 file mỗi task.
7. Phân mức: P1 (sai mục tiêu/tiêu chí), P2 (thiếu sót đáng sửa), P3 (góp ý nhỏ).

## 7. Format báo cáo (giống template mục 7)

```markdown
# Review M4 — bởi <reviewer>
## 1. Bảng đối chiếu tiêu chí (V1–V8)
## 2. Architecture Compliance (4.1–4.12)
## 3. Findings (P1/P2/P3 + đề xuất)
## 4. Kết luận (đạt/không đạt + điều kiện)
```
