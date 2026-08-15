# TASK-063 — Implementation

Task tài liệu (docs-only) — artifact chính là file tài liệu, không có code hệ thống:

| Artifact | Vị trí |
|----------|--------|
| Tài liệu kiến trúc mới (bản hiện hành) | `docs/architecture-v2.md` |
| File cũ (giữ làm lịch sử, không sửa) | `docs/architecture.md` |
| Script kiểm tra cấu trúc markdown | `%TEMP%/aios-mermaid-check/check-markdown.js` (dùng để test, không commit) |

Nội dung file mới: 14 mục — §0 cách đọc · §1 tổng quan 7 tầng + 4 lớp M6–M9 + bảng package · §2 ba mặt phẳng (Autonomy/Control/Worker/Execution) · §3 Orchestrator modules · §4 luồng request 12 bước + hành trình 1 lệnh + bảng module · §5 Runtime Kernel 9 services · §6 Core Intelligence M5 · §7 Harness M6 · §8 Enterprise M7 · §9 Ecosystem M8 · §10 Autonomous M9 · §11 milestones M0–M10 + bảng tasks · §12 INV-001..034 · §13 nguyên tắc · §14 nguồn & lịch sử.

Định dạng: markdown thuần (bảng + danh sách + sơ đồ ASCII trong code block), không dùng Mermaid — theo yêu cầu người dùng (amend spec 2026-08-15).
