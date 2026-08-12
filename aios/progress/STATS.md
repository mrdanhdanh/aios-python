# STATS.md — Tổng hợp tiến độ

> Cập nhật định kỳ (mỗi milestone hoặc theo yêu cầu). Dữ liệu cho đánh giá hệ thống.

## M0 — Development Foundation

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 1 (TASK-001) |
| Task done | 1 |
| Số critique đã resolve | 2 / 2 |
| Bypass đã dùng | 0 |
| Commit | 5 |

## M1 — Core Runtime ✅

| Chỉ số | Giá trị |
|--------|---------|
| Task tổng | 9 (TASK-002 → 009) — **TẤT CẢ done** |
| Task done | 9/9 |
| Tests (cuối M1) | **346 pass — coverage 95.30%** |
| Critique resolve | 9 task × 2 vòng (trung bình 20+ vấn đề/task) |
| Review | 9 task (0-1 R1 mỗi task) |
| Bypass | 0 |
| Deliverable M1 | `aiagent run workflow.yaml --simulate` ✓ |
| Commit | ~30 commits |
| Critique resolve (TASK-004) | v1: 11 (2 P1 + 6 P2 + 3 P3); v2: 15 (1 P1 + 6 P2 + 8 P3) |
| Review (TASK-004) | 0 R1 + 5 R2 + 6 R3 — resolved trước implement |
| Bypass đã dùng | 0 |
| Commit | TASK-004: 1 (eb64795) |

## Ghi chú

- Thống kê mở rộng theo milestone; cập nhật sau mỗi task.

## Bài học (lessons learned)

> Nguồn: `evaluation.md` của từng task.

1. **Critique ×2 tìm ra vấn đề thật, kể cả task "nhỏ"**: gitignore chặn cả `.vscode/` sẽ gây khó từ M1; rule phân loại TASK vs fix nhỏ thiếu → agent tự quyết tùy hứng. Không nên bỏ qua phản biện.
2. **Cần rule định lượng để agent phân loại công việc**: "> 30 phút hoặc chạm nhiều file → TASK mới; ngược lại → bypass ghi log" — giúp nhất quán, dễ đánh giá.
3. **Tách rõ verify "tự động" vs "thủ công" ngay trong test.md**: AC về agent picker cần người dùng xác nhận — ghi rõ để không bị bỏ sót.
4. **TASK tự dogfood quy trình** (chính task này đi qua đủ 8 bước) — hiệu quả, phát hiện lỗi quy trình ngay khi tạo quy trình.
5. **Commit thường xuyên theo bước** (4 commit cho M0) — mỗi bước hoàn chỉnh là một mốc khôi phục được.
6. **Claim kỹ thuật phải kiểm chứng bằng spike test** — `extra="forbid"` bắt typo env là claim SAI cơ chế (pydantic-settings v2), critique-2 bắt được.
7. **pydantic v2**: default callable phải dùng `Field(default_factory=...)`; truyền `None` override default — helper phải filter.
8. **hatchling không cho readme ngoài project dir** — README package đặt trong `backend/`.
9. **Bảng AC ↔ checklist trong review** giúp phát hiện bước thiếu (VD thiếu venv step) trước khi code.
10. **pydantic v2: validator method trùng tên trong subclass REPLACE validator kế thừa** (key theo tên method) — đổi tên hoặc khai báo lại.
11. **pydantic v2 clears `__abstractmethods__`** khi complete model — ABC không enforce trên BaseModel; dùng `validate()` runtime làm enforcement point.
12. **Class không định nghĩa `__init__` (kế thừa object) có `*args/**kwargs`** — container phải skip, không ném lỗi varargs.
13. **Shallow copy dict trong test**: `dict(VALID_DATA)` share nested list → mutation test đầu hỏng test sau; luôn deepcopy.
14. **2 vòng critique có giá trị cộng dồn**: vòng 2 bắt mâu thuẫn do chính resolution vòng 1 tạo ra — không gộp được.
15. **Model validator raise ValueError → pydantic wrap thành ValidationError** ("Value error, ...") — match regex theo nội dung thật.
16. **Path guard phải dùng `is_relative_to` sau resolve** — `startswith` prefix string bị bypass bằng thư mục sibling (`artifacts2`).
17. **Persistence phải có cơ chế tường minh từ spec** — `list()` cần sidecar, không thể tự bịa lúc code.
18. **Một khái niệm một định nghĩa** — "pending" xuất hiện 3 chỗ với 2 nghĩa; spec phải nhất quán.
19. **Timebase không trộn**: metadata `created: datetime` + TTL `_created_mono` (monotonic) tách bạch.
20. **EventBus.publish nhận Event object** — wrapper service phải tạo Event trước.
21. **Tên biến unpack phải khớp ngữ nghĩa index** — in-index lưu (rel, source_kind, source_id): dùng `_sk, source_id`, không dùng tk/ti chung.
22. **Fixture tên ngắn dễ conflict** — g/cat thiếu tham số → FixtureFunctionDefinition; tên rõ + tham số tường minh.
23. **Thread-safe test: id phải unique theo thread** — agent-{i} × 2 thread = 50 unique không phải 100.
24. **Regex lookaround + scan escape-first** — validate template lúc construct (object hỏng không tồn tại).
