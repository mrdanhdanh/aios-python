# Test — TASK-077 Quy trình Issue → Branch → PR → Merge thủ công → verify → master

> Chạy thật: `backend\.venv\Scripts\python aios\progress\tasks\TASK-077\implementation\validate_task077.py`
> Kết quả: **78 PASS / 0 FAIL** (exit code 0) — 2026-08-16

## Kết quả theo nhóm (đối chiếu AC9)

| Hạng mục | Số case | Kết quả | Ghi chú |
|----------|---------|---------|---------|
| T1 — YAML parse (3 templates + config.yml + pr-validation.yml) | 5 | ✅ 5/5 | PyYAML parse sạch |
| T2 — Schema assertions AC1 (frontmatter `name`/`about`/`labels`/body types/validations) | 18 | ✅ 18/18 | Khớp chuẩn GitHub issue forms (key `about`, không `description` — C2-01) |
| T2 — config.yml (`blank_issues_enabled: false` + contact_links) | 2 | ✅ 2/2 | |
| T2 — workflow (name/on/`types`/jobs/permissions/concurrency/github-script@v7) | 7 | ✅ 7/7 | Quirk PyYAML `on:` → boolean `True` đã xử lý (R2 review) |
| T2 — PR template (issue section + `[bypass]` + checklist) | 3 | ✅ 3/3 | |
| T3 — Mô phỏng luồng quyết định action (7 bước) | 20 | ✅ 20/20 | ≥14 case, mọi nhánh: draft/release/base/bypass/ISSUE/title-format; ≥2 case/nhánh |
| T4 — Docs structure (workflow doc 10 mục, ADR-0006 6 mục, AGENTS §4.2, PLAN links) | 23 | ✅ 23/23 | |

## Test case tiêu biểu (T3 — mô phỏng luồng quyết định)

- `feature/ISSUE-5: ...` + `Fixes #5` + base `verify` → PASS
- `feature/ISSUE-5: ...` + base `master` → FAIL (chặn merge thẳng master — ADR-0005)
- `release: verify → master (2026-08-16)` + base `master` → PASS (skip body-check — C1-02)
- `release: ...` + base `verify` → FAIL
- `fix/bypass-typo` + body `[bypass]` → PASS; thiếu tag → FAIL
- Body `[bypass]` + title bất kỳ → PASS (override title check — C2-02 dogfooding)
- Draft PR → PASS (skip — C1-05)
- Title trống / prefix lạ → FAIL

## Giới hạn đã ghi nhận (không chặn)

- PR đầu tiên của chính workflow (chưa trên default branch) **không chạy action** (C2-05) — kiểm chứng bằng mô phỏng T3 + PR thử nghiệm nhỏ sau khi merge workflow vào verify/master.
- Body-check chỉ xác nhận "có link issue", không xác minh đúng issue (C2-11).
- Action chạy thật trên GitHub (runner) chưa test được local — mô phỏng logic tương đương trong T3.
