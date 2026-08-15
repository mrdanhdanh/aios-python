# TASK-063 — Evaluation (M10-F1)

## Đối chiếu AC (v2 — M10-F1)

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | 5 file docs/architecture/* + constitution-1.0.md | ✅ |
| AC2 | layer-model 7 tầng đúng thứ tự | ✅ |
| AC3 | constitution INV-001..034 đủ 34 + 15 core principle | ✅ |
| AC4 | Mọi INV có enforcement test | ✅ (phát hiện + bổ sung 2 test thiếu) |
| AC5 | Freeze tuyên bố + renumber deferred | ✅ |
| AC6 | Không mermaid | ✅ |
| AC7 | architecture-v2.md cập nhật | ✅ |
| AC8 | DoD | ✅ |

**ĐẠT 8/8 AC (v2) — TASK-063 DONE (gộp v1 7/7 + v2 8/8).**

## Giá trị
- **Constitution 1.0** = văn bản chuẩn cho mọi thay đổi sau freeze; mapping 15 core principle → canonical INV giúp tra cứu nhanh.
- **Bộ 6 tài liệu docs/architecture/** tách vai trò rõ (tổng thể / layer / control / execution / autonomy / constitution) — không trùng lặp architecture-v2.md.

## Bài học
1. **"Invariant trên giấy" có thật**: 2/34 INV (008 Artifact First, 012 Context Budget) chưa có enforce test trực tiếp — AC4 đối chiếu tự động đã phát hiện. Bài học: mọi milestone cần bước "đối chiếu INV với test" trước khi tuyên bố done (đã đưa vào M10 gate A).
2. Tài liệu 1.0 nên viết trước khi làm task cụ thể (TASK-073 conformance sẽ dùng constitution làm chuẩn).
3. (Từ v1) Ưu tiên khả năng đọc > sơ đồ đẹp; ASCII diagrams đủ trực quan.
