# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `done` ✅ |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `todo` ← next |
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

### P0.5 — Runtime Kernel (TASK-003 + TASK-004 + TASK-005)

**TASK-003 — Kernel Foundations** ✅ (2026-08-12)
- semver + contracts + DI container + event bus + execution plan — 107 tests, coverage 94.82%, 20/20 AC

**TASK-004 — Kernel Services I** ✅ (2026-08-12)
- Context + EventService (audit SQLite) + ArtifactService (sidecar) + PermissionService + PolicyService
- 162 tests pass, coverage 94.77%, 13/13 AC — commit eb64795

**TASK-005 — Kernel Services II** ✅ (2026-08-12)
- Scheduler + State + Resource + ExecutionService + RuntimeKernel (9 services wiring)
- 207 tests pass, coverage 95.32%, 15/15 AC — commit code M1-P0.5c

### P1 — Model + Memory + Knowledge

**TASK-006 — Model Contract + Providers** ✅ (2026-08-12)
- ModelContract template-method + Mock/OpenAI/Ollama + ModelRegistry + RuntimeKernel wiring
- 233 tests pass, coverage 94.73%, 13/13 AC

**TASK-007 — Memory 4 loại + Knowledge pipeline** ✅ (2026-08-12)
- Conversation (SQLite) + Session (cache) + Knowledge (chunks+vectors cùng file) + Artifact (TASK-004)
- 270 tests pass, coverage 94.90%, 12/12 AC

### P2 — Workflow + Capability + Catalog

**TASK-008 — Workflow Definition + Compilers + Library** ✅ (2026-08-12)
- Declarative definition + DAG helper + MockCompiler + LangGraph stub + Library + CLI simulate
- **Deliverable M1 đạt: `aiagent run workflow.yaml --simulate` chạy được**
- 300 tests pass, coverage 94.92%, 10/10 AC

**TASK-009 — Capability + Prompt Registry + Catalog + Knowledge Graph** ✅ (2026-08-12)
- CapabilityRegistry + PromptRegistry (str.format v1) + SystemCatalog + KnowledgeGraph + PLAN amend
- **346 tests pass, coverage 95.30% — M1 HOÀN TẤT (9/9 tasks)**

## M1 — Core Runtime ✅ (2026-08-12)
**Toàn bộ P0–P2 xong**: 9 services + contracts + DI + event bus + models (Mock/OpenAI/Ollama) + memory 4 loại + knowledge pipeline + workflow (CLI simulate) + capability + prompt + catalog + knowledge graph. Deliverable `aiagent run workflow.yaml --simulate` ✓

## Tasks

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-001 | M0 — Development Foundation | M0 | `done` ✅ | AIOS Orchestrator |
| TASK-002 | M1-P0 — Scaffold monorepo + backend core | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-003 | M1-P0.5a — Kernel Foundations | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-004 | M1-P0.5b — Kernel Services I (context, event+audit, artifact, permission, policy) | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-005 | M1-P0.5c — Kernel Services II (scheduler, state, resource, execution) + RuntimeKernel | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-006 | M1-P1a — Model Contract + providers (Mock/OpenAI/Ollama) | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-007 | M1-P1b — Memory 4 loại + Knowledge pipeline | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-008 | M1-P2a — Workflow Definition + compilers + library + CLI | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-009 | M1-P2b — Capability + Prompt Registry + Catalog + Knowledge Graph | M1 | `done` ✅ | AIOS Orchestrator |
| TASK-010 | M2-P3a — AIOS Orchestrator v1 (Decision Pipeline 4 tầng + Workflow Matcher) | M2 | `todo` | AIOS Orchestrator |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-12 | TASK-003 | D5.1 | 107 tests pass ×2 nơi, coverage 94.82%, 20/20 AC` → done
2. `2026-08-12 | TASK-003 | D2-D4 | Implement + fix 5 lỗi thật (pydantic, container, event bus)` → done
3. `2026-08-12 | TASK-003 | critique ×2 + review | resolve toàn bộ trước implement` → done
