# TASK-077 — Implementation Artifacts

> Pointer tới deliverables thật (theo tiền lệ M7 F2 / M8: implementation/ là pointer, code thật nằm tại vị trí gốc).

## Deliverables

| # | File thật (gốc) | Mô tả |
|---|------------------|-------|
| 1 | `.github/ISSUE_TEMPLATE/bug-report.yml` | Template issue — Bug Report (forms: version, component, steps, expected/actual, environment, severity, checklist) |
| 2 | `.github/ISSUE_TEMPLATE/feature-upgrade.yml` | Template issue — Feature / Upgrade Request |
| 3 | `.github/ISSUE_TEMPLATE/idea-proposal.yml` | Template issue — Idea / System Change Proposal |
| 4 | `.github/ISSUE_TEMPLATE/config.yml` | Tắt blank issue + contact links (docs + workflow guide) |
| 5 | `.github/pull_request_template.md` | Template PR: link issue, [bypass], mô tả, test, checklist |
| 6 | `.github/workflows/pr-validation.yml` | Action validate PR: luồng quyết định 7 bước (draft skip → release → base → bypass → ISSUE → bypass-title → fail), github-script@v7, permissions read-only, concurrency |
| 7 | `docs/workflows/issue-pr-workflow.md` | Hướng dẫn quy trình 5 giai đoạn + lệnh gh/git + sơ đồ mermaid |
| 8 | `docs/adr/0006-issue-pr-workflow.md` | ADR-0006 (accepted, extends ADR-0005, main = master) |
| 9 | `AGENTS.md` §4.2 | Quy tắc Issue-Driven Development bắt buộc cho mọi agent |
| 10 | `docs/PLAN.md` | Cập nhật Branching Model: link ADR-0006 + workflow docs |

## Test

- Script test + kết quả: xem `../test.md`
- Script mô phỏng luồng quyết định action (Python, ≥14 case): chạy trực tiếp tại bước test (lưu trong `test.md`)
