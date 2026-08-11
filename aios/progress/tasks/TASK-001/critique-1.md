# Critique vòng 1 — TASK-001

## Đánh giá chung
Spec rõ ràng, phạm vi tốt, AC kiểm chứng được. Sẵn sàng: 4/5. Có 1 vấn đề P1 cần sửa trước khi implement tiếp.

## Các vấn đề tìm được

### P1 — `.gitignore` chặn cả `.vscode/` (Nghiêm trọng)
- Vị trí: Yêu cầu chi tiết + rủi ro (không đề cập), file `.gitignore` đã commit
- Vấn đề: `.gitignore` hiện ignore toàn bộ `.vscode/`. Từ M1 sẽ cần track workspace settings chung cho backend/dashboard/extension (launch.json, tasks.json, mcp.json — dự án plan có mcp cho AIOS SDK). Ignore toàn bộ sẽ khiến các file cấu hình phát triển KHÔNG được commit, vi phạm chính nguyên tắc "cấu trúc nằm trong repo" của dự án.
- Đề xuất: Sửa `.gitignore`: bỏ dòng `.vscode/`, thay bằng chỉ ignore file cá nhân `.vscode/settings.json` (personal settings thường có đường dẫn máy), giữ track các file workspace còn lại.

### P2 — Chưa nêu quy tắc "khi nào tạo TASK mới" (Trung bình)
- Vị trí: spec.md — Yêu cầu chi tiết (thiếu), agent orchestrator body cũng chưa nói
- Vấn đề: Quy trình có hard gate cho TASK, có bypass cho fix nhỏ, nhưng KHÔNG có tiêu chí phân loại "việc này là TASK mới hay fix nhỏ". Agent sẽ tự quyết định tùy hứng → không nhất quán, khó đánh giá.
- Đề xuất: Bổ sung rule định lượng vào agent orchestrator: yêu cầu mới > ~30 phút làm hoặc chạm nhiều file/module → tạo TASK-xxx mới; ngược lại → bypass ghi log.

### P3 — Template `tasks.md` chưa có cột "đã verify" (Nhẹ)
- Vị trí: Phạm vi In mục 3 (template 8 file)
- Vấn đề: Checklist checkbox thuần không phân biệt "đã làm" và "đã kiểm chứng chạy được".
- Đề xuất: Trong template tasks.md ghi chú: checkbox [x] = đã làm VÀ đã verify (test chạy được), không chỉ viết xong.

## Kết luận
- [ ] Chấp nhận spec (không còn P1/P2)
- [x] **Cần sửa trước khi implement tiếp**: P1 (gitignore) + P2 (rule tạo task mới)

## Resolution (bởi AIOS Orchestrator)
- **P1 — ĐÃ SỬA**: `.gitignore` bỏ ignore toàn bộ `.vscode/`, chỉ giữ `.vscode/settings.json` trong danh sách ignore (file cá nhân). Workspace settings sẽ được track từ M1.
- **P2 — ĐÃ SỬA**: Bổ sung rule vào `aios-orchestrator.agent.md` (mục Decision Pipeline): "Yêu cầu mới > ~30 phút hoặc chạm nhiều file/module → tạo TASK-xxx mới; nhỏ hơn → bypass ghi LOG.md". AC6 bổ sung kiểm tra rule này tồn tại trong file agent.
- **P3 — CHẤP NHẬN**: ghi chú đã thêm vào template tasks.md (checklist: [x] = làm xong VÀ verify được).
