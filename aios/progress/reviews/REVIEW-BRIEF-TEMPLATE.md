# Milestone Review Brief — TEMPLATE

> **Mục đích**: tài liệu tự chứa (self-contained) để đem cho một model/người review ĐỘC LẬP đánh giá một milestone.
> **Cách dùng**: copy toàn bộ file này (bản đã điền `{{MILESTONE}}`) sang model review. Model review tự đọc file trong repo và đưa kết luận riêng — KHÔNG xem kết quả review trước đó.
> **Quy tắc**: model review KHÔNG sửa file, chỉ trả về báo cáo theo format mục 6.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M4). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "{{MILESTONE}}" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu)
- `AGENTS.md` — quy tắc vận hành dự án

## 2. Nhiệm vụ

Review milestone **{{MILESTONE}}** — {{MILESTONE_DESCRIPTION}}.

Đánh giá độc lập 3 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho milestone này không
2. **Đúng quy trình**: hard gate (spec/critique ×2/tasks/review/test/evaluate) có được tuân thủ cho từng task không
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế có khớp nhau không

## 3. Deliverable cần kiểm tra

{{DELIVERABLE_LIST — đường dẫn cụ thể từng file/task, đủ để model tự đọc}}

## 4. Tiêu chí chấp nhận (nguồn: PLAN.md → Verification)

{{AC_TABLE — mỗi dòng: tiêu chí | cách kiểm chứng | bằng chứng mong đợi}}

## 5. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 4: tìm bằng chứng → kết luận **PASS/FAIL** kèm trích dẫn `file:đường dẫn`
3. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật nếu có quyền)
4. Tìm lỗ hổng chủ động: file thiếu, nội dung mâu thuẫn giữa các file, checkbox chưa tick, claim không có bằng chứng, tham số khai báo sai frontmatter
5. Với mỗi task: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
6. Phân mức findings: **P1** (sai mục tiêu/tiêu chí — phải sửa trước khi chấp nhận), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 6. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review {{MILESTONE}} — bởi <tên model / reviewer>

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

---

## Cách tạo bản điền sẵn cho milestone mới

Copy template này → đổi tên `{{MILESTONE}}-review-brief.md` → điền 4 placeholder: `{{MILESTONE}}`, `{{MILESTONE_DESCRIPTION}}`, `{{DELIVERABLE_LIST}}`, `{{AC_TABLE}}` (lấy AC từ PLAN.md mục Verification).
