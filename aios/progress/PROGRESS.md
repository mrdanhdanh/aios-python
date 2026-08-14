# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `done` ✅ (review độc lập PASS) |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `done` ✅ (669 tests, 95.51%) |
| M3 | Desktop Edition (P5–P6: dashboard, VS Code extension) | `done` ✅ (689 pytest + 19 vitest) |
| M4 | Platform Edition (P7–P8: upgrade pipeline, observability) | `done` ✅ (809 tests, 94.92%) |
| M5 | Core Intelligence (P9–P10: memory/context/model/planning/graph/scheduler) | `done` ✅ (1086 tests, 95.22%) |

## Hạ tầng bổ sung (bypass)

| Mục | Nội dung | Trạng thái | Ghi chú |
|-----|----------|------------|---------|
| Secret scan | GitHub Actions Gitleaks — quét secret trên push/PR master + manual trigger | `done` | `.github/workflows/secret-scan.yml` (2026-08-14) |
| Remote | Chuyển origin → repo GitHub mới `mrdanhdanh/aios-python` (PUBLIC) | `done` | commit e42bae4 (2026-08-14) |


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
| TASK-014 | M2-P4 — Tools 6 loại (Python/Docker/REST/MCP/Shell/Git) + Tool Registry + capability binding | M2 | `done` ✅ | AIOS Orchestrator |
| TASK-015 | M2-P4 — Skills lifecycle 10 trạng thái + Skill Manager (zip/git/pip) + Sandbox Pool | M2 | `done` ✅ | AIOS Orchestrator |

## M2 — Developer Edition (in-progress)

**TASK-012 — M2-P3b: Goal Manager + Task Queue + Permission Broker + Failure Recovery** ✅ (2026-08-13)- `orchestrator/goals/` package mới: goal.py (GoalManager, state machine, cascade cancel), task_queue.py (dequeue atomic RETURNING, reorder 2 pha, recover stale), permission_broker.py (ask_scopes, default-deny no-approver), failure_recovery.py (retry→fallback→report), errors.py, schema.py (shared DDL), `__init__.py` (build_goal_modules factory)
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

**TASK-014 — M2-P4: Tools (Execution Plane)** ✅ (2026-08-13)
- `tools/` package mới (allow-list cứng — chỉ metadata + pydantic + stdlib + urllib.parse; KHÔNG kernel/capabilities/agents/orchestrator): base.py (template run 1-6: tool_id → gate fail-closed [None/False/raise] → started → _run(input, context) → finished → output), 6 stub tool (Python ast.parse no-exec / Docker mock / REST validate / MCP registry giả / Shell no-exec scope bắt buộc / Git mock), registry.py (RLock, bind_capabilities qua callable — idempotent)
- **test_architecture.py**: `test_inv_tools_import_allowlist` (2 set + urllib AST module-con check R3)
- Critique ×2: 27 vấn đề resolved (1 P1 + 7 P2...); Review: APPROVED + 3 lưu ý (duration_s error path, gate-raise test, urllib AST)
- **622 passed + 0 skipped, coverage 96.15%, 14/14 AC**

**TASK-015 — M2-P4: Skills + Sandbox Pool** ✅ (2026-08-13)
- `skills/` package: base.py (10 SkillState + bảng transitions T1-T10 — C1-01, manifest validate bằng aios_core.semver), manager.py (lifecycle đầy đủ + optimistic concurrency WHERE state + dependent check rollback/remove + history stack), registry.py (read-through), sources.py (Zip/Git/Pip stub no-syscall), schema.py (CHECK sinh từ hằng số)
- `sandbox/` package: pool.py (SandboxPool — acquire warm reuse + normalize language, execute no-exec, release, evict_idle(now=...), health; RLock; không thread nền)
- **test_architecture.py**: `test_inv_skills_import_allowlist` (metadata + semver) + `test_inv_sandbox_import_allowlist` (empty set)
- Critique ×2: 27 vấn đề resolved (1 Critical + 4 Major...); Review: CHANGES REQUESTED → R1 (dependent check spec body) + R2 (optimistic spec body) + R3 (semver 6 chỗ)
- **669 passed + 0 skipped, coverage 95.51%, 18/18 AC — M2-P4 HOÀN TẤT**

## M3 — Desktop Edition ✅ (2026-08-13)

**TASK-017 — M3-P5: FastAPI REST + WebSocket API** ✅ (commit 16c998f)
- `api/` package: app.py (create_app), wiring.py (build_registries — MockModel registered đầu, catalog populated), serve.py (uvicorn), routers/ 9 router (health score = 1 - weight/2, events REST + WS loop.call_soon_threadsafe, catalog, goals, skills, tools, memory, prompts, chat ChatRequest → orchestrator → assistant resolve theo intent)
- CLI `aiagent serve --host --port` (lazy import)
- **689 passed + 0 skipped, coverage 95.10%** (14 API test + 6 chat/serve test mới)

**TASK-018 — M3-P5: Dashboard SPA (React + Vite + TS)** ✅ (commit 33b6b05)
- `dashboard/`: vite proxy /api → 127.0.0.1:8000 (ws: true), 10 tabs (Chat/Workflow/Events/Tools/Memory/Artifacts/Skills/Models/Prompts/Health), api.ts 3-envelope, ws.ts reconnect 3s + MockWebSocket stub
- **vitest 12/12 pass + vite build OK**

**TASK-019 — M3-P6: VS Code Extension (TS, 9 lệnh)** ✅
- `extension/`: package.json (9 commands + activationEvents + config aios.serverUrl), client.ts (AiosClient.callChat — 3 envelope + 422 array + trim slash), context.ts (editorText qua document.getText — Selection thật không có .text; gitDiff(cwd); buildPrompt 8 template), extension.ts (activate với vscode injected, 9 commands, INTENTS map đúng bảng §4, guard selection warning, editor.edit replace cho fix/generate_test)
- Critic ×2: critique-1 13 vấn đề (1 P1 — Selection.text, 7 P2, 5 P3) + critique-2 3 vấn đề — resolved hết; Review: APPROVED có điều kiện → 3 R2 (gitDiff cwd, intent test 9 case, editor.edit test) + 7 R3 resolved
- **vitest 19/19 pass + tsc clean + build emit out/extension.js — M3 HOÀN TẤT**
## M4 — Platform Edition (in-progress)

### P7 — TASK-020: Upgrade Pipeline ✅ (2026-08-13)
- `upgrade/` package: dependency.py (ComponentSpec/Dependency frozen, DependencyResolver — DFS post-order, sort (name,version), missing/cycle/conflict, deterministic), backup.py (BackupStore SQLite — backup/restore/list, persist cross-instance), migrator.py (Migrator Protocol + DictMigrator + SkillMigrator wrap SkillManager — payload = model_dump JSON), pipeline.py (6 bước: read current → skip check → compatibility → dependencies → backup → migrate → health → complete; dry-run 0→2; rollback best-effort: migrator.rollback ưu tiên, fallback write_current backup; 9 UPGRADE_* events), errors.py (UpgradeError)
- `kernel/events.py`: +8 EventType members (UPGRADE_STARTED..ROLLED_BACK, value "upgrade.<snake>")
- `workflow/cli.py`: subcommand `aiagent upgrade <kind> <id> --version X [--dry-run]` — v1 chỉ wire skill (SkillMigrator + SkillManager từ settings); exit codes chuẩn
- `test_architecture.py`: `test_inv_upgrade_import_allowlist` (internal: contracts/semver/kernel.events/skills.errors; hook-injected — không import skills.manager)
- Critic ×2: 31 vấn đề (9 P1) resolved — **quyết định: chỉ migrate ROOT, dependency chỉ resolve**; Review: CHANGES REQUESTED → 1 R1 + 3 R2 + 6 R3 resolved
- **730 passed + 0 skipped, coverage 95.00%, 10/10 AC — P7 HOÀN TẤT**

### P8 — TASK-021: Observability & Diagnostics ✅ (2026-08-13)
- `observability/` package: metrics.py (MetricsService — subscribe EventBus, category workflow/tool, duration từ Event.timestamp, UPDATE row mới nhất chưa finish, orphan NULL, tool_failures), prompt_history.py (PromptHistory — SQLite sort_keys), profiler.py (Profiler — fake clock, double-start raise), doctor.py (HealthDoctor — worst-wins + diagnostics hooks, tránh trùng agents.SystemDoctor), arch_scan.py (move từ tests/ — 1 engine, SRC_ROOT parents[2]), arch_health.py (ArchitectureHealth — scan(package_dir), layer/contract/policy 3 check), evaluation.py (EvaluationStore — cache STARTED duration, COMPLETED→success / FAILED+CANCELLED→failed, evaluate() feedback)
- `kernel/services/execution.py`: +5 emit (WORKFLOW_FAILED 6 nhánh _run, WORKFLOW_CANCELLED flag + cancel giữa node; resume ×2 + cancel trước execute không emit)
- `api/routers/observability.py`: 5 GET (metrics/prompt-history/doctor/arch-health/evaluations) + POST feedback (404/422); wiring regs["observability"]; config ObservabilitySettings
- CLI: `aiagent metrics` / `doctor` (giữ key kernel) / `arch-health`
- Critic ×2: 36 vấn đề (9 P1) resolved; Review: APPROVED có điều kiện → 3 amendment (duration cache, emit scope, doctor key) + R2-2 + R3×7 resolved
- **779 passed + 0 skipped, coverage 95.11%, 10/10 AC — P8 Phần 1 HOÀN TẤT**

### P8 — TASK-022: Orchestrator v2 ✅ (2026-08-13)
- `orchestrator/advisor.py` — ImprovementAdvisor: 5 rules deterministic (quality thấp, fail nhiều, tool failures, prompt chưa đánh giá, workflow chậm — duration_by_workflow mới) + dedup/sort; suggestion KHÔNG tự áp dụng
- `orchestrator/supervisor.py` — ExecutionSupervisor: track running từ bus (clock float monotonic), stuck detect, FAILED+CANCELLED → recent_failed, queue hook
- `orchestrator/evaluation_collector.py` — EvaluationCollector: evaluator layer trên EvaluationStore, KeyError/error swallow, collect_all aggregate; trigger qua bus wiring
- `orchestrator/goals/reporting.py` — GoalReporter: 5 status, avg_progress, failed=FAILED+CANCELLED, report_goal detail (qua public API — không sửa GoalManager)
- API `/api/v1/orchestrator-v2/` (4 GET); wiring regs["orchestrator_v2"] + TaskQueue wire; CLI `aiagent advisor`/`supervisor`; metrics.py +duration_by_workflow
- Critic ×2: 24 vấn đề (7 P1) resolved; Review: APPROVED có điều kiện → 1 R2 + 3 R3 resolved (+1 bypass fix `_metrics` suffix)
- **809 passed + 0 skipped, coverage 94.92%, 8/8 AC — P8 HOÀN TẤT → M4 HOÀN TẤT**

## M5 — Core Intelligence (in-progress) — 2026-08-14

> PLAN.md §M5: nâng cấp "bộ não vận hành" — không thêm agent/UI. Trả lời: Memory (nhớ gì?), Context (đưa gì vào?), Model Router (dùng model nào?), Planning (làm bước nào?), Execution Graph (phụ thuộc thế nào?), Scheduler (chạy khi nào/song song?).
> Thứ tự: Phase 1 (023→024) → Phase 2 (025) → Phase 3 (026→027→028). Mỗi task qua hard gate đầy đủ (spec → critique ×2 → tasks → review → implement → test → evaluate).
> DoD M5: Memory không truy cập trực tiếp từ Agent; Context có budget + priority; Model routing theo policy + fallback; Planner tạo task graph; Graph hỗ trợ dependency + parallel; Scheduler không sở hữu Resource/Execution; INV-011..016 enforced bằng AST tests; observability đầy đủ.

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-023 | Memory Coordinator — Retrieve → Filter → Rank → Deduplicate → Compress → Prioritize → Inject; contract MemoryQuery/Candidate/Score/Selection/Context; budget; INV-011 | `done` ✅ | 855 pass, coverage 95.16%, 10/10 AC (2026-08-14) |
| TASK-024 | Context Optimizer — Deduplicate → Compress → Prioritize → Token Budget → Final Context; priority P0–P6; compression 3 cấp; INV-012 | `done` ✅ | 896 pass, coverage 95.21%, 11/11 AC (2026-08-14) |
| TASK-025 | Model Router — ModelSelector/RoutingPolicy/CostEstimator/AvailabilityChecker/FallbackResolver/ModelHealth; metadata model; policy yaml; fallback theo Policy; INV-013 | `done` ✅ | 949 pass, coverage 95.13%, 11/11 AC (2026-08-14) |
| TASK-026 | Planning Engine — Goal Analyzer → Task Decomposer → Dependency Analyzer → Capability Resolver → Risk Analyzer → Execution Planner → Execution Graph; plan validation 8 hạng mục; INV-014 | `done` ✅ | 1003 pass, coverage 95.00%, 11/11 AC (2026-08-15) |
| TASK-027 | Execution Graph — ExecutionGraph/GraphNode/GraphEdge/Dependency/Condition/JoinPolicy/FailurePolicy; graph state 8 trạng thái; INV-015 | `done` ✅ | 1055 pass, coverage 95.09%, 13/13 AC (2026-08-15) |
| TASK-028 | Parallel Scheduler — Graph Scheduler → Resource → Execution → State; không sở hữu Resource/Execution; INV-016 | `done` ✅ | 1086 pass, coverage 95.22%, 12/12 AC (2026-08-15) — **M5 HOÀN TẤT** |

## M6 — AIOS Harness (in-progress) — 2026-08-15

> PLAN.md §M6: subsystem `harness/` giúp AIOS tự kiểm thử/xác minh/quan sát/cải tiến (H1-H5). Không sửa Runtime/Orchestrator — chỉ gọi qua API. INV-017..021.

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-029 | H1 Harness Kernel — contracts chung + lifecycle 8-state + registry + runner + evidence (INV-018); INV-017 isolation | `done` ✅ | 1124 pass, coverage 95.20%, 10/10 AC (2026-08-15) |
| TASK-030 | H2 Execution Verification — Preconditions/Postconditions/Verdict + Evidence Package + Replay; INV-019 | `done` ✅ | 1210 pass, coverage 95.26%, 10/10 AC (2026-08-15) |
| TASK-031 | H3 Test & Simulation — Scenario + Simulation Mode; không side effect | `done` ✅ | 1299 pass, coverage 95.26%, 12/12 AC (2026-08-15) |
| TASK-032 | H4 Evaluation Harness — Evaluation Model + Suite + Trajectory; INV-020 | `done` ✅ | 1387 pass, coverage 95.27%, 12/12 AC (2026-08-15) |
| TASK-033 | H4 Benchmark + Regression Gate — INV-021 | `todo` | sau 032 |
| TASK-034 | H5 Doctor & Readiness — Doctor architecture + Readiness Score | `todo` | |
| INV-011..016 | Enforcement tests (AST) trong `tests/test_architecture.py` + observability metrics M5 | `todo` | tích hợp trong các task |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-13 | TASK-022 | T4-T11 | Orchestrator v2: advisor/supervisor/collector/goal_reporter + API 4 GET + CLI; 809 pass, coverage 94.92%; M4 DONE` → done
2. `2026-08-13 | TASK-022 | [bypass] | fix _metrics() đọc sai db suffix (R2-1 reviewer phát hiện)` → done
3. `2026-08-13 | TASK-021 | T4-T15 | observability/: metrics/prompt_history/profiler/doctor/arch_health/evaluation + execution emit FAILED/CANCELLED + API/CLI; 779 pass, 95.11%` → done

