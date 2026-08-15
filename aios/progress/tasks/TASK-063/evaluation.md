# TASK-063 — Evaluation

## Đối chiếu tiêu chí chấp nhận (spec.md)

| AC | Tiêu chí | Kết quả |
|----|----------|---------|
| AC1 | Trạng thái M0–M9 done, M10 todo; số liệu khớp PROGRESS.md | ✅ PASS — test.md §2 |
| AC2 | Không còn khối mermaid; cấu trúc markdown hợp lệ | ✅ PASS — script node 21/21 |
| AC3 | Đủ 7 tầng lõi + 4 lớp M6–M9 | ✅ PASS — §1 + §7–§10 |
| AC4 | Bảng INV-001..034 đúng nhãn canonical | ✅ PASS — §12 (M2:001-010, M5:011-016, M6:017-021, M7:022-029, M9:030-034) |
| AC5 | Bảng milestone M0–M10 + bảng tasks M1–M9 đúng | ✅ PASS — §11 + §11.1 |
| AC6 | File cũ `docs/architecture.md` không bị sửa | ✅ PASS — chỉ tạo file mới |
| AC7 | DoD: LOG.md + PROGRESS.md + commit | ✅ PASS |

## Kết quả

**ĐẠT 7/7 AC — TASK-063 DONE.**

## Bài học

1. **Người dùng ưu tiên khả năng đọc > sơ đồ đẹp**: yêu cầu "đọc không bị lỗi" + "markdown bình thường" → markdown thuần + ASCII diagrams là lựa chọn an toàn nhất, không phụ thuộc renderer (VS Code preview, GitHub, trình xem bất kỳ).
2. **Source of truth quan trọng**: file cũ lệch 4–5 milestone với code thật — cần quy trình cập nhật tài liệu kiến trúc theo từng milestone (gợi ý: thêm bước "cập nhật architecture doc" vào DoD các milestone tới).
3. **ASCII diagrams vẫn trực quan** mà không cần renderer — đủ cho tài liệu kiến trúc nội bộ.

## Đề xuất (P3 — ghi nhận, không làm ngay)

- Cân nhắc thêm bước "cập nhật docs/architecture-v2.md" vào DoD mỗi milestone (M10 khi hoàn tất).
- Khi M10 (AIOS 1.0) xong: cập nhật §11 trạng thái M10 → done.
