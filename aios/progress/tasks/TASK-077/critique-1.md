# Critique vòng 1 — TASK-077 (bởi Critic)

> Trạng thái: **RESOLVED** — 4 P1 + 7 P2 + 6 P3, tất cả đã resolve vào spec (xem bảng dưới).

## Các vấn đề và resolution

| # | Mức | Vấn đề | Resolution |
|---|-----|--------|------------|
| C1-01 | P1 | Ngoại lệ `[bypass]` không bao giờ đạt được: AC3a bắt title phải có `ISSUE-N` → fix nhỏ không issue luôn fail title check | RESOLVED — thêm nhánh bypass vào title regex: `^(fix\|docs\|refactor\|test\|operation)/(bypass\|hotfix)-[a-z0-9-]+` khi body có `[bypass]`; docs GĐ3 định nghĩa title bypass mẫu |
| C1-02 | P1 | PR promotion `release: verify → master` bị body-check chặn (body không chứa `#N`/`[bypass]`) | RESOLVED — action skip body-check khi title khớp `^release:`; PR template promotion bắt buộc mục "Issues included: #N, #M..." |
| C1-03 | P1 | Action không check base branch → PR nhầm base `master` vẫn PASS, vi phạm ADR-0005 nguy hiểm nhất | RESOLVED — action check `base.ref`: feature PR → base phải `verify`; title `^release:` → base phải `master`; fail case ngược lại; thêm test case |
| C1-04 | P1 | Thiếu cơ chế tạo PR (tooling) — agent không có công cụ tuân thủ quy trình bắt buộc | RESOLVED — chuẩn tooling: GitHub CLI `gh` (`gh auth login` bắt buộc, liệt kê lệnh `gh issue create` / `gh pr create --draft --base verify`); PR promotion: agent chuẩn bị nội dung + lệnh, người dùng bấm create/merge |
| C1-05 | P2 | Draft PR chưa xử lý — action vẫn chạy trên draft, fail check nhiễu | RESOLVED — github-script skip khi `draft === true`; thêm `ready_for_review` vào `types` |
| C1-06 | P2 | `config.yml` không hỗ trợ "label defaults" (sai sự thật) | RESOLVED — config.yml chỉ dùng `blank_issues_enabled: false` + `contact_links`; label gợi ý đặt trong frontmatter từng template |
| C1-07 | P2 | AC3c khẳng định quá mức "PR bị block" (chưa có required status checks) | RESOLVED — sửa wording: "check failed (PR ✗); merge chỉ bị chặn khi người dùng bật required status checks — docs hướng dẫn bước này" |
| C1-08 | P2 | Drift verify cục bộ — thiếu bước refresh trước khi tạo nhánh | RESOLVED — GĐ2 thêm bước chuẩn: `git fetch origin` → `git checkout verify` → `git pull origin verify` → tạo nhánh từ `origin/verify` |
| C1-09 | P2 | "Merge thủ công bằng lệnh git" mơ hồ — có thể đọc thành merge thẳng master | RESOLVED — ghi rõ: merge local CHỈ hợp lệ cho feature → verify; `master` CHỈ cập nhật qua merge button PR promotion |
| C1-10 | P2 | Không có quy trình PR reject / conflict | RESOLVED — reject: sửa trên CÙNG nhánh → push → re-request review (không tạo PR mới); conflict: `git rebase origin/verify` (feature) / merge (verify); thêm vào docs |
| C1-11 | P2 | YAML parse ≠ GitHub chấp nhận template (thiếu schema assertions) | RESOLVED — AC9 thêm schema assertions: frontmatter `name` (≤80), `description` (≤190), `labels` list, `body` list, `type ∈ {markdown, input, textarea, dropdown, checkboxes}`, `validations.required` boolean; workflow có `name/on/jobs` + `types` đúng |
| C1-12 | P3 | Escape regex trong YAML double-quoted là lỗi parse ngầm (`\d` invalid escape) | RESOLVED — dùng single-quoted YAML cho pattern; ghi chú quy tắc vào docs |
| C1-13 | P3 | Workflow thừa `actions/checkout` + thiếu `permissions` | RESOLVED — chỉ `actions/github-script@v7` + `permissions: contents: read` (không cần checkout, an toàn PR từ fork) |
| C1-14 | P3 | `ISSUE-\d+` khớp cả số PR (dãy số chung) | RESOLVED — action optional `github.rest.issues.get` xác minh issue tồn tại; docs khuyến khích `Fixes #N`/`Closes #N`; `[bypass]` match case-insensitive |
| C1-15 | P3 | Promotion all-or-nothing (gộp mọi thay đổi trên verify) | RESOLVED — ghi ADR-0006 consequences: promote thường xuyên, nhỏ, nhanh; title promotion có ngày tránh trùng |
| C1-16 | P3 | Thiếu bước xóa nhánh cụ thể | RESOLVED — docs thêm `git push origin --delete <branch>` + `git branch -d <branch>` |
| C1-17 | P3 | Dogfooding: PR của TASK-077 (không có ISSUE-N) sẽ fail check của chính nó | RESOLVED — PR TASK-077 body sẽ có dòng `[bypass]` (fix nhỏ/process không issue) + ghi LOG.md; ghi vào tasks.md để không quên |

## Kết luận

- [x] Cần sửa trước khi implement — 4 P1 + 7 P2 + 6 P3 đều đã resolve vào spec (spec v2)
- [ ] Chấp nhận spec (không còn P1/P2) — chờ critique vòng 2 xác nhận
