# Evaluation — TASK-003

## Kết quả đối chiếu tiêu chí chấp nhận
**20/20 AC PASS** — chi tiết tại `test.md`.

| Hạng mục | Kết quả |
|----------|---------|
| 107 tests pass (backend/ + root) | ✅ |
| Coverage 94.82% (ngưỡng 80%) | ✅ |
| Quy trình hard gate | spec → critique ×2 (v1: 2 P1 + 8 P2 + 8 P3; v2: 2 P1 + 8 P2 + 10 P3 — **tất cả resolve trước khi code**) → review (1 R1 + 2 R2 + 4 R3) → implement → test → evaluate |

## Đánh giá hệ thống tổng thể
- **Critique vòng 2 bắt 2 mâu thuẫn nội bộ do resolution vòng 1 tạo ra** (AC2 case 6 mâu thuẫn rule list; check_upgrade vs is_compatible đảo tham số) — chứng minh cần đủ 2 vòng phản biện, không thể rút gọn.
- **Reviewer verify tay toàn bộ 5-rule compatibility** với 8 case + invariant trước khi code — bắt được thiếu bước cập nhật `aios_core/__init__.py` (R1 blocking) mà nếu bỏ sót thì AC14 fail ở cuối.
- Implement phát hiện **5 lỗi thật** trong đó 3 là lỗi quen thuộc của pydantic v2 (validator shadowing, abstractmethods cleared, object.__init__) — đều có test bắt và fix ngay.
- Nền móng TASK-004 đã đủ: Container has/clear cho test isolation, Subscription export, Event.to_dict cho WebSocket, ExecutionPlan cho Execution Service.

## Bài học (bổ sung STATS.md)
1. **pydantic v2: validator method trùng tên trong subclass sẽ REPLACE validator kế thừa** (key theo tên method) — đổi tên hoặc khai báo lại.
2. **pydantic v2 clears `__abstractmethods__`** khi complete model — ABC không enforce trên BaseModel; dùng `validate()` runtime làm enforcement point.
3. **Class không định nghĩa `__init__` (kế thừa object) có `*args/**kwargs`** — container phải skip, không ném lỗi varargs.
4. **Shallow copy dict trong test**: `dict(VALID_DATA)` share nested list → mutation test đầu hỏng test sau; luôn deepcopy.
5. **2 vòng critique có giá trị cộng dồn**: vòng 2 bắt mâu thuẫn do chính resolution vòng 1 tạo ra — không thể gộp thành 1 vòng.
6. **Model validator raise ValueError → pydantic wrap thành ValidationError** với message "Value error, ..." — match regex theo nội dung thật.

## Đề xuất cải tiến
- TASK-004 (9 services): tận dụng has/clear cho test isolation; dùng `asyncio.run` cho service sync tests; cân nhắc `ruff` lint từ task này.

## Kết luận
- [x] **ĐẠT spec (20/20 AC)** — TASK-003 done, sẵn sàng TASK-004 (9 Runtime Services + RuntimeKernel).
