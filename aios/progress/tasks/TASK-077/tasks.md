# Tasks.md — TASK-077 Quy trình Issue → Branch → PR → Merge thủ công → verify → master

## Checklist

### T1 — Plan & hard gate
- [x] T1.1 Plan ghi PROGRESS.md + tạo task folder (8-file)
- [x] T1.2 Spec v3 (3 vòng: v1 → resolve C1 → v2 → resolve C2 → v3)
- [x] T1.3 Critique-1 + critique-2 (đủ 2 vòng, đã resolve)
- [x] T1.4 Tasks.md (file này) + review.md

### T2 — Implement (theo spec v3)
- [ ] T2.1 `.github/ISSUE_TEMPLATE/bug-report.yml`
- [ ] T2.2 `.github/ISSUE_TEMPLATE/feature-upgrade.yml`
- [ ] T2.3 `.github/ISSUE_TEMPLATE/idea-proposal.yml`
- [ ] T2.4 `.github/ISSUE_TEMPLATE/config.yml` (`blank_issues_enabled: false` + contact_links)
- [ ] T2.5 `.github/pull_request_template.md` (link issue + bypass section + checklist)
- [ ] T2.6 `.github/workflows/pr-validation.yml` (github-script@v7, luồng quyết định 7 bước, concurrency)
- [ ] T2.7 `docs/workflows/issue-pr-workflow.md` (5 giai đoạn + lệnh gh/git + sơ đồ)
- [ ] T2.8 `docs/adr/0006-issue-pr-workflow.md` (extends ADR-0005, main = master)
- [ ] T2.9 Cập nhật `AGENTS.md` §4.2 (Issue-Driven Development bắt buộc)
- [ ] T2.10 Cập nhật `docs/PLAN.md` (link ADR-0006 + workflow docs)
- [ ] T2.11 Nộp bản sao deliverables vào `implementation/` (AGENTS.md §3.1 — artifact bắt buộc)

### T3 — Test
- [ ] T3.1 YAML parse 3 templates + config.yml + workflow (python)
- [ ] T3.2 Schema assertions AC1 (name/about/labels/body types) + workflow (name/on/jobs/types/concurrency) — ⚠️ PyYAML parse key `on:` thành boolean `True`: assert `data.get('on') or data.get(True)` (quirk YAML 1.1)
- [ ] T3.3 Script mô phỏng luồng quyết định action ≥ 14 case (mọi nhánh: draft/release/base/bypass/ISSUE/fail) — dùng **Python** (thống nhất với T3.1/T3.2); body-check chỉ scan body, KHÔNG scan title
- [ ] T3.4 Markdown docs đủ heading/mục theo checklist AC5/AC6/AC7
- [ ] T3.5 Ghi kết quả vào test.md

### T4 — Evaluate & close
- [ ] T4.1 evaluation.md (đối chiếu 10 AC + bài học)
- [ ] T4.2 LOG.md entry + PROGRESS.md cập nhật
- [ ] T4.3 Commit trên nhánh `docs/issue-pr-workflow` (tạo từ verify) + working tree sạch
- [ ] T4.4 Ghi chú dogfooding: PR TASK-077 body có `[bypass]` (không có ISSUE-N); PR đầu tiên không chạy action (C2-05) → xác nhận bằng script mô phỏng + PR thử nghiệm nhỏ sau khi merge workflow vào verify/master

## Ghi chú

- PR của chính task này (C1-17/C2-02/C2-05): title không có ISSUE-N; body PR sẽ có dòng `[bypass]`; action chưa chạy trên PR đầu (workflow chưa trên default branch) — kiểm chứng bằng script mô phỏng.
- Sau khi merge vào verify: chạy 1 PR thử nghiệm nhỏ để xác nhận action chạy thật.
