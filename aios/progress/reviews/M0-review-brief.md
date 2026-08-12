# Review M0 — Development Foundation

> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem `M0-review.md` (bản review nội bộ của AIOS Orchestrator).

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M4). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M0 – Development Foundation" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu)
- `AGENTS.md` — quy tắc vận hành dự án

## 2. Nhiệm vụ

Review milestone **M0** — Development Foundation (khởi động dự án: master plan trong repo, VS Code custom agents, hệ thống progress/log, task mẫu).

Đánh giá độc lập 3 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M0 không
2. **Đúng quy trình**: hard gate có được tuân thủ cho TASK-001 không
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế có khớp nhau không

## 3. Deliverable cần kiểm tra

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 1 | `docs/PLAN.md` | Tồn tại, đúng master plan v6, mục M0 rõ ràng |
| 2 | `AGENTS.md` | Tồn tại, quy tắc đọc PROGRESS đầu phiên + ghi LOG sau mỗi hành động |
| 3 | `.gitignore` | Tồn tại, có nội dung hợp lý (không chặn nhầm file cần thiết) |
| 4 | `.github/agents/aios-orchestrator.agent.md` | Frontmatter hợp lệ (description keyword-rich, `user-invocable: true`, tools, agents); body có hard gate + bypass rules + rule phân loại TASK |
| 5 | `.github/agents/spec-writer.agent.md` | Tồn tại, `user-invocable: false` |
| 6 | `.github/agents/critic.agent.md` | Tồn tại, `user-invocable: false`, quy định phản biện 2 vòng |
| 7 | `.github/agents/reviewer.agent.md` | Tồn tại, `user-invocable: false` |
| 8 | `aios/progress/PROGRESS.md` | Có mục M0, trạng thái từng bước B0–B4, khớp git history |
| 9 | `aios/progress/LOG.md` | Entry cho TỪNG bước M0 (B0→B4) đúng format `thời gian \| task \| bước \| việc \| kết quả \| artifact` |
| 10 | `aios/progress/STATS.md` | Có mục M0: task, critique resolve, bypass, commit |
| 11 | `aios/progress/tasks/TASK-001/` | **Đủ 8 file**: spec.md, critique-1.md, critique-2.md, tasks.md, review.md, test.md, evaluation.md, implementation/ |
| 12 | Git history | `git log --oneline` có ≥5 commit M0 (Bước 0 → B4) |

## 4. Tiêu chí chấp nhận (nguồn: PLAN.md → Verification M0)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|------------------|---------------------|
| V1 | Agent picker hiển thị "AIOS Orchestrator", chọn được, mọi request đi qua nó | Đọc frontmatter agent file + test.md TASK-001 (B4.2) | `user-invocable: true`; test.md ghi nhận người dùng xác nhận |
| V2 | Hard gate: yêu cầu implement task chưa có spec+critique → agent từ chối | Đọc body agent file + test.md TASK-001 (B4.3) | Rule hard gate có trong file; test.md ghi nhận xác nhận thủ công |
| V3 | Bypass: fix nhỏ → thực hiện nhưng LOG.md có entry `[bypass]` kèm lý do | Đọc quy tắc trong agent + tìm entry thật trong LOG.md | Quy tắc tồn tại; **kiểm tra thêm**: có/không có entry `[bypass]` thực tế (không có cũng hợp lệ, chỉ cần quy tắc) |
| V4 | Progress: PROGRESS.md/LOG.md cập nhật sau mỗi bước; TASK-xxx đủ 8 file | Đối chiếu PROGRESS ↔ LOG ↔ git; đếm file trong tasks/TASK-001/ | Mỗi bước có entry LOG; 8 file/task; trạng thái khớp nhau |
| V5 | Critique ×2: task không thể done khi chỉ có 1 critique | Đếm + đọc critique-1.md, critique-2.md | Đủ 2 file, cả 2 có resolution; mục "resolve" ghi rõ |

## 5. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 4: tìm bằng chứng → kết luận **PASS/FAIL** kèm trích dẫn `file:đường dẫn`
3. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật nếu có quyền)
4. Tìm lỗ hổng chủ động: file thiếu, nội dung mâu thuẫn giữa các file, checkbox chưa tick, claim không có bằng chứng, frontmatter sai
5. Với TASK-001: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
6. Phân mức findings: **P1** (sai mục tiêu/tiêu chí — phải sửa trước khi chấp nhận), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 6. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review M0 — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả | Bằng chứng (file + trích dẫn) |

## 2. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 3. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 4. Điểm mạnh (nếu có)
## 5. Gợi ý cải thiện (không bắt buộc)
```
