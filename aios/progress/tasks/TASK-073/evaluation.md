# TASK-073 — Evaluation

## Đối chiếu AC — 8/8 ĐẠT (xem test.md)

## Giá trị — đỉnh cao M10
- `aiagent conformance` trả `AIOS 1.0 READY` — 13 categories được phủ bằng 9 areas + 20 GS + 5 gates.
- GS-001..020 là "release phải pass" — mọi bản release sau này chạy conformance trước khi phát hành.

## Bài học
1. Hệ thống kiểm chứng toàn cục phải được phép đọc mọi layer — rule scanner cần ngoại lệ có chú thích (INV-017 mở rộng "chỉ gọi API, không sửa").
2. Golden scenarios deterministic + nhanh (<5s) — chạy được trong CI mỗi commit.

## Đề xuất (P3)
- Golden Demo (PLAN §M10-40) end-to-end qua Dashboard Execution Timeline — nâng cấp GS-003 thành workflow thật nhiều bước.
