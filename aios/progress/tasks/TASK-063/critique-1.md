# TASK-063 — Critique vòng 1

> Critic (tự — reviewer độc lập quan điểm, không có subagent phản hồi). Phản biện spec trước khi viết tài liệu.

## Các vấn đề tìm được

### C1-01 (P2) — Số liệu tests có thể lệch giữa các nguồn
PROGRESS.md có nhiều con số (M8 "1639", M9 "1780 @M9 / full 1793", dashboard 12 + extension 19). Nếu ghi sai con số trong file kiến trúc → mất giá trị tham chiếu.
→ **Resolve**: Chỉ dùng PROGRESS.md làm nguồn duy nhất, ghi rõ "theo PROGRESS.md 2026-08-15". Với M9 ghi cả 1780 (baseline M9) và 1793 (full suite sau review) kèm chú thích.

### C1-02 (P2) — Mermaid: emoji và ký tự đặc biệt trong subgraph title là rủi ro render
File cũ dùng `subgraph T45["Tầng 4.5 — Core Intelligence (M5) 🚧"]` — emoji + dấu gạch ngang dài trong title. Đây là ứng viên gây lỗi render trên một số bản mermaid/VS Code preview.
→ **Resolve**: File mới: subgraph title CHỈ chữ + ngoặc kép, không emoji, không `→`/`—`; trạng thái ✅/🔲 chỉ đặt trong NODE label (đã bọc ngoặc kép). Edge label dùng `-->|"text"|` thuần.

### C1-03 (P2) — Tham chiếu chéo file cũ
Nếu người đọc vẫn mở file cũ, cần chỉ dẫn rõ file nào là hiện hành.
→ **Resolve**: Đầu file mới ghi banner "tài liệu hiện hành — thay thế docs/architecture.md"; thêm dòng pointer ở cuối. Không sửa file cũ (AC6).

### C1-04 (P3) — M10 chưa làm: tránh vẽ như thể đã có
Không nên mô tả chi tiết M10 (AIOS 1.0) như module thật.
→ **Resolve**: M10 chỉ xuất hiện trong bảng milestone với trạng thái `todo`, ghi chú "freeze INV-001..034, release blocker", không có sơ đồ module.

### C1-05 (P3) — Sơ đồ tổng quá to sẽ khó đọc
File cũ sơ đồ tổng ~60 node — khó đọc, dễ lỗi cú pháp.
→ **Resolve**: Chia thành nhiều sơ đồ nhỏ (7–20 node mỗi sơ đồ): tổng quan / planes / orchestrator / request flow / milestone. Mỗi sơ đồ có tiêu đề.

### C1-06 (P3) — Đánh dấu trạng thái trong sơ đồ
Mọi node phải có trạng thái rõ ràng (done/todo) để không tái diễn tình trạng "file nói 🔲 nhưng thực tế ✅".
→ **Resolve**: Node label luôn kèm `✅` hoặc `🔲`; chú giải ngay dưới sơ đồ tổng.

## Kết luận vòng 1
Spec cơ bản đủ; các vấn đề trên được resolve bằng quy ước viết (C1-01..C1-06) — chuyển sang critique vòng 2.
