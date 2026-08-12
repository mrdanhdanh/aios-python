# Critique vòng 1 — TASK-012 (M2-P3b: Goal Manager + Task Queue + Permission Broker + Failure Recovery)

> Ngày: 2026-08-12 | Reviewer: critic subagent (vòng 1) | Spec: `spec.md`

## Đánh giá chung

**Điểm sẵn sàng: 3/5 — CẦN SỬA TRƯỚC KHI IMPLEMENT.**

Spec rất kỹ, bài học áp dụng đúng (sleeper injectable, đọc thẳng DB, state machine tường minh, dequeue rowcount-check). Đối chiếu code thực tế: `EventType` chưa có 6 event mới, `query_audit` tồn tại đúng API, Settings pattern khớp, `OrchestratorError` có sẵn, `PermissionScope`/`PermissionDecision` khớp. **Nhưng có 2 mâu thuẫn thiết kế nghiêm trọng ở PermissionBroker (C1-01) và CancelGoal vs TaskQueue (C1-03), cùng 3 vấn đề Major khác** về crash recovery, race enqueue và event trùng lặp.

## Vấn đề tìm được (16)

| ID | Mức | Vấn đề | Quyết định resolve |
|----|-----|--------|---------------------|
| C1-01 | Critical | `PolicyDecision` không có `ask_scopes`; case `require_approval=True` + mọi scope allowed bị bỏ sót → broker auto-allow sai | **(a)** Thêm `ask_scopes: list[str] = []` vào `PolicyDecision` (additive, an toàn) + broker xử lý `requires_approval=True` → toàn bộ batch ASK |
| C1-02 | Critical | `cancel_goal`/`pause_goal` không định nghĩa ảnh hưởng lên queue items → task vẫn chạy sau cancel | **Cascade**: `cancel_goal` chuyển queue items `queued → cancelled` cùng transaction; `pause_goal` không cascade (ghi rõ giới hạn) |
| C1-03 | Major | Crash giữa chừng: item `running` kẹt vĩnh viễn, claim persist không trọn vẹn | Thêm `recover_stale_running(threshold_s=3600)` gọi lúc khởi tạo TaskQueue + ghi giả định single-process |
| C1-04 | Major | Race `enqueue`: `MAX(position)+1` trong deferred transaction → trùng position | Gộp 1 câu SQL `INSERT ... SELECT COALESCE(MAX(position),0)+1` + `UNIQUE(position)` + test 2 thread |
| C1-05 | Major | `PERMISSION_REQUESTED` phát 2 lần, 2 schema trên bus | Broker không emit `PERMISSION_REQUESTED` riêng — dùng event của PolicyService làm request; broker chỉ emit `PERMISSION_GRANTED`/`PERMISSION_DENIED` với payload thống nhất |
| C1-06 | Minor | Giá trị `EventType` 6 event mới chưa pin | Pin: `goal.created`, `goal.status_changed`, `goal.task_updated`, `queue.updated`, `recovery.retry`, `recovery.fallback` + bảng payload |
| C1-07 | Minor | Approver callback trả ASK hoặc raise: chưa định nghĩa | Approver raise → **DENY** (default-deny) + warning; trả ASK → coi như DENY (approved=False) — ghi + test |
| C1-08 | Minor | Auto-fail "bất kỳ task failed/cancelled → goal failed" quá nhạy | Giữ v1, thêm rationale 1 dòng |
| C1-09 | Minor | `add_task` trên goal terminal + `goal_id`/`task_id` mismatch chưa định nghĩa | `add_task` trên terminal → `GoalError`; mismatch → `GoalError`; + test |
| C1-10 | Minor | Fallback không được retry + wording AC10 | Ghi rõ "retry chỉ áp dụng attempt gốc; fallback 1 lần không retry" + sửa wording AC10 |
| C1-11 | Minor | `collect([])`/batch rỗng chưa định nghĩa | `ValueError("empty scopes")` + test |
| C1-12 | Minor | `reorder` mixed-priority gây hiểu lầm | Giữ nguyên, docstring cảnh báo + test dùng cùng priority |
| C1-13 | Minor | `GoalsSettings.db_path` chết — không nơi nào dùng | Thêm factory `build_goal_modules()` trong `goals/__init__.py` + test dùng `Settings().goals.db_path` |
| C1-14 | Minor | `PolicyRequest(internet=False)` hardcode | Ghi rõ giới hạn cố ý (gating thật ở ExecutionService) |
| C1-15 | Minor | Emit event khi thành công hay cả khi fail | "Events chỉ emit khi thao tác thành công; exception không emit" + test negative |
| C1-16 | Minor | `enqueue` với `goal_id`/`task_id` lạ không validate | Ghi rõ "enqueue không validate sự tồn tại (queue decoupled)" + test |

## Kết luận vòng 1

- [x] **Cần sửa trước khi implement** — danh sách bắt buộc: C1-01, C1-02 (Critical), C1-03, C1-04, C1-05 (Major) + toàn bộ P3 cùng đợt (tránh lặp ở vòng 2).
- Khả thi chung: **đạt** — code hiện có khớp hầu hết spec; các sửa là additive, không phá baseline 428 test.

**Trạng thái: RESOLVED 16/16** (spec.md đã được cập nhật theo bảng trên — xem commit kèm theo).
