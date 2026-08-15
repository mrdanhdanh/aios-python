# TASK-063 — Critique vòng 2

> Critic vòng 2 (độc lập, sau khi resolve vòng 1). Kiểm tra spec + quy ước đã bổ sung.

## Các vấn đề tìm được

### C2-01 (P2) — Kiểm tra render phải là "test thật", không chỉ nhìn
AC2 nói "parser hoặc render thật chạy được" nhưng chưa nói làm thế nào.
→ **Resolve**: Chạy thật `mermaid.parse()` bằng Node (jsdom) trên TỪNG block mermaid trích từ file; ghi kết quả vào `test.md`. Nếu môi trường không cài được (offline), ghi rõ lý do + fallback: render thủ công VS Code preview + đối chiếu cú pháp theo checklist. (Quyết định: thử parser trước, fallback thủ công.)

### C2-02 (P2) — Bảng INV phải khớp nhãn canonical của test
PROGRESS.md ghi rõ nhãn test: M6 = `test_inv017..inv021`, M7 = `test_inv022..inv029`, M9 = `test_inv030..inv034`. Bảng INV trong file mới phải dùng đúng các nhãn này, kèm tên gọi tiếng Việt.
→ **Resolve**: Bảng INV có cột "ID" (INV-xxx), "Tên (canonical test label)", "Nội dung", "Milestone", "Enforce".

### C2-03 (P3) — File mới cần mục "Cách đọc tài liệu này"
Người đọc mới cần biết thứ tự đọc và nguồn dữ liệu.
→ **Resolve**: Thêm mục §0 "Cách đọc" ngay sau banner: nguồn (PLAN.md + PROGRESS.md), quy ước ký hiệu, thứ tự đọc đề xuất.

### C2-04 (P3) — Giữ liên kết ADR
File cũ tham chiếu `docs/adr/0004-architecture-invariants.md` — file mới phải giữ liên kết này để không mất thông tin.
→ **Resolve**: Mục INV ghi rõ liên kết ADR-0004 + test_architecture.py + arch_health.py (scanner runtime).

## Kết luận vòng 2
Các vấn đề đã resolve — **spec v2 đạt, được phép implement** (viết file + test render).
