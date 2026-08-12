# Review — TASK-012 (M2-P3b: Goal Manager + Task Queue + Permission Broker + Failure Recovery)

> Ngày: 2026-08-12 | Reviewer: reviewer agent | Giai đoạn: REVIEW TRƯỚC KHI IMPLEMENT
> Đã đọc: spec.md (12 AC), tasks.md (T1–T8), critique-1.md (16), critique-2.md (15), code kernel (events.py, services/events.py, services/policy.py, services/permissions.py, services/execution.py, config.py, orchestrator/errors.py, orchestrator.py, __init__ chain), STATS.md, PLAN.md
> Bằng chứng thực tế: pytest → **428 passed in 7.50s** (baseline xanh); python 3.13.14 | sqlite 3.50.4 (RETURNING OK)

## Tổng quan

Spec xây 4 module Control Plane (`orchestrator/goals/`) thuần deterministic, offline-first, persist SQLite. Đã kiểm chứng đối chiếu code thực tế:
- `EventType` hiện có 19 giá trị, `ERROR_OCCURRED="error.occurred"` đã tồn tại → +6 additive, không test nào enumerate toàn bộ members ✅
- `PolicyDecision` là `@dataclass`, chỉ được construct bằng kwargs tại 5 nhánh return của `evaluate` → thêm `ask_scopes` additive ✅ (nhớ thêm `field` vào import `from dataclasses import`)
- `EventService.emit(event_type, payload, source)` + `query_audit(limit, event_type)` khớp ✅
- `Settings` guard dựa trên `model_fields` → thêm `goals` + config.yaml cùng commit an toàn ✅
- SQLite 3.50.4 ≥ 3.35 → dequeue `UPDATE ... RETURNING *` khả thi ✅

## Phần 1: Đối chiếu AC ↔ test

**11/12 AC phủ đầy đủ; AC11 phủ đủ nhưng thiếu 2 assertion audit nhỏ (R6).** Mọi AC 1–12 có test tương ứng trong test plan (xem bảng chi tiết trong spec mục 8).

## Phần 2: Rủi ro implement (R1–R6)

| ID | Mức | Vấn đề | Cách tránh (bắt buộc) |
|----|-----|--------|------------------------|
| R1 | Major | Cascade `cancel_goal` UPDATE `queue_items` → crash `no such table` nếu app chỉ khởi tạo GoalManager (TaskQueue chưa từng tạo bảng) | **Shared DDL 3 bảng trong `goals/__init__.py`** (hoặc đảo T4 trước T3); test GoalManager-only cancel |
| R2 | Major | Thứ tự T3.5 (cascade) cần DDL queue_items của T4.1 | Shared DDL giải quyết; ghi 1 dòng vào tasks.md |
| R3 | Major | `evaluate` quên set `ask_scopes` ở 1 trong 5 nhánh → bug âm thầm; quên import `field` → ImportError | Set ở ĐỦ 5 nhánh (deny/token/internet/approval/allow); test assert cả 5 nhánh; thêm `field` vào import dataclasses |
| R4 | Minor | `recover_stale_running` so sánh string ISO → sai; spec im lặng về event recover | `datetime.fromisoformat(updated_at)` so với `datetime.now(timezone.utc)`; **emit `QUEUE_UPDATED` action="recover" per item** + 1 assertion test |
| R5 | Minor | `cancel_goal` không định nghĩa ảnh hưởng lên `goal_tasks.status` | **Cascade: mọi task không terminal → `cancelled`** (nhất quán) |
| R6 | Minor | Thiếu 3 assertion: `PERMISSION_REQUESTED.source == batch.id`; audit có QUEUE_UPDATED; payload round-trip | Thêm vào test plan (đã cập nhật) |

## Phần 3: Ràng buộc dự án

| Ràng buộc | Trạng thái |
|-----------|-----------|
| Offline-first, không LLM | ✅ 4 module thuần deterministic, sleeper injectable |
| Kernel đóng băng (M1) | ✅ Chỉ EventType +6, PolicyDecision.ask_scopes, Settings.goals — toàn additive; RuntimeKernel/ExecutionService/Orchestrator KHÔNG sửa |
| Persist qua phiên | ✅ goals.db 3 bảng, đọc thẳng DB không cache |
| Baseline 428 test | ✅ đã chạy thật trước implement |
| State machine + CHECK | ✅ tường minh + tầng bảo vệ thứ 2 |

## Kết luận

- [x] **APPROVED** — đủ điều kiện implement
- Điều kiện kèm (bắt buộc xử lý, không blocking spec):
  1. R1+R2: shared DDL 3 bảng trong `goals/__init__.py` — chống `no such table` khi cascade cancel với GoalManager-only
  2. R3: set `ask_scopes` ở đủ 5 nhánh `evaluate` + thêm `field` vào import dataclasses; test assert cả 5 nhánh
  3. R4–R6: parse ISO stale recovery + emit QUEUE_UPDATED "recover"; cascade task → cancelled khi cancel goal; bổ sung 3 assertion audit

Top 3 rủi ro: (1) cascade cancel crash khi queue_items chưa tồn tại — shared DDL; (2) quên set ask_scopes 1/5 nhánh — test từng nhánh; (3) reorder 2 pha — check `set(item_ids) == set(queued_ids)` trước.
