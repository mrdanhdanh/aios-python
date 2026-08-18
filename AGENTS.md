# AGENTS.md — Quy tắc bắt buộc cho mọi AI agent làm việc trong repo này

> File này được áp dụng cho MỌI session làm việc (bất kể agent nào: default, plan, ask, hay AIOS Orchestrator).
> Vi phạm quy tắc dưới đây = làm sai quy trình dự án.

## 1. Nguồn sự thật là REPO, không phải bộ nhớ phiên

- **BẮT ĐẦU phiên**: đọc `docs/PLAN.md` + `aios/progress/PROGRESS.md` + `aios/progress/LOG.md` TRƯỚC khi làm bất cứ việc gì.
- **KẾT THÚC phiên (hoặc mỗi phase)**: cập nhật `aios/progress/` + commit.
- Nếu không nhớ "đã làm tới đâu" → đọc `PROGRESS.md`, KHÔNG hỏi lại người dùng và KHÔNG tự suy đoán.
- Không bao giờ tạo cấu trúc quan trọng chỉ trong chat session — phải nằm trong repo, git-tracked.

## 2. Quy trình bắt buộc cho mỗi task (Hard Gate)

Mọi công việc được chia thành task có id `TASK-xxx` trong `aios/progress/tasks/TASK-xxx/`.

Chuỗi bắt buộc — task chỉ được đánh dấu `done` khi ĐỦ TẤT CẢ:

1. **Plan** — ghi kế hoạch vào PROGRESS.md
2. **Spec** — `spec.md` (mục tiêu, phạm vi, input/output, tiêu chí chấp nhận)
3. **Critique ×2** — `critique-1.md` → resolve → `critique-2.md` → resolve (đủ 2 vòng, phản biện độc lập)
4. **Task** — `tasks.md`: breakdown thành checklist nhỏ có checkbox
5. **Review** — `review.md` trước khi implement
6. **Implement** — code theo spec, ghi LOG.md song song
7. **Test** — `test.md` + chạy test thật
8. **Evaluate** — `evaluation.md`: đối chiếu tiêu chí chấp nhận, bài học

**Hard gate**: TỪ CHỐI implement nếu chưa đủ spec + 2 critique đã resolve. Nêu rõ lý do cho người dùng.

**Bypass hợp lệ** (chỉ cho fix nhỏ: 1 dòng, typo, sửa nhanh): được phép làm ngay NHƯNG bắt buộc:
- Ghi entry `[bypass]` vào `LOG.md` kèm lý do
- Đánh dấu `[bypass]` trong PROGRESS.md

## 3. Log & Progress bắt buộc

- **`aios/progress/LOG.md`**: ghi SAU MỖI hành động có ý nghĩa. Format:
  `YYYY-MM-DD HH:MM | TASK-xxx | bước | việc đã làm | kết quả | artifact (đường dẫn)`
- **`aios/progress/PROGRESS.md`**: cập nhật trạng thái mỗi task sau mỗi thay đổi (todo/in-progress/done/blocked).
- **`aios/progress/STATS.md`**: tổng hợp khi kết thúc milestone.

## 3.1. Definition of Done — Closing Checklist (bắt buộc, KHÔNG bỏ qua)

Sau khi xử lý XONG mỗi yêu cầu/task (kể cả bypass fix nhỏ), TRƯỚC khi tuyên bố hoàn thành hoặc chuyển sang việc khác, phải đóng đủ checklist sau — đối chiếu lần lượt, thiếu cái nào bổ sung cái đó:

- [ ] **`aios/progress/LOG.md`** — ghi entry mới đúng format (thời gian | task | bước | việc đã làm | kết quả | artifact)
- [ ] **`aios/progress/PROGRESS.md`** — cập nhật trạng thái task/milestone/phase (todo/in-progress/done/blocked) + bảng tasks nếu có
- [ ] **`docs/PLAN.md`** — cập nhật nếu milestone/phase/plan/ADR bị ảnh hưởng (trạng thái, ghi chú, quyết định mới)
- [ ] **`aios/progress/STATS.md`** — cập nhật nếu kết thúc milestone hoặc cần tổng hợp số liệu
- [ ] **Task folder `aios/progress/tasks/TASK-xxx/`** — đủ 8-file hard gate + artifact (implementation/, test.md, evaluation.md...)
- [ ] **Commit** — sau mỗi bước hoàn chỉnh; chắc chắn working tree sạch trước khi kết thúc phiên

Quy tắc: KHÔNG được nói "xong" khi checklist chưa đóng đủ. Nếu quên giữa chừng (phát hiện khi đã chuyển việc khác) → quay lại đóng checklist ngay trước khi tiếp tục, ghi rõ trong LOG.md.

## 4. Commit

- Commit sau mỗi bước hoàn chỉnh (không gộp lung tung).
- Message commit ngắn gọn, tiền tố milestone/phase: `M0: tạo ...`.
- Luôn commit trước khi kết thúc phiên.

## 4.1. Branching Model (BẮT BUỘC — xem ADR-0005)

- **`master`** = nhánh ổn định duy nhất, CHỈ nhận thay đổi từ `verify` (không commit trực tiếp, không nhận nhánh khác).
- **`verify`** = trạm kiểm tra bắt buộc: mọi thay đổi phải đi qua `verify` trước khi về `master`.
- **Nhánh chức năng** (feature/fix/docs/...) phải tạo TỪ `verify` (KHÔNG tạo từ `master`), tên có tiền tố loại: `feature/`, `fix/`, `docs/`, `operation/`, `refactor/`, `test/`...
- **Chuỗi bắt buộc**: nhánh chức năng (từ `verify`) → merge vào `verify` → kiểm tra trên `verify` (test + hard gate + review) → `verify` → `master` (chỉ khi verify PASS).
- Vi phạm (tạo nhánh từ master, commit thẳng master, merge thẳng master) = sai quy trình, phải sửa lại.

## 4.2. Issue-Driven Development (BẮT BUỘC — xem ADR-0006 + docs/workflows/issue-pr-workflow.md)

Mọi thay đổi hệ thống phải đi qua chuỗi **Issue → Branch → PR → Merge thủ công → verify → master**:

- **Issue**: mọi bug / nâng cấp / ý tưởng phải đăng lên GitHub Issue qua 1 trong 3 template (`.github/ISSUE_TEMPLATE/`). Fix nhỏ không có issue → đánh dấu `[bypass]` trong PR body + LOG.md.
- **Branch**: nhánh chức năng tạo TỪ `verify` (refresh `verify` trước), tên `<type>/ISSUE-<N>-<slug>` (bug → `fix/`, nâng cấp → `feature/`, tài liệu → `docs/`, fix nhỏ → `fix/bypass-<slug>` hoặc `hotfix/bypass-<slug>`). **Agent PHẢI xin xác nhận người dùng TRƯỚC khi chạy lệnh tạo nhánh** — KHÔNG tự ý tạo.
- **PR**: tạo PR ngay sau commit đầu (draft nếu chưa xong), base = `verify`, title `<type>/ISSUE-<N>: <mô tả>`, body bắt buộc link issue (`Fixes #N`/`Refs #N` — KHÔNG `Closes` cho PR feature→verify) hoặc `[bypass]`. Dùng GitHub CLI `gh` (đã `gh auth login` + `gh auth setup-git`).
- **Merge thủ công**: người dùng review + bấm Merge — KHÔNG bot tự merge. PR feature → `verify`; `master` CHỈ cập nhật qua PR promotion `release: verify → master (YYYY-MM-DD)` (body có `Issues included` + bằng chứng test/hard gate) do người dùng duyệt.
- **Kiểm tra tự động**: `.github/workflows/pr-validation.yml` chặn PR sai title/base/thiếu link issue. PR đầu tiên của chính workflow (chưa trên default branch) không chạy action — chấp nhận.
- Vi phạm (thay đổi không qua issue, PR nhắm base master, merge thẳng master) = sai quy trình, phải sửa lại. Chi tiết: `docs/workflows/issue-pr-workflow.md`.

## 5. Ngôn ngữ

- Tài liệu tiến độ (`aios/progress/`) và trao đổi với người dùng: **tiếng Việt**.
- Code, tên biến, tên file, commit message: **tiếng Anh** (trừ tài liệu).
- Chi tiết branching model: [ADR-0005](docs/adr/0005-branching-model.md).
