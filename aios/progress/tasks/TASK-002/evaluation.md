# Evaluation — TASK-002

## Kết quả đối chiếu tiêu chí chấp nhận
**16/16 AC PASS** — chi tiết tại `test.md`.

| Hạng mục | Kết quả |
|----------|---------|
| 32 tests pass (backend/ + root) | ✅ |
| Coverage 96.14% (ngưỡng 80%) | ✅ |
| `pip install -e ".[dev]"` | ✅ aios-core 0.1.0 |
| Quy trình hard gate | spec → critique ×2 (3 P1 + 6 P2 + 5 P3 vòng 1; 1 P1 + 6 P2 + 3 P3 vòng 2) → review (1 R1 + 3 R2 + 4 R3) → implement → test → evaluate — **tất cả resolved trước khi code** |

## Đánh giá hệ thống tổng thể
- **Critique ×2 hoạt động xuất sắc ở task code thật đầu tiên**: bắt được claim kỹ thuật SAI (`extra="forbid"` không bắt typo env trong pydantic-settings v2 — có nguy cơ AC4 fail im lặng), bẫy import-time (`default=now()`), mâu thuẫn `.gitignore` vs AC9, thiếu venv step (AC1 không verify được), xung đột `backend/core` vs src layout.
- **Reviewer bắt thêm 1 R1 blocking** (thiếu bước venv) mà critique bỏ sót — chứng minh hard gate 8 bước có giá trị cộng dồn, không trùng lặp.
- Implement phát hiện 2 lỗi thật (readme path ngoài project dir; pydantic default factory) — đều là lỗi quen thuộc, test bắt ngay.
- Quy ước layout M1 đã được chốt và note vào PLAN.md — tránh refactor khi TASK-003 thêm DI container.

## Bài học (bổ sung STATS.md)
1. **Claim kỹ thuật phải được kiểm chứng bằng spike test** — "extra forbid bắt typo env" nghe hợp lý nhưng sai cơ chế; spec nên có test spike từ đầu.
2. **pydantic v2: default callable phải dùng `Field(default_factory=...)`**; `created=None` truyền vào model sẽ override default → helper phải filter None.
3. **hatchling không cho readme ngoài project dir** — file README package phải đặt trong backend/.
4. **Chạy pytest từ root tạo `.coverage` ở root** — thêm vào .gitignore.
5. **Bảng AC ↔ checklist trong review** (mỗi AC có mục checklist tương ứng) giúp phát hiện bước thiếu trước khi code.

## Đề xuất cải tiến
- M1-P0.5 (TASK-003): thêm hook pre-commit đơn giản (chạy pytest khi commit vào backend/) hoặc ghi chú vào tasks.json.
- Xem xét `ruff` lint từ TASK-003 (type checking không bắt buộc ở P0, nhưng thêm sớm rẻ hơn).

## Kết luận
- [x] **ĐẠT spec (16/16 AC)** — M1/P0 hoàn thành, sẵn sàng TASK-003 (P0.5: Runtime Kernel + DI container + contracts).
