# TASK-043 — Pre-implementation review

## Kết luận
**APPROVED có điều kiện** để implement SDK Python v1.

## Kiểm tra
- Phạm vi đúng M8-E1, không kéo plugin/marketplace vào task.
- Dependency một chiều: SDK độc lập với backend; Client dùng transport injection.
- Public API nhỏ, có thể mở rộng cho TASK-044/045 mà không expose internal.
- DAG validation và DTO strict đáp ứng contract-first.

## Điều kiện bắt buộc khi implement
1. Không import `aios_core`, `backend` hoặc runtime internals trong `sdk/python`.
2. Không chạy side effect mặc định trong SDK tests/quickstart.
3. Response từ transport phải được chuẩn hóa thành public DTO.
4. Chạy SDK tests và backend pytest trước khi đánh dấu done.
