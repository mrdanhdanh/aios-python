# Pull Request — AIOS

> Đọc `docs/workflows/issue-pr-workflow.md` + `AGENTS.md` trước khi tạo PR. Mọi thay đổi phải qua PR (merge thủ công), không commit thẳng `master`.

## Issue liên quan

<!-- BẮT BUỘC:
  - PR có issue: `Fixes #N` hoặc `Refs #N` (KHÔNG dùng `Closes #N` cho PR feature → verify — GitHub sẽ tự đóng issue trước khi promotion lên master; đóng issue thủ công sau khi promotion).
  - PR bypass (fix nhỏ không có issue): giữ dòng [bypass] bên dưới kèm lý do — title khuyến nghị dạng `type/bypass-<slug>`.
-->
Refs #___

- [ ] `[bypass]` — lý do (chỉ khi fix nhỏ không có issue): ...

## Mô tả thay đổi

<!-- Thay đổi gì, tại sao, ảnh hưởng tới thành phần nào -->

## Test đã chạy

- [ ] pytest (backend) — kết quả: ...
- [ ] vitest (dashboard / extension) — kết quả: ...
- [ ] CLI / thủ công — lệnh đã chạy: ...
- [ ] Không cần test (chỉ tài liệu/quy trình) — lý do: ...

## Checklist

- [ ] Đã đọc `AGENTS.md` (quy trình bắt buộc: hard gate, LOG.md, PROGRESS.md, commit)
- [ ] Nhánh tạo TỪ `verify` (KHÔNG từ `master`); tên theo quy ước `<type>/ISSUE-N-slug` hoặc `<type>/bypass-slug`
- [ ] PR này nhắm base = `verify` (KHÔNG nhắm `master`, trừ PR promotion `release: verify → master`)
- [ ] Đã cập nhật `aios/progress/LOG.md` + `PROGRESS.md` (nếu thay đổi code/quy trình)
- [ ] Đủ hard gate 8-file (nếu là TASK-xxx)
- [ ] Working tree sạch trước khi request review

---
*PR này được kiểm tra tự động: title/body/base branch (`.github/workflows/pr-validation.yml`) — không có bot tự merge; việc duyệt & merge do con người thực hiện.*
