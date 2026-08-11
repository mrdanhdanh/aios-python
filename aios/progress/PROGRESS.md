# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `todo` ← next |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `todo` |
| M3 | Desktop Edition (P5–P6: dashboard, VS Code extension) | `todo` |
| M4 | Platform Edition (P7–P8: upgrade pipeline, observability) | `todo` |
| M5 | Enterprise Edition (tương lai — không làm v1) | `todo` |

## M0 — Development Foundation ✅

| Bước | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| B0 | git init + docs/PLAN.md + AGENTS.md + .gitignore + commit | `done` | commit e50b715 |
| B1 | Tạo 4 VS Code custom agent (.github/agents/) | `done` | orchestrator + spec-writer + critic + reviewer |
| B2 | Tạo aios/progress/ (PROGRESS, LOG, STATS, TASK-001) | `done` | TASK-001 đủ 8 file, critique ×2 đã resolve |
| B3 | Commit lần cuối M0 | `done` | commit 08f1efa + c2d1032 |
| B4 | Verify M0 (agent picker, hard gate) | `done` | người dùng xác nhận B4.2/B4.3 2026-08-11 |

## Tasks

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-001 | M0 — Development Foundation | M0 | `done` ✅ | AIOS Orchestrator |
| TASK-002 | M1 — Scaffold monorepo (backend/, sdk/, pyproject, config, logging) | M1 | `todo` | AIOS Orchestrator |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-11 | TASK-001 | B4 | Người dùng xác nhận agent picker + hard gate` → done — M0 ĐÓNG
2. `2026-08-11 | TASK-001 | evaluation | ĐẠT spec — 7/7 AC pass` → done
3. `2026-08-11 | TASK-001 | B3/B4 | Verify tự động B4.1/4.4/4.5 pass + commits` → done
