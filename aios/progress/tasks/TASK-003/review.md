# Review — TASK-003 (Pre-Implementation)

## Tổng quan
Spec đã qua 2 vòng critique (20 resolution đều áp vào spec). Reviewer verify tay 5-rule compatibility với 8 case AC2 + 4 case AC17 + invariant — **không còn mâu thuẫn**. 19/20 AC được checklist phủ. **CHANGES REQUESTED**: 1 R1 + 2 R2 + 4 R3.

## Đối chiếu AC ↔ checklist
19/20 AC phủ trực tiếp. AC13/AC14 có lỗ hổng → R2-2/R1.

## Vấn đề + Resolution

### R1 — tasks.md thiếu bước cập nhật `aios_core/__init__.py` (Blocking)
- Vấn đề: AC14 cần `from aios_core import contracts, Container, ...` nhưng `__init__.py` hiện chỉ export config/healthcheck/logging/metadata; tasks.md không nhắc sửa.
- **Resolution**: thêm vào D4.3: "cập nhật `aios_core/__init__.py`: export `contracts`, `Container`, `ContainerError`, `EventBus`, `ExecutionPlan`, `ExecutionPlanBuilder`".

### R2-1 — `flush()` chưa pin hành vi khi handler async raise (Major)
- Vấn đề: `await flush()` có thể re-raise exception handler (thứ tự done_callback vs awaiter không đảm bảo) → AC10 caplog flaky.
- **Resolution**: pin "`flush()` KHÔNG re-raise exception của handler (đã được done_callback log); implement bằng `gather(..., return_exceptions=True)`".

### R2-2 — AC13 "pytest (backend/ + root)" không khả thi nguyên văn (Major)
- Vấn đề: root không có pytest config (pythonpath/cov) → `pytest` từ root không enforce.
- **Resolution**: D5.1 pin lệnh: `backend/.venv/Scripts/python -m pytest` (cwd = `backend/`) → pass + coverage ≥ 80%; từ root chỉ smoke import (không bắt buộc full test).

### R3-1 — Số test file không nhất quán (4 vs 5)
- **Resolution**: sửa Yêu cầu 6: "5 file test riêng (test_semver, test_contracts, test_container, test_event_bus, test_execution_plan)".

### R3-2 — `register_instance` exception type chưa pin
- **Resolution**: vi phạm scope → `ContainerError` (nhất quán container).

### R3-3 — `Subscription` chưa trong exports
- **Resolution**: export `Subscription` từ `kernel/__init__.py` + test nhỏ.

### R3-4 — `semver.py` duplicate regex
- **Resolution**: `semver.py` import `SEMVER_RE` từ `.metadata` (1 chiều, không circular) — 1 nguồn sự thật.

## Kết luận
- [x] **Resolve toàn bộ (1 R1 + 2 R2 + 4 R3)** — tasks.md + spec cập nhật, sẵn sàng implement.

*(Nội dung review gốc do subagent reviewer; resolution bởi AIOS Orchestrator.)*
