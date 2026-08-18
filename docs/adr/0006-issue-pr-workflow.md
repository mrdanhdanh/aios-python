# ADR-0006: Issue-Driven Development — Issue → Branch → PR → verify → master

- **Status**: accepted
- **Date**: 2026-08-16
- **Extends**: [ADR-0005](0005-branching-model.md) (branching model `master` ← `verify` ← feature branch)

## Context

ADR-0005 quy định branching model nhưng chưa định nghĩa: yêu cầu mới được ghi nhận ở đâu, nhánh chức năng được đặt tên thế nào, thay đổi được review/merge ra sao, và cơ chế xác nhận nguồn `verify` → `master`. Người dùng yêu cầu quy trình đầy đủ: (1) đăng bug/nâng cấp/ý tưởng lên GitHub Issue; (2) nhận issue → tạo nhánh tên hệ thống → tạo PR rồi sửa; (3) duyệt rồi merge thủ công; (4) xác nhận source từ `verify` sang main dựa trên PR. Lưu ý: yêu cầu ghi "main" nhưng repo dùng nhánh `master` — **giữ nguyên `master`** (đổi tên nhánh default rủi ro cao, không cần thiết).

## Decision

### 1. Issue là nguồn yêu cầu duy nhất

- Mọi bug / nâng cấp / ý tưởng thay đổi hệ thống phải được đăng lên GitHub Issue qua 1 trong 3 template chuẩn (`.github/ISSUE_TEMPLATE/`: `bug-report`, `feature-upgrade`, `idea-proposal`).
- Blank issue bị tắt (`.github/ISSUE_TEMPLATE/config.yml`: `blank_issues_enabled: false`).
- Issue được đánh số tự động → `ISSUE-N`; là id tham chiếu xuyên suốt (branch, PR, LOG.md, task folder).

### 2. Tạo nhánh từ verify, tên có hệ thống

- **BẮT BUỘC xin xác nhận người dùng TRƯỚC khi tạo nhánh** — agent KHÔNG tự ý tạo nhánh mà phải trình bày kế hoạch (tên nhánh, lý do, issue tham chiếu) và đợi người dùng đồng ý.
- Nhánh chức năng tạo TỪ `verify` (sau khi refresh: `git fetch origin` → `git checkout verify` → `git pull origin verify`), KHÔNG từ `master` (giữ ADR-0005).
- Quy ước tên: `<type>/ISSUE-<N>-<slug>` với `<type> ∈ {feature, fix, docs, operation, refactor, test}` map theo loại issue (bug → `fix/`, nâng cấp → `feature/`, ý tưởng → `feature/` hoặc `docs/`, còn lại giữ nguyên).
- Fix nhỏ không có issue: `<type>/bypass-<slug>` (khẩn cấp: `hotfix/bypass-<slug>`) — kèm dòng `[bypass]` trong PR body.

### 3. PR-driven: tạo PR sớm, sửa trên PR

- Sau commit đầu tiên có ý nghĩa → tạo PR ngay (draft nếu chưa xong), base = `verify`; mọi commit tiếp theo push lên chính nhánh → PR tự cập nhật.
- Tooling chuẩn: GitHub CLI `gh` (`gh auth login` + `gh auth setup-git`).
- PR title: `<type>/ISSUE-<N>: <mô tả>`; bypass: `<type>/bypass-<slug>: <mô tả>`; promotion: `release: verify → master (YYYY-MM-DD)` (ký tự `→` = U+2192).
- PR body theo template — bắt buộc link issue (`Fixes #N`/`Refs #N`; KHÔNG `Closes #N` cho feature → verify vì GitHub tự đóng issue trước promotion) hoặc `[bypass]`.

### 4. Merge thủ công

- KHÔNG bot tự merge / auto-approve / auto-label. Người dùng review và bấm nút Merge.
- PR feature → merge vào `verify`; merge local chỉ hợp lệ cho feature → verify; `master` CHỈ cập nhật qua merge button của PR promotion.

### 5. Xác nhận nguồn verify → master dựa trên PR

- Sau khi `verify` PASS (test + hard gate + review), code về `master` chỉ qua **PR promotion** `verify` → `master` (`release: verify → master (YYYY-MM-DD)`), body bắt buộc mục `Issues included: #N, ...` + bằng chứng test/hard gate.
- Promotion là all-or-nothing → promote thường xuyên, nhỏ, nhanh.

### 6. Kiểm tra tự động (nhẹ, không can thiệp)

- `.github/workflows/pr-validation.yml` — `actions/github-script@v7`, permissions `{contents: read, issues: read}`, concurrency theo PR; KHÔNG checkout (đọc thẳng event payload).
- Luồng quyết định tuyến tính 7 bước: (1) draft → skip; (2) title `^release:` → base = master, skip body-check; (3) base ≠ verify → fail; (4) body có `[bypass]` → pass; (5) title `type/ISSUE-N` → body phải có link issue (optional `issues.get` — mọi lỗi chỉ warning); (6) title `type/(bypass|hotfix)-slug` → body phải có `[bypass]`; (7) còn lại → fail.
- Check fail hiển thị ✗; merge thực sự bị chặn khi người dùng bật required status checks (branch protection — hướng dẫn trong docs).

## Consequences

- **Positive**: yêu cầu có traceability đầy đủ (issue → branch → PR → verify → master); `master` chỉ nhận nguồn đã kiểm chứng qua PR; action chặn các vi phạm phổ biến (base master, title sai, thiếu link issue); quy trình deterministic, agent thực thi được qua `gh` CLI.
- **Negative**: thêm bước tạo PR + PR promotion (2 lần merge); action là chi phí bảo trì (regex/phạm vi); promotion all-or-nothing yêu cầu promote thường xuyên.
- **Bảo trì**: danh sách prefix `<type>` nằm ở 2 nơi (docs `issue-pr-workflow.md` GĐ2 + regex `pr-validation.yml`) — thêm prefix mới phải cập nhật đồng bộ cả 2. Body-check chỉ xác nhận "có link" chứ không xác minh đúng issue (giới hạn chấp nhận).
- **Ghi chú**: "main" trong yêu cầu người dùng = nhánh `master` hiện tại — giữ nguyên `master`, không đổi tên.
