# Evaluation — TASK-077 Quy trình Issue → Branch → PR → Merge thủ công → verify → master

## Đối chiếu tiêu chí chấp nhận (AC1–AC10)

| AC | Nội dung | Kết quả | Bằng chứng |
|----|----------|---------|------------|
| AC1 | 3 issue templates + config.yml, đúng chuẩn GitHub forms | ✅ | T2 — 18/18 schema assertions (name/about/labels/body types/validations) |
| AC2 | PR template: link issue + [bypass] + test + checklist | ✅ | `.github/pull_request_template.md` + T2 3/3 |
| AC3 | Action validate: luồng quyết định 7 bước, base check, draft skip, không auto-merge | ✅ | `.github/workflows/pr-validation.yml` + T3 20/20 (mọi nhánh) |
| AC4 | Chỉ github-script@v7, permissions read-only, concurrency, single-quoted YAML | ✅ | T2 workflow 7/7; `\u2192` trong JS (không trong YAML) |
| AC5 | Docs 5 giai đoạn + quy ước nhánh + lệnh gh/git PowerShell + sơ đồ | ✅ | `docs/workflows/issue-pr-workflow.md` — T4 10/10 mục |
| AC6 | ADR-0006 accepted, extends ADR-0005, main = master | ✅ | `docs/adr/0006-issue-pr-workflow.md` — T4 6/6 |
| AC7 | AGENTS.md §4.2 Issue-Driven Development | ✅ | AGENTS.md + T4 |
| AC8 | PLAN.md link ADR-0006 + workflow docs | ✅ | T4 |
| AC9 | Test thật: YAML parse + schema + mô phỏng ≥14 case + docs checklist + 8-file | ✅ | **78 PASS / 0 FAIL**; 20 case mô phỏng; 8-file đủ |
| AC10 | Nhánh `docs/issue-pr-workflow` từ verify; dogfooding [bypass]; working tree sạch | ✅ | nhánh tạo từ verify (git); PR body sẽ có [bypass]; commit cuối |

## Đánh giá quy trình (process)

- Hard gate đủ chuỗi: spec v3 (3 vòng sửa từ 2 critique độc lập) → critique-1 (4 P1/7 P2/6 P3 resolved) → critique-2 (2 P1/4 P2/6 P3 resolved) → review (APPROVED có điều kiện, R2 đã resolve) → implement → test (78/78) → evaluate.
- 2 critic vòng độc lập đã bắt được các lỗi chuẩn GitHub quan trọng (key `about` vs `description`, quirk PyYAML `on:`, permissions `issues: read`, draft skip, base branch check) — giá trị của hard gate thể hiện rõ.

## Bài học & đề xuất

1. **Đồng bộ quy ước 2 nơi**: danh sách prefix nằm ở docs + regex action — cần luật "thêm prefix = cập nhật đồng bộ" (đã ghi ADR-0006).
2. **PR đầu tiên không chạy action**: sau khi merge workflow vào `verify`/`master`, cần 1 PR thử nghiệm nhỏ để xác nhận action hoạt động thật (ghi tasks.md T4.4 — chưa thực hiện, thuộc sau merge).
3. **Branch protection là bước người dùng**: action chỉ hiển thị ✗; để merge thực sự bị chặn cần bật required status checks trên GitHub — đã hướng dẫn trong docs, nhắc người dùng khi merge PR này.
4. **Dogfooding thành công**: PR của chính task này tuân thủ quy trình mới (body `[bypass]`, base `verify`).

## Kết luận

**TASK-077 DONE** — 10/10 AC đạt; quy trình Issue → Branch → PR → Merge thủ công → verify → master đã được thiết lập đầy đủ (templates + action + docs + ADR + AGENTS/PLAN).
