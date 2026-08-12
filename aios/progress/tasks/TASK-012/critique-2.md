# Critique vòng 2 — TASK-012 (M2-P3b)

> Ngày: 2026-08-12 | Reviewer: critic subagent (vòng 2) | Spec: `spec.md` (đã sửa sau vòng 1)

## Đánh giá chung

**Điểm sẵn sàng: 3/5 — CẦN SỬA TRƯỚC KHI IMPLEMENT.**

Vòng 1 xử lý đúng 13/16; vòng 2 phát hiện: C1-05 FAIL (spec đi ngược quyết định), mâu thuẫn do resolution C1-04 tạo ra (UNIQUE(position) vs reorder — hỏng AC5), `Field` trên dataclass PolicyDecision, factory không lấy được bus từ EventService.

## Mục A — Verify 16 resolutions vòng 1

| ID | Verdict | Ghi chú |
|----|---------|---------|
| C1-01 | ⚠️ snippet sai | `PolicyDecision` là `@dataclass` — phải `field(default_factory=list)` (dataclasses), không phải pydantic `Field` → C2-06 |
| C1-02 | ✅ | Cascade an toàn với race dequeue (cả 2 UPDATE có WHERE status='queued') |
| C1-03 | ✅ | recover_stale_running + giả định single-process ghi rõ |
| C1-04 | ⚠️ | Đúng cho enqueue, NHƯNG UNIQUE(position) xung đột reorder → C2-01 (Critical) |
| C1-05 | ❌ FAIL | Spec vẫn cho broker emit PERMISSION_REQUESTED schema khác policy → C2-04 (re-decide) |
| C1-06 | ✅ | 6 giá trị pin đúng, không sót tên event |
| C1-07 | ⚠️ | Đúng nhưng EventType warning chưa pin → C2-09 |
| C1-08..C1-12 | ✅ | Đúng |
| C1-13 | ⚠️ | Factory cần bus nhưng EventService không expose bus → C2-03 (Major) |
| C1-14 | ✅ | Ghi chú giới hạn |
| C1-15 | ⚠️ | Chỉ restate ở GoalManager; thiếu cho TaskQueue/Broker + test negative → C2-15 |
| C1-16 | ✅ | Đúng |

**Kết quả: 13/16 đúng, 1 FAIL (C1-05), 2 thiếu (C1-13, C1-15), 1 snippet sai (C1-01).**

## Mục B — Vấn đề mới (15)

| ID | Mức | Vấn đề | Quyết định resolve |
|----|-----|--------|---------------------|
| C2-01 | Critical | UNIQUE(position) immediate → reorder 1 pha đụng position → IntegrityError, AC5 tự hỏng | **reorder 2 pha trong 1 transaction** (pha 1: gán position tạm âm `-(i+1)`; pha 2: gán 0..n-1) + **bắt buộc `item_ids` = đủ mọi item queued** (thiếu/thừa/không tồn tại → `QueueError`) — deterministic, không lộ IntegrityError |
| C2-02 | Major | `get_goal` "order theo position" nhưng `goal_tasks` không có cột position | Thêm cột `position INTEGER NOT NULL DEFAULT 0` vào `goal_tasks` (đánh 0..n-1 khi create/add) + `ORDER BY position` |
| C2-03 | Major | Factory "tự tạo PolicyService từ bus của event_service" bất khả thi (không expose bus) | **Bắt buộc `policy_service` trong factory** — `build_goal_modules(settings, event_service, policy_service, approver=None)`; AC12 test truyền `PolicyService(EventBus())` thật |
| C2-04 | Major | C1-05 chưa re-decide: giữ broker emit nhưng schema khác policy | **Chọn (b) có chủ đích**: broker emit `PERMISSION_REQUESTED` payload KHỚP policy `{service: "permission_broker", request_id, scopes, ask_scopes}` (bỏ batch_id/source khỏi payload — để vào `Event.source`); lý do: policy event không qua audit; AC8 assert schema này |
| C2-05 | Minor | Dequeue B1/B2: 2 thread → thua cuộc trả None dù queue còn item | Gộp 1 statement `UPDATE ... WHERE id=(SELECT ... LIMIT 1) RETURNING *` (SQLite ≥ 3.35 — Python 3.13 luôn có); ghi docstring |
| C2-06 | Minor | `Field(default_factory=list)` trên dataclass | `ask_scopes: list[str] = field(default_factory=list)` (dataclasses) + mọi nhánh return của evaluate set đủ (deny=[]) |
| C2-07 | Minor | Fallback fail không rõ có emit ERROR_OCCURRED không | **Mọi** lần executor fail (gốc/retry/fallback agent/fallback workflow) đều emit `ERROR_OCCURRED` |
| C2-08 | Minor | QUEUE_UPDATED cho action bulk (reorder/clear) không xác định | reorder → 1 event/item; clear → 1 event tổng (`item_id=None`, kèm `count`) |
| C2-09 | Minor | EventType warning khi approver raise chưa pin | Pin: emit `ERROR_OCCURRED` (payload: service="permission_broker", batch_id, error) |
| C2-10 | Minor | Không code path nào set task `pending → queued` | Ghi choreography v1: sau enqueue, caller gọi `update_task_status(..., QUEUED)` trước dequeue + test tích hợp |
| C2-11 | Minor | `resume_goal` không recompute → goal ACTIVE mãi | `resume_goal` gọi lại auto-status recompute sau khi chuyển ACTIVE + test |
| C2-12 | Minor | Auto-approve mặc định footgun với require_approval=True | **approver=None + policy requires_approval=True → `approved=False` + reason "no approver configured"** (default-deny); chỉ auto-approve khi policy không yêu cầu approval |
| C2-13 | Minor | `progress` goal không tồn tại / `request` batch rỗng chưa định nghĩa | `progress` không tồn tại → `GoalError`; `request` batch rỗng → `ValueError`; thêm test `list_goals` |
| C2-14 | Minor | Không ràng buộc GoalManager/TaskQueue chung db_path | Docstring constructor + factory: "PHẢI dùng chung db_path" (factory dùng 1 path cho cả 2) |
| C2-15 | Minor | AC11 thiếu GOAL_STATUS_CHANGED + negative queue | AC11 thêm `GOAL_STATUS_CHANGED` + test `pause(running) → QueueError → không emit QUEUE_UPDATED`; restate success-only ở 5.2 |

## Kết luận

- [x] **Cần sửa trước khi implement**: C2-01 (Critical) + C2-02/03/04 (Major) + toàn bộ Minor cùng đợt.
- Khả thi chung: **đạt** — toàn bộ additive, không phá baseline 428 test.

**Trạng thái: RESOLVED 15/15** (spec.md đã cập nhật).
