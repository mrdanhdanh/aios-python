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

## 4. Commit

- Commit sau mỗi bước hoàn chỉnh (không gộp lung tung).
- Message commit ngắn gọn, tiền tố milestone/phase: `M0: tạo ...`.
- Luôn commit trước khi kết thúc phiên.

## 5. Ngôn ngữ

- Tài liệu tiến độ (`aios/progress/`) và trao đổi với người dùng: **tiếng Việt**.
- Code, tên biến, tên file, commit message: **tiếng Anh** (trừ tài liệu).
