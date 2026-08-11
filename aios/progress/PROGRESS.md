# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `in-progress` |
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

## M1 — Core Runtime (in-progress)

### P0 — Infrastructure (TASK-002) ✅
| Bước | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| 1 | Spec + critique ×2 + tasks + review | `done` | critic ×2 (19 vấn đề resolved), reviewer (8 vấn đề resolved) |
| 2 | Implement: scaffold monorepo + aios_core (config/logging/metadata/healthcheck) | `done` | commits 7a270ff + 486fb9f |
| 3 | Test + Evaluate | `done` | 32 tests pass, coverage 96.14%, 16/16 AC |
| 4 | Commit | `done` | working tree sạch |

### P0.5 — Runtime Kernel (TASK-003 + TASK-004)

**TASK-003 — Kernel Foundations** ✅ (2026-08-12)
- semver helper + contracts version hóa (ContractVersion, ContractMetadata, ArtifactContract, CompatibilityChecker 5-rule) + DI Container + EventBus + ExecutionPlan
- 107 tests pass (75 mới), coverage 94.82%, 20/20 AC — commit e3bfc54

**TASK-004 — Runtime Services** (9 services + RuntimeKernel wiring) — todo

## Tasks

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-001 | M0 — Development Foundation | M0 | `done` ✅ | AIOS Orchestrator |
| TASK-002 | M1-P0 — Scaffold monorepo + backend core | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-003 | M1-P0.5a — Kernel Foundations: contracts + DI + event bus + execution plan | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-004 | M1-P0.5b — Runtime Services: 9 services + RuntimeKernel | M1 | `todo` | AIOS Orchestrator |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-12 | TASK-003 | D5.1 | 107 tests pass ×2 nơi, coverage 94.82%, 20/20 AC` → done
2. `2026-08-12 | TASK-003 | D2-D4 | Implement + fix 5 lỗi thật (pydantic, container, event bus)` → done
3. `2026-08-12 | TASK-003 | critique ×2 + review | resolve toàn bộ trước implement` → done
