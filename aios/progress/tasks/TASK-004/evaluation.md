# Evaluation — TASK-004

## Kết quả đối chiếu tiêu chí chấp nhận
**13/13 AC PASS** — chi tiết tại `test.md`. 162 tests pass, coverage 94.77%.

## Đánh giá hệ thống tổng thể
- Critique ×2 bắt: path traversal guard `startswith` (bypass thật), `list()` thiếu cơ chế persist (sidecar), mâu thuẫn timebase `created` vs monotonic, pending lifecycle mâu thuẫn giữa 3 chỗ trong spec, fake clock trap (`init=False`).
- Reviewer xác nhận không R1 — 5 R2 vá nhẹ (không đổi kiến trúc).
- Implement phát hiện 2 lỗi thật (import path, publish signature) — test bắt ngay.
- Nền cho TASK-005: PermissionService/Pending → Permission Broker, PolicyService pre-check → Execution, ArtifactService sidecar → Artifact Browser M3, EventService audit → Observability P8.

## Bài học (bổ sung STATS.md)
1. **Path guard phải dùng `is_relative_to` sau resolve** — `startswith` prefix string bị bypass bằng thư mục sibling (`artifacts2`).
2. **Persistence phải có cơ chế tường minh từ spec** — `list()` cần sidecar, không thể "tự bịa lúc code".
3. **Một khái niệm một định nghĩa** — "pending" xuất hiện 3 chỗ với 2 nghĩa; spec phải nhất quán.
4. **Timebase không trộn**: metadata `created: datetime` + TTL `_created_mono` (monotonic) tách bạch.
5. **EventBus.publish nhận Event object** — wrapper service phải tạo Event trước.

## Kết luận
- [x] **ĐẠT spec (13/13 AC)** — TASK-004 done, sẵn sàng TASK-005 (Scheduler/State/Resource/Execution + RuntimeKernel).
