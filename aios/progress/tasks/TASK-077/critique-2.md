# Critique vòng 2 — TASK-077 (bởi Critic, sau khi resolve vòng 1)

> Trạng thái: **RESOLVED** — 2 P1 + 4 P2 + 6 P3, tất cả đã resolve vào spec v3 (xem bảng dưới).

## Các vấn đề và resolution

| # | Mức | Vấn đề | Resolution |
|---|-----|--------|------------|
| C2-01 | P1 | Frontmatter issue form dùng `description` thay vì `about` — sai chuẩn GitHub (key đúng: `name`/`about`/`title`/`labels`/`assignees`/`body`); test assert theo `description` → false-positive PASS | RESOLVED — AC1 + AC9 đổi `description` → `about` (bắt buộc, ≤190); assert đúng chuẩn: `name` (≤80), `about` (≤190), `title` (string, optional), `labels` (string HOẶC list), `body` (list, bắt buộc) |
| C2-02 | P1 | Dogfooding vỡ: `[bypass]` trong body chỉ cứu body-check, KHÔNG cứu title-check — PR TASK-077 (title `docs/issue-pr-workflow: ...`) vẫn fail | RESOLVED — chọn phương án (b): body có `[bypass]` → bỏ qua title check (bypass = title bypass-style HOẶC body `[bypass]`); ghi vào luồng quyết định AC3 + AC10 + tasks.md |
| C2-03 | P2 | `github.rest.issues.get` cần `issues: read`; `permissions: contents: read` không đủ → 403; thiếu xử lý 404 | RESOLVED — thêm `issues: read` vào permissions; try/catch MỌI lỗi (403/404/rate-limit); 404 → chỉ warning, không fail (traceability ≠ gate) |
| C2-04 | P2 | `hotfix` có trong regex nhưng không có trong quy ước GĐ2 — docs lệch check | RESOLVED — GĐ2 thêm: fix khẩn cấp không issue → `hotfix/bypass-slug` (biến thể ưu tiên của bypass) |
| C2-05 | P2 | PR đầu tiên của TASK-077 KHÔNG chạy workflow (workflow chưa tồn tại trên default branch) — AC10 không kiểm chứng được | RESOLVED — AC10 + docs GĐ3 ghi chú rõ; thay bằng AC9-3 (script mô phỏng ≥12 case); xác nhận action chạy thật bằng PR thử nghiệm nhỏ sau khi merge workflow vào verify/master (tasks.md) |
| C2-06 | P2 | AC3b/c thiếu thứ tự ưu tiên logic — implement dễ sai | RESOLVED — AC3 mô tả luồng quyết định tuyến tính 7 bước (draft → release → base → bypass → ISSUE title → bypass title → fail); AC9 yêu cầu ≥2 test case/nhánh |
| C2-07 | P3 | Regex đóng cứng 6 prefix; ADR-0005 có "..." mở rộng — bảo trì lệch | RESOLVED — ADR-0006 Consequences ghi: danh sách prefix nằm ở 2 nơi (docs GĐ2 + regex action), thêm prefix mới phải cập nhật đồng bộ |
| C2-08 | P3 | `Closes #N` tự đóng issue khi merge feature→verify — đóng sớm trước promotion | RESOLVED — docs GĐ3/GĐ5 khuyến nghị `Fixes #N`/`Refs #N` cho PR feature→verify; đóng issue thủ công sau promotion |
| C2-09 | P3 | Thiếu `gh auth setup-git` + lưu ý ký tự `→` trên Windows | RESOLVED — docs thêm `gh auth setup-git`; nhắc copy đúng `→` (regex khớp `\u2192`, gõ `->` sẽ fail) |
| C2-10 | P3 | Thiếu `concurrency` — push nhanh → nhiều run song song, nhiễu status | RESOLVED — workflow thêm `concurrency: { group: pr-${{ github.event.pull_request.number }}, cancel-in-progress: true }` |
| C2-11 | P3 | Body check `#\d+` trùng số PR/issue — false-positive | RESOLVED — docs khuyến nghị `Fixes #N`/`Refs #N` (KHÔNG `Closes` cho PR feature→verify — tránh đóng issue sớm, xem C2-08); ghi chú check chỉ xác nhận "có link", không xác minh đúng issue |
| C2-12 | P3 | AC1 ép `labels` là list — GitHub chấp nhận string đơn | RESOLVED — nới assertion: `labels` string hoặc list |

## Kết luận

- [x] Cần sửa trước khi implement — 2 P1 + 4 P2 + 6 P3 đều đã resolve vào spec (spec v3)
- [ ] Chấp nhận spec (không còn P1/P2) — chờ tasks.md + review.md
