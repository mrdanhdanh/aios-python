# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `in-progress` |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `todo` |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `todo` |
| M3 | Desktop Edition (P5–P6: dashboard, VS Code extension) | `todo` |
| M4 | Platform Edition (P7–P8: upgrade pipeline, observability) | `todo` |
| M5 | Enterprise Edition (tương lai — không làm v1) | `todo` |

## M0 — Development Foundation

| Bước | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| B0 | git init + docs/PLAN.md + AGENTS.md + .gitignore + commit | `done` | commit e50b715 |
| B1 | Tạo 4 VS Code custom agent (.github/agents/) | `done` | orchestrator + spec-writer + critic + reviewer |
| B2 | Tạo aios/progress/ (PROGRESS, LOG, STATS, TASK-001) | `done` | TASK-001 đủ 8 file, critique ×2 đã resolve |
| B3 | Commit lần cuối M0 | `in-progress` | đang thực hiện |
| B4 | Verify M0 (agent picker, hard gate) | `todo` | cần người dùng xác nhận thủ công |

## Tasks

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-001 | M0 — Development Foundation (chính task này) | M0 | `in-progress` | AIOS Orchestrator |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-11 | TASK-001 | B2 | Tạo progress system + spec + critique ×2 + review + implement` → done
2. `2026-08-11 | TASK-001 | critique-2 | P2 (verify subagent) + P3 (STATS Bài học) → resolved` → done
3. `2026-08-11 | TASK-001 | critique-1 | P1 gitignore + P2 rule phân loại task + P3 → resolved` → done
