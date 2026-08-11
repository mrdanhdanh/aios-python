# Review — TASK-005 (Pre-Implementation)

## Tổng quan
2 vòng critique resolve đầy đủ; reviewer verify DI-safe từng service với container.py thật (EventService/ArtifactService/ContextService/ResourcesSettings → register_instance bắt buộc — đúng). 15/15 AC kiểm chứng được. **CHANGES REQUESTED: 2 R1 (clarification) + 2 R2 + 2 R3.**

## Vấn đề + Resolution

### R1-1 — Mâu thuẫn "execute reset cancel flag" vs "cancel trước execute → CANCELLED ngay"
- **Resolution**: quy định thứ tự: execute() **kiểm tra pending cancel TRƯỚC → có → trả CANCELLED ngay (không reset, không chạy); không có → reset state + flag → chạy**.

### R1-2 — RuntimeKernel.create thiếu register_instance(EventBus)
- **Resolution**: thêm `register_instance(EventBus, bus)` — khớp AC12 "9 services + bus" + DI chain PolicyService → EventBus.

### R2-1 — tasks.md quá thô (1 checkbox/8 AC)
- **Resolution**: F3.1 liệt kê tên test case theo AC (test_interval_skips_overlap, test_cancel_before_execute_immediate, test_snapshot_fallback_repr...).

### R2-2 — ExecutionService ctor chưa pin
- **Resolution**: pin `ExecutionService(event_service: EventService, policy_service: PolicyService, state_service: StateService, resource_service: ResourceService)`.

### R3 — (áp khi implement)
1. AC1 dùng real tiny sleep (delay 0.05s) + margin; không cần sleep_fn param
2. AC6 test runner dùng threading.Event kiểm soát thread cũ (song song attempt) trước khi assert

## Kết luận
- [x] **Resolve toàn bộ (2 R1 + 2 R2 + 2 R3)** — spec + tasks.md cập nhật, sẵn sàng implement.
