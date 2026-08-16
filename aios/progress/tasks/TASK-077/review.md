# Review — TASK-077 (bởi Reviewer, trước implement)

> Kết luận: **APPROVED CÓ ĐIỀU KIỆN** — spec v3 đủ chi tiết để implement, không có R1 (blocking).

## Đối chiếu tiêu chí chấp nhận

- [x] AC1: đủ chi tiết (frontmatter `name`/`about`/`labels` string-hoặc-list, body types, `validations.required` boolean) — đúng chuẩn GitHub theo C2-01
- [x] AC2: yêu cầu rõ link issue + bypass section + checklist
- [x] AC3: luồng 7 bước tuyến tính, regex cụ thể, thứ tự ưu tiên rõ, base-branch check, optional `issues.get` try/catch — đủ để code chính xác
- [x] AC4: permissions `{contents: read, issues: read}`, không checkout, single-quoted YAML, `\u2192` trong JS (không trong YAML), concurrency
- [x] AC5/AC6/AC7/AC8: nội dung docs/ADR/AGENTS/PLAN mô tả đầy đủ, khớp hiện trạng repo (`.github/workflows/` chỉ có secret-scan.yml ✓, ADR-0006 trống ✓, PLAN.md có mục Branching Model ✓, pyyaml trong pyproject ✓)
- [x] AC9: 5 hạng mục test cụ thể, khả thi (PyYAML có sẵn)
- [x] AC10: dogfooding `[bypass]` + ghi chú C2-05 (PR đầu không chạy action) nhất quán giữa spec/AC/tasks.md

## Vấn đề phát hiện & resolution

| # | Mức | Vấn đề | Resolution |
|---|-----|--------|------------|
| R1-1 | R2 | tasks.md T2.1–T2.10 đánh `[x]` nhưng implementation CHƯA xảy ra | RESOLVED — uncheck T2.1–T2.10 (chỉ check khi làm thật) |
| R1-2 | R2 | tasks.md thiếu checklist item cho artifact `implementation/` (AGENTS.md §3.1) | RESOLVED — thêm T2.11 "Nộp bản sao deliverables vào implementation/" |
| R1-3 | R2 | AC9-2 chưa ghi chú quirk PyYAML: key `on:` parse thành boolean `True` → assert `'on' in data` sẽ false-fail | RESOLVED — T3.2 ghi chú: assert `data.get('on') or data.get(True)` |
| R1-4 | R3 | Critique-2 bảng C2-11 còn text cũ `(Fixes\|Closes\|Refs)` mâu thuẫn GĐ3 (không dùng Closes) | RESOLVED — sửa bảng C2-11 khớp spec |
| R1-5 | R3 | AC4 "≥12 case" vs AC9 "≥14 case" | RESOLVED — thống nhất ≥14 (tasks.md T3.3) |
| R1-6 | R3 | Giới hạn `name` ≤80 ký tự ít chắc chắn (GitHub docs chỉ rõ `about` ≤190) | GHI NHẬN — giữ assert an toàn, template tự tuân thủ; test theo đúng chuẩn đã ghi |
| R1-7 | R3 | Body-check bước 5 chỉ scan `body`, không scan title (tránh false-positive vì title chứa ISSUE-N) | RESOLVED — ghi chú vào T3.3 |
| R1-8 | R3 | T3.3 chưa nói rõ ngôn ngữ script mô phỏng | RESOLVED — dùng Python (thống nhất T3.1/T3.2) |

## Kết luận

- [x] **APPROVED CÓ ĐIỀU KIỆN** — không R1; trước khi chạy T2: (1) uncheck T2.1–T2.10, (2) thêm item `implementation/` (T2.11), (3) ghi chú PyYAML `on:` vào T3.2. R3 đã ghi nhận, không chặn.
- [ ] REJECTED

*Ghi chú: reviewer không có công cụ chỉnh sửa file → nội dung được orchestrator lưu vào review.md sau khi áp resolution.*
