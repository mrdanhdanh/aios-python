# Review — TASK-008 (Pre-Implementation)

## Tổng quan
Verify code nền: baseline 270 tests ✓, ExecutionService ctor pattern ✓, policy AC4 ✓, merge semantics khớp engine ✓, refactor dag an toàn ✓, editable-install ✓ (chạy `python -m` được). **APPROVED** — 2 R2 + 3 R3.

## Vấn đề + Resolution

### R2-1 — tasks.md thiếu bước cập nhật test_import.py
- **Resolution**: thêm checkbox vào I2.4: "cập nhật test_import.py + test_exports_present".

### R2-2 — Default retries/timeout_s cấp definition chưa chốt
- **Resolution**: chốt `WorkflowDefinition.retries: int = 0`, `timeout_s: float = 300.0` (khớp PlanNode default — merge 3 tầng rõ ràng).

### R3 (áp khi implement)
1. Ghi chú AC9: main() + monkeypatch vẫn đúng (aios_core đã editable-install — bỏ claim "subprocess fail")
2. CLI lazy-import trong main() (tránh module-level chạy 2 lần với `python -m`)
3. `from . import workflow` đặt sau block kernel; baseline = 270 test

## Kết luận
- [x] **APPROVED — 2 R2 + 3 R3 resolve khi implement.**
