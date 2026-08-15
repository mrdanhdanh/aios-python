# AIOS M5 Core Intelligence — notes

- M5 HOÀN TẤT 2026-08-15: 1086 tests pass (baseline M4 809 + 277), coverage 95.22%.
- 6 task: TASK-023 Memory Coordinator (`memory/coordinator.py`), TASK-024 Context Optimizer (`context/optimizer.py`), TASK-025 Model Router (`models/router/` 8 file), TASK-026 Planning Engine (`orchestrator/planning/` 11 file), TASK-027 Execution Graph (`kernel/graph/` 6 file), TASK-028 Parallel Scheduler (`kernel/scheduler/` 5 file).
- 6 invariant mới INV-011..016 enforced bằng AST allow-list tests trong `tests/test_architecture.py` (17 test: test_inv011/012/013/014/015/016_*).
- **Review M5 (2026-08-15, self-review)**: M5 ĐẠT V1–V8, không P1. 2 finding tự sửa:
  - **F1 (P2)**: runtime `ArchitectureHealth.scan()` (`observability/arch_health.py`) KHÔNG cover M5 packages → vi phạm PLAN §M5 "observability đầy đủ". Đã thêm 6 M5 layer rule (forbidden downward imports, mirror allow-list test_architecture.py) + 6 test regresi (test_m5_*) trong `tests/test_observability_arch_health.py`. Scanner trên SRC_ROOT → healthy=True, 0 violations.
  - **F2 (P3)**: M5 thiếu milestone review doc → đã viết `reviews/M5-review.md` + `reviews/M5-review-brief.md`.
- Cảnh báo: working tree có M9 Autonomous IN-PROGRESS (broken: `autonomous/__init__.py:135` NameError `objective`) — KHÔNG liên quan M5. M5 commit riêng, không đụng M9.
- Lesson: PLAN yêu cầu "observability đầy đủ" cho mỗi milestone → runtime arch scanner phải cover các package của milestone đó (không chỉ test_architecture.py). Khi review milestone mới, luôn kiểm tra `_LAYER_RULES` trong arch_health.py đã cover chưa.
