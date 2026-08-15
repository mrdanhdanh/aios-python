# TASK-063 — Test

> Task tài liệu (docs-only): không có test code mới; test = kiểm tra cấu trúc markdown tự động + đối chiếu dữ liệu.

## 1. Kiểm tra cấu trúc markdown (AC2) — chạy thật

Script: `check-markdown.js` (Node, không dependency) chạy trên `docs/architecture-v2.md`.

Kết quả **2026-08-15**:

```
[OK]   Không còn khối ```mermaid
[OK]   Code fence cân bằng (14 fence, chẵn)
[OK]   Chỉ 1 heading H1 (có 1)
[OK]   Mục "## 0..14" — đủ 15 mục chính
[OK]   Bảng hợp lệ (12 separator rows)
[OK]   Đủ INV-001..034
[OK]   Đủ milestone M0..M10 trong bảng
KẾT QUẢ: TẤT CẢ CHECK PASS ✅  (21/21)
```

Lệnh chạy lại:
```
node check-markdown.js "docs/architecture-v2.md"
```

## 2. Đối chiếu dữ liệu với PROGRESS.md (AC1, AC4, AC5)

| Kiểm tra | Kết quả |
|----------|---------|
| M0–M9 `done`, M10 `todo` | ✅ khớp PROGRESS.md 2026-08-15 |
| Số liệu tests M1..M9 (428/669/689+12+19/809/1086/1521/1560/1639/1780) | ✅ khớp bảng milestone + tasks |
| Coverage (95.76/95.51/94.92/95.22/95.35/95.05/94.46) | ✅ khớp |
| INV-001..034: M2=001-010, M5=011-016, M6=017-021, M7=022-029, M9=030-034 | ✅ khớp nhãn canonical (PROGRESS.md §M7 note) |
| Task id M1–M9 (TASK-002..062) + số tests từng task | ✅ khớp PROGRESS.md |

## 3. Kiểm tra tham chiếu file cũ (AC6)

- `docs/architecture.md` KHÔNG bị sửa (git status chỉ thấy file mới + aios/progress/).

## Kết luận

**PASS 21/21** — đủ điều kiện đánh giá.
