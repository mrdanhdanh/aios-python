# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `done` ✅ (review độc lập PASS) |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `in-progress` |
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
| B5 | **Milestone review M0** (hồi tố, bằng chứng repo) | `done` | 5/5 mục tiêu + 4/5 verification pass; M0 ĐẠT — xem `reviews/M0-review.md` |
| B6 | **Review brief** (template + bản M0) để đem cho model khác review độc lập | `done` | xem `reviews/REVIEW-BRIEF-TEMPLATE.md` + `reviews/M0-review-brief.md` |
| B7 | **Review brief M1** (điền từ template, 7 tiêu chí AC từ PLAN.md) | `done` | xem `reviews/M1-review-brief.md` |
| B7 | **Fix review findings** (F-001..F-004 P3) — bypass fixes + commit | `done` | commits 92f1321 + 3b7d8b6; working tree clean |

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
- 207 tests pass, coverage 95.32%, 15/15 AC — commit code M1-P0.5c (`a3426de`; done `57f1896`)

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

## M1 — Follow-up (P3 remediation) ✅ (2026-08-12)

**TASK-011 — Remediation 9 P3 findings từ M1 v2 independent review** ✅ (2026-08-12)
- F-001 CLI subcommands (doctor / catalog list / workflow validate / contract validate, nested parsers)
- F-002 contract field-evolution regression tests (pydantic dual-class, 4 case direction)
- F-003 Resource FIFO queue (`acquire_slot_wait` blocking + `pending()`), giữ `acquire_slot` non-blocking
- F-004 Context inheritance (PARENT map, `get/get_context/get_all` inherit)
- F-005 Tool/Snapshot events (`SNAPSHOT_SAVED` + `TOOL_STARTED`/`TOOL_FINISHED` emit từ ExecutionService)
- F-006 Catalog `rebuild()` + `_revision` + `is_stale()`
- F-007 CLI dùng `RuntimeKernel.create()` / `SystemCatalog()` (DI đúng chỗ), không còn `ExecutionService(...)` trực tiếp
- F-008 ≥3 ADR (`docs/adr/0001..0003`) + link từ `PLAN.md`
- F-009 Benchmark harness (`tests/test_benchmark.py`, marked skippable)
- **428 tests pass, coverage 95.76%, 9/9 AC — M1 runtime hardening hoàn tất**

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
| TASK-010 | M2-P3a — AIOS Orchestrator v1: Decision Pipeline 4 tầng (Normalizer, Rule Engine, Workflow Matcher, Planner LLM) | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-012 | M2-P3b — Goal Manager + Task Queue + Permission Broker + Failure Recovery | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-011 | M1/P3 — Remediation 9 P3 findings từ M1 v2 review (CLI subcommands, contract field-evolution test, resource queue, context inheritance, tool/snapshot events, catalog rebuild, CLI DI, ADR, benchmark) | M1 (follow-up) | `done` ✅ | AIOS Orchestrator |
| TASK-016 | M2-ARCH — Architecture Hardening: INV-001..010 + AST tests + reference update (docs/architecture.md, ADR-0004, PLAN.md) | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-013 | M2-P3c — Assistants: General + Coder Pipeline + Doctor Pipeline + Safety Layer + System Doctor (Worker Plane — INV-001/002) | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-014 | M2-P4 — Tools 6 loại + Tool Registry + capability binding | M2 | `todo` | AIOS Orchestrator |

## M2 — Developer Edition (in-progress)

**TASK-012 — M2-P3b: Goal Manager + Task Queue + Permission Broker + Failure Recovery** ✅ (2026-08-13)
- `orchestrator/goals/` package mới: goal.py (GoalManager, state machine, cascade cancel), task_queue.py (dequeue atomic RETURNING, reorder 2 pha, recover stale), permission_broker.py (ask_scopes, default-deny no-approver), failure_recovery.py (retry→fallback→report), errors.py, schema.py (shared DDL), `__init__.py` (build_goal_modules factory)
- Kernel additive: EventType +6 (`goal.*`, `queue.updated`, `recovery.*`), `PolicyDecision.ask_scopes` (5 nhánh), `GoalsSettings` + config.yaml
- Critique ×2: 31 vấn đề resolved (C1-01..C1-16, C2-01..C2-15) — gồm 3 Critical, 6 Major
- **490 tests pass (baseline 428 + 62), coverage 95.96%, 12/12 AC**

**TASK-016 — Architecture Hardening** ✅ (2026-08-13)
- 10 Architecture Invariants (INV-001..010) chốt vào `docs/architecture.md` §7 + ADR-0004 + PLAN.md (link + index + Architecture Health→M4)
- Control/Execution Plane tách bạch; dependency 1 chiều Agent→Capability→Tool→Infra; Evaluation = post-execution observer; KB vs KG; Context vs Memory; Scheduler/Resource/Execution 3 vai; System Knowledge = System Brain
- **12 architecture tests** (`tests/test_architecture.py` + `_arch_scan.py`, AST pure scan — không import runtime): INV-003/004/005(A+B allow-list)/006/007(hard call-site)/009(4 business)/010 + helper; INV-001/002 skip (chờ agents//tools/)
- Critique ×2: 23 vấn đề resolved (1 P1 + 5 P2...); Review: CHANGES REQUESTED → R1 fix (SRC_ROOT parents[1])
- **502 passed + 2 skipped, coverage 95.96%, 10/10 AC**

**TASK-013 — M2-P3c: Assistants (Worker Plane)** ✅ (2026-08-13)
- `agents/` package mới (tuân INV-001/002 — chỉ import models.base/errors + pydantic + stdlib, mọi service qua callable injectable): base.py (template method handle + event sink best-effort), general.py, coder.py (7 steps + Self-Fix loop, repr-escape, exec ns), doctor.py (6 bước + Safety Layer 4 bất biến: disclaimer ok-only, cấm kê đơn trước (d), high→emergency, (d) gate không danger; KB-miss cautious), system_doctor.py (probe + score + FIX_HINTS), registry.py (RLock, resolve_by_intent qua selector)
- **test_architecture.py**: skip condition INV-002 sửa (chỉ agents/); `test_inv_agents_import_allowlist` (2 set, exclude agents*)
- Critique ×2: 25 vấn đề resolved (1 Critical + 5 Major...); Review: CHANGES REQUESTED → R1.1 (extractor union default KB) + R1.2 (allow-list exclude intra)
- **549 passed + 0 skipped, coverage 96.03%, 12/12 AC — INV-001/002 BẬT và PASS**

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-13 | TASK-013 | T4 | 549 pass + 0 skip (INV-001/002 bật), coverage 96.03%, 12/12 AC; evaluation.md; commit` → done
2. `2026-08-13 | TASK-013 | T3 | 47 test mới; fix 5 bài học (state merge phẳng+key, MockModel responses, extractor substring, __future__ scanner, danger-only need_more_info)` → done
3. `2026-08-13 | TASK-013 | T1-T2 | agents/ package (base/general/coder/doctor/system_doctor/registry) + test_architecture.py (skip INV-002 chỉ agents/ + allow-list 2 set exclude agents*)` → done
