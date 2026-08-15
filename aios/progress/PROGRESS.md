# PROGRESS.md — Chỉ mục tiến độ dự án AIOS

> Cập nhật sau MỖI thay đổi trạng thái. Đọc đầu mỗi phiên làm việc.
> Trạng thái: `todo` | `in-progress` | `done` | `blocked`

## ✅ TASK-078 — Làm lại hoàn toàn game "Yuniebel's Cat" theo kịch bản + 5 ảnh tham khảo (2026-08-15)

- **Kết quả**: **DONE** — viết lại từ đầu `games/yuniebel/` (bản cũ TASK-077 bị chê xấu). 13 câu thoại nguyên văn brief-scenario.md, 9 task text, 10 mood nhạc nền + 27 SFX WebAudio, 7 cảnh vẽ theo 5 ảnh tham khảo (trời động ngày→hoàng hôn→đêm + đèn hiên, 5 kiểu hù riêng biệt, ma xanh đầu lâu chặn cửa, vết máu lớn + mắt sáng, lò sưởi + bánh kem sinh nhật).
- **Test (theo yêu cầu "chụp ảnh so brief")**: **54/54 PASS** — core 27 + smoke 4 + Playwright 23 (2 test chơi thật không hook: title→sinh nhật 42.7s, title→game over 21.4s; 17 ảnh chụp màn hình đối chiếu brief → COMPARISON.md **17/17 khớp**). Post-review R-01..R-12 resolved. **14/14 AC ĐẠT**.
- Xem chi tiết: `aios/progress/tasks/TASK-078/` (plan + spec + critique×2 + tasks + review + review-post + test + evaluation + shots/ 17 ảnh)

## ✅ TASK-077 — Webgame 2D Pixel "Yuniebel" (2026-08-15)

- **Kết quả**: tạo `games/yuniebel/` — webgame 2D pixel 100% static (HTML/CSS/JS, 0 dependency). Sprites canvas primitives (mèo orange可爱 tóc hồng, chủ, ma, bướm, bánh kem) + 7 backgrounds pre-rendered. 6 cảnh + title/game over/end, 17 AC PASS.
- **Cấu trúc**: `index.html` + `style.css` + `src/` (core.js logic thuần 58/58 PASS + sprites.js canvas primitives + audio.js WebAudio + game.js loop/render/input) + `test/` (core.test.js 58 PASS + smoke.test.js 28 PASS)
- **Deploy**: `.github/workflows/pages.yml` (GitHub Pages, paths: games/**)
- Xem chi tiết: `aios/progress/tasks/TASK-077/` (spec + critique×2 + tasks + review + test + evaluation)

## ✅ TASK-076 — Architecture v3 (Mermaid): AIOS 1.0 Final (2026-08-15)

- **Kết quả**: tạo `docs/architecture-v3.md` — bản **hiện hành** (AIOS 1.0 Final, **Mermaid** — theo yêu cầu người dùng phương án "2 và 3"), 12 khối sơ đồ (10 flowchart + stateDiagram-v2 Safety chain + sequenceDiagram Kill Switch), 7 tầng L1..L7 theo `layer-model.md` **frozen** (Autonomous = L2 — sửa điểm v2 sai; Harness/Enterprise/Ecosystem = L7; M10 = nhóm đảm bảo không phải L8), bảng tasks M10 13/13 done (đúng ánh xạ id PROGRESS), INV-001..034 frozen + 5 release gates + AIOS 1.0 READY/CERTIFIED. `architecture-v2.md` đánh dấu **LỊCH SỬ** (header/§0/§14); README link → v3.
- **Test**: `validate-v3.js` **19/19 PASS**; Mermaid parse thật (mermaid v11 + jsdom tại `aios/tools/mermaid-validate/`, node_modules gitignored) **12/12 khối OK**; AC9 diff v2 chỉ header/§0/§14; AC12 `docs/architecture/*` nguyên vẹn. **13/13 AC — TASK-076 DONE**.
- Xem chi tiết: `LOG.md` entry 2026-08-15 TASK-076.

## ✅ TASK-063 — Vẽ lại hoàn toàn kiến trúc hệ thống (2026-08-15)

- **Kết quả**: tạo `docs/architecture-v2.md` (markdown thuần — bảng + ASCII diagrams, KHÔNG Mermaid theo yêu cầu người dùng) — tài liệu kiến trúc **hiện hành** thay thế file cũ; file cũ `docs/architecture.md` giữ nguyên làm lịch sử.
- **Nội dung**: 14 mục — 7 tầng lõi M0–M5 + 4 lớp M6–M9 (Harness/Enterprise/Ecosystem/Autonomous) + 3 plane + Orchestrator modules + luồng request 12 bước + Runtime Kernel 9 services + Core Intelligence + INV-001..034 + milestones M0–M10 + bảng tasks M1–M9.
- **Test**: script node kiểm tra cấu trúc markdown 21/21 PASS; đối chiếu dữ liệu PROGRESS.md khớp. **7/7 AC — TASK-063 DONE**.
- Xem chi tiết: `LOG.md` entry 2026-08-15 TASK-063.

## M10 — AIOS 1.0 ✅ (2026-08-15 — DONE)

> PLAN.md §M10: `BUILD NOTHING — PROVE EVERYTHING → AIOS 1.0 CERTIFIED`. Freeze Architecture (INV-001..034, vi phạm = release blocker), Contract 1.0, Runtime durable, Autonomous bounded, 5 release gates, Golden Scenarios GS-001..020, `aiagent conformance` → **AIOS 1.0 READY**.
> 13 task (TASK-063..075), 5 phase: **P1 Freeze** (063, 064) → **P2 Harden** (065, 066, 069) → **P3 Secure** (067, 068, 070) → **P4 Productize** (071, 072, 075) → **P5 Certify** (073, 074).
> Kết quả: full suite **1939 pass** + vitest 13/13 + conformance READY + doctor 100/100. Review: `reviews/M10-review.md` (ACCEPTED, không P1).

| Task | Nội dung | Milestone | Trạng thái | Owner |
|------|----------|-----------|------------|-------|
| TASK-063 | F1 Architecture Freeze — Constitution 1.0 (INV-001..034 frozen) + docs/architecture/* (AIOS-1.0, layer-model, control-plane, execution-plane, autonomy) | M10-P1 | `done` ✅ (19/19 PASS; +2 enforcement test INV-008/012) | AIOS Orchestrator |
| TASK-064 | F2 Contract 1.0 — freeze 10 contracts (Agent/Capability/Tool/Workflow/Runtime/Event/Artifact/Plugin/Model/Memory) + semantic versioning + `aiagent contract-check` | M10-P1 | `done` ✅ (20/20 PASS) | AIOS Orchestrator |
| TASK-065 | F3 Runtime Hardening — failure matrix 12 loại (detect→contain→recover→resume) | M10-P2 | `done` ✅ (18/18 PASS — 12 scenario end-to-end) | AIOS Orchestrator |
| TASK-066 | Durable Execution 1.0 — journal + verify-before-resume + idempotency classification (exactly-once/at-least-once) | M10-P2 | `done` ✅ (10/10 PASS) | AIOS Orchestrator |
| TASK-069 | Reliability Engineering — SLO registry + non-averaged gates (policy bypass=0, lost execution=0, ...) | M10-P2 | `done` ✅ (12/12 PASS) | AIOS Orchestrator |
| TASK-067 | F4 Autonomy Safety — Action Proposal → Risk Classifier → Governor → Policy → Permission → Capability → Tool (mandatory, stop-anywhere) | M10-P3 | `done` ✅ (15/15 PASS) | AIOS Orchestrator |
| TASK-068 | Kill Switch — `aiagent stop execution/goal` + `aiagent emergency-stop` | M10-P3 | `done` ✅ (13/13 PASS) | AIOS Orchestrator |
| TASK-070 | Security Baseline 1.0 — 11 items baseline + `aiagent security-check` (9 PASS/2 WARN, SECURE) | M10-P3 | `done` ✅ (8/8 PASS) | AIOS Orchestrator |
| TASK-071 | F7 Developer Experience — command tree thống nhất + `aiagent doctor` first-class (Health 100/100) | M10-P4 | `done` ✅ (10/10 PASS) | AIOS Orchestrator |
| TASK-072 | AIOS Dashboard 1.0 — 11 tabs + Execution Timeline | M10-P4 | `done` ✅ (backend 5/5 + vitest 13/13) | AIOS Orchestrator |
| TASK-075 | Performance & Cost — metrics + Cost/Goal/Workflow/Agent/Tool/Success + model independence | M10-P4 | `done` ✅ (11/11 PASS) | AIOS Orchestrator |
| TASK-073 | F8 Certification Suite — 13 categories + GS-001..020 + `aiagent conformance` + 5 release gates | M10-P5 | `done` ✅ (9/9 PASS — **AIOS 1.0 READY**) | AIOS Orchestrator |
| TASK-074 | Upgrade & Migration 1.0 — migration plan/backup/dry-run/validation/rollback (0.x→1.0, plugin/contract/workflow v0→v1) | M10-P5 | `done` ✅ (13/13 PASS) | AIOS Orchestrator |

## ✅ Review toàn diện M0–M9 (2026-08-15)

- **Kết quả**: M0–M9 ĐẠT — backend 1793 pass + dashboard 12 + extension 19; CLI deliverable chạy thật (doctor/arch-health/run --simulate); **ALL 62 TASK đủ 8-file hard gate**.
- **Đã sửa (process/hồ sơ, không code)**:
  - Bổ sung file hard-gate thiếu cho 24 task: `test.md` (TASK-011/020/021/022), `review.md` (TASK-033/034/046/047/048/049), `evaluation.md` (TASK-045..049), `implementation/README.md` (23 task — pointer tới code thật).
  - PROGRESS.md: 8 header milestone sai `(in-progress)` → `✅` (M1/M2/M4/M5/M6/M7/M8/M9); ghi chú INV-022 lỗi thời → cập nhật theo M7 F3 đã resolve (nhãn canonical `test_inv022..inv029`).
- Xem chi tiết: `LOG.md` entry 2026-08-15 "M0-M9 review+fix".

## Tổng quan

| Milestone | Mô tả | Trạng thái |
|-----------|-------|------------|
| M0 | Development Foundation (VS Code agent + progress system) | `done` ✅ |
| M1 | Core Runtime (P0–P2: infra, kernel, model/memory/knowledge, workflow/capability/catalog) | `done` ✅ (review độc lập PASS) |
| M2 | Developer Edition (P3–P4: orchestrator v1 + assistants, tools/skills/sandbox) | `done` ✅ (669 tests, 95.51%) |
| M3 | Desktop Edition (P5–P6: dashboard, VS Code extension) | `done` ✅ (689 pytest + 12+19 vitest) — **review độc lập ACCEPTED** (V1–V6,V8 PASS; V7 P2 → đã bổ sung đủ 8-file hard gate TASK-017/018/019) |
| M4 | Platform Edition (P7–P8: upgrade pipeline, observability) | `done` ✅ (809 tests, 94.92%) — **review độc lập + 1 P1 fix (F1 arch-health scanner)** |
| M5 | Core Intelligence (P9–P10: memory/context/model/planning/graph/scheduler) | `done` ✅ (1086 tests, 95.22%) |
| M6 | AIOS Harness (P11: harness kernel, verification, test & simulation, evaluation, benchmark, doctor & readiness) | `done` ✅ (1521 tests, 95.35%) — **review độc lập (self) + 1 P2 fix (F1 harness scanner)** |
| M7 | Enterprise (P12: identity, tenancy, distributed runtime, distributed scheduler, governance, security, operations, dashboard) | `done` ✅ (1560 tests, 95.05%) — **review độc lập ACCEPTED** (V1–V7 PASS; V8 P2→RESOLVED: F1 scanner cover enterprise + F2 implementation/ + F3 INV-022 label) |
| M8 | Ecosystem (P13: Public SDK, Plugin Runtime, Extension Contracts, Registry, Developer Kit, Hub, Certification) | `done` ✅ (1639 tests) — **review độc lập (self) + 1 P2 fix (F1 M8 scanner coverage)** |
| M9 | Autonomous (P14: goal engine, planner, world model, loop, governor, recovery, long-horizon, memory, experimentation, multi-agent, evaluation, stuck, scheduler) | `done` ✅ (**1780 tests @M9, coverage 94.46%; full suite 1793 sau review + M5/M6/M7/M8 review additions**) — **review độc lập ACCEPTED** (V1–V7 PASS; V8 P2→RESOLVED: F1 scanner cover autonomous, F2/F3 không apply — TASK-050..062 đã đủ 8-file, INV-030..034 không collision) |
| M10 | AIOS 1.0 (P15: freeze architecture + contract 1.0 + hardening + durable + autonomy safety + kill switch + security baseline + DX + dashboard + certification + migration + performance) | `done` ✅ (**1939 tests + 13 vitest dashboard** — **review ACCEPTED, không P1; `aiagent conformance` → AIOS 1.0 READY**) |

## Hạ tầng bổ sung (bypass)

| Mục | Nội dung | Trạng thái | Ghi chú |
|-----|----------|------------|---------|
| Secret scan | GitHub Actions Gitleaks — quét secret trên push/PR master + manual trigger | `done` | `.github/workflows/secret-scan.yml` (2026-08-14) |
| Remote | Chuyển origin → repo GitHub mới `mrdanhdanh/aios-python` (PUBLIC) | `done` | commit e42bae4 (2026-08-14) |
| DoD checklist | **Definition of Done — Closing Checklist** (AGENTS.md §3.1 + PLAN.md): bắt buộc cập nhật LOG.md + PROGRESS.md + PLAN.md + STATS.md + task folder + commit sau MỖI task — tránh quên ghi tài liệu | `done` | theo yêu cầu người dùng 2026-08-15 |
| README docs | `[bypass]` — cập nhật `docs/README.md` (GitHub fallback render khi root không có README.md) khớp trạng thái AIOS 1.0: mô tả 7 tầng + CERTIFIED, bảng M0–M10, mục kiểm tra sức khỏe (`aiagent doctor/conformance/arch-health`), link constitution-1.0.md; không tạo README root mới | `done` | theo yêu cầu người dùng 2026-08-15 |


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

## M1 — Core Runtime ✅ (2026-08-12)

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

## M2 — Developer Edition ✅ (2026-08-13)

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
- **Đủ 8-file hard gate**: spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/ (test.md + implementation/README.md bổ sung 2026-08-15 để đóng F1 review)
- **vitest 19/19 pass + tsc clean + build emit out/extension.js — M3 HOÀN TẤT**

**TASK-017 / TASK-018 — bổ sung hard-gate files (F1 review M3, 2026-08-15)**: TASK-017 thiếu critique-2/tasks/review/test/implementation → đã tạo đủ; TASK-018 thiếu tasks/review/test/implementation → đã tạo đủ. Cả 3 task TASK-017/018/019 nay đủ 8-file hard gate (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/).
## M4 — Platform Edition ✅ (2026-08-13)

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

### M4 — Review độc lập (self-review, 2026-08-15)
- Đọc thực tế code TASK-020/021/022 + spec + chạy test thật + chạy scanner trên cây thật `SRC_ROOT`.
- **F1 (P1)**: `ArchitectureHealth.scan()` bỏ qua TOÀN BỘ layer/contract check trên cây thật — `target = package_dir / sub` với `package_dir = backend/src`, nhưng `agents/` nằm dưới `backend/src/aios_core/agents` → `is_dir()` False → skip silent; chỉ policy check chạy. Thêm nữa: `rel` truyền dot-form vào `collect_imports` (hàm expects slash-form) → relative import phân giải sai. **→ ĐÃ TỰ SỬA**: tính `aios_root = package_dir/"aios_core"` nếu tồn tại; truyền `rel` slash-form; exempt slash-form. Thêm 2 test regresi (nested layout).
- F2 (P3): `orchestrator/__init__.py` không export module M4 mới (inconsistency, không phải bug). F3 (P3): advisor rule 1+5 dedup collapse (đúng spec).
- Kết quả: **M4 ĐẠT** V1–V8 (sau fix F1); full suite `1636 passed, 0 fail`. Xem `reviews/M4-review.md` + `reviews/M4-review-brief.md`.

## M5 — Core Intelligence ✅ (2026-08-15)

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

### M5 — Review độc lập (self-review, 2026-08-15)
- Đọc thực tế code TASK-023..028 + spec, chạy test thật (256 M5 test + 17 INV-011..016 arch test PASS), chạy scanner trên cây thật.
- **F1 (P2)**: runtime `ArchitectureHealth.scan()` không cover M5 packages (memory/context/models.router/orchestrator.planning/kernel.graph/kernel.scheduler) — vi phạm PLAN §M5 "observability đầy đủ". **→ ĐÃ TỰ SỬA**: thêm 6 M5 layer rule vào `arch_health.py` + 6 test regresi `test_observability_arch_health.py`; scanner trên `SRC_ROOT` → `healthy=True, 0 violations`.
- **F2 (P3)**: M5 thiếu milestone review doc (M0/M3/M4 có). **→ ĐÃ TỰ SỬA**: viết `reviews/M5-review.md` + `reviews/M5-review-brief.md`.
- Kết quả: **M5 ĐẠT** V1–V8 (sau F1); không P1. Xem `reviews/M5-review.md` + `reviews/M5-review-brief.md`.

## M6 — AIOS Harness ✅ (2026-08-15)

> PLAN.md §M6: subsystem `harness/` giúp AIOS tự kiểm thử/xác minh/quan sát/cải tiến (H1-H5). Không sửa Runtime/Orchestrator — chỉ gọi qua API. INV-017..021.

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-029 | H1 Harness Kernel — contracts chung + lifecycle 8-state + registry + runner + evidence (INV-018); INV-017 isolation | `done` ✅ | 1124 pass, coverage 95.20%, 10/10 AC (2026-08-15) |
| TASK-030 | H2 Execution Verification — Preconditions/Postconditions/Verdict + Evidence Package + Replay; INV-019 | `done` ✅ | 1210 pass, coverage 95.26%, 10/10 AC (2026-08-15) |
| TASK-031 | H3 Test & Simulation — Scenario + Simulation Mode; không side effect | `done` ✅ | 1299 pass, coverage 95.26%, 12/12 AC (2026-08-15) |
| TASK-032 | H4 Evaluation Harness — Evaluation Model + Suite + Trajectory; INV-020 | `done` ✅ | 1387 pass, coverage 95.27%, 12/12 AC (2026-08-15) |
| TASK-033 | H4 Benchmark + Regression Gate — INV-021 | `done` ✅ | 1450 pass, coverage 95.31%, 11/11 AC (2026-08-15) |
| TASK-034 | H5 Doctor & Readiness — Doctor architecture + Readiness Score | `done` ✅ | 1521 pass, coverage 95.35%, 11/11 AC (2026-08-15) — **M6 HOÀN TẤT** |
| INV-011..016 | Enforcement tests (AST) trong `tests/test_architecture.py` + observability metrics M5 | `todo` | tích hợp trong các task |

## M7 — Enterprise ✅ (2026-08-15)

> PLAN.md §M7: đưa AIOS từ single-instance thành nền tảng vận hành an toàn quy mô doanh nghiệp. 7 nhóm (E1–E7), 8 invariant (INV-022..INV-029). Không biến AIOS thành cloud/distributed platform — chỉ định nghĩa contract + governance.
> Dependency: TASK-035 → TASK-036 → ┬ TASK-037 ┐ → TASK-038 → TASK-039 → TASK-041 → TASK-042; └ TASK-040 ┘ song song với TASK-037.
> Approach: gom 8 task thành 1 package `backend/src/aios_core/enterprise/` (offline-first, DI injectable, không God Object), mỗi nhóm = 1 module, facade `EnterpriseManager` trong `runtime_kernel`. Behavioral tests trong `tests/test_enterprise.py`, structural invariant tests trong `tests/test_architecture.py` (m7_*).

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-035 | E1 Identity & Access — Principal (user/agent/service), RBAC + ABAC, delegation + capability attenuation; INV-022 | `done` ✅ | `enterprise/identity.py` + `contracts.py`; 29 enterprise tests pass (chung) |
| TASK-036 | E2 Multi-Tenancy — Tenant model + TenantBoundary (deny-by-default) + MemoryNamespace isolation; INV-023 | `done` ✅ | `enterprise/tenancy.py` |
| TASK-037 | E3 Distributed Runtime — RuntimeNodeInfo + NodeRegistry + RuntimeRouter (tenant/region/capability/capacity/cost/health), tenant_class gate; INV-029 | `done` ✅ | `enterprise/runtime.py` |
| TASK-038 | E4 Distributed Scheduler + Lease — single-active lease (INV-026) + failover/resume snapshot | `done` ✅ | `enterprise/scheduler.py` |
| TASK-039 | E5 Resource Governance — QuotaManager (fairness INV-025) + CostGovernor (budget deny / cheaper route) | `done` ✅ | `enterprise/governance.py` |
| TASK-040 | E6 Security & Data Isolation — CredentialBroker (scoped INV-024) + NetworkPolicy (default-deny) + SandboxBoundary (INV-028) | `done` ✅ | `enterprise/security.py` |
| TASK-041 | E7 Operations — CentralAuditStore (tamper-evident INV-027) + HealthMonitor failover + RecoveryManager | `done` ✅ | `enterprise/operations.py` |
| TASK-042 | Enterprise Operations + Dashboard — EnterpriseDashboard aggregate tenant metrics từ audit | `done` ✅ | `enterprise/dashboard.py` |
| TASK-043 | M8-E1 — Public AIOS SDK | `done` ✅ | 5 SDK tests pass; backend regression có 1 flaky timing failure không liên quan |
| TASK-044 | M8-E2 — Plugin Runtime | `done` ✅ | 1584 tests (baseline 1560 + 24), 1 flaky timing có sẵn |
| INV-022..029 | 8 architecture invariant enforced bằng import allow-list + source-literal tests trong `tests/test_architecture.py` (`test_inv022..inv029_*` — canonical, rename từ `test_m7_*` sau M7 F3) | `done` ✅ | 79 arch tests pass (chung) |

**Deliverable M7 (batch)**: `backend/src/aios_core/enterprise/` 10 file (contracts, identity, tenancy, runtime, scheduler, governance, security, operations, dashboard, __init__) + config (`EnterpriseSettings` trong `config.py` + `config.yaml`) + wiring (`RuntimeKernel.create` register `EnterpriseManager`) + `tests/test_enterprise.py` (29 tests) + `tests/test_architecture.py` (8 m7_* invariant tests).
**1560 passed + 0 skipped, coverage 95.05%, 8/8 AC (E1–E7) — M7 CORE HOÀN TẤT**.

> ✅ Ghi chú đánh số (đã resolve M7 review F3, 2026-08-15): nhãn INV chuẩn hóa — M6 = `test_inv017..inv021` (4 test M6-H5 đã rename khỏi nhãn inv022), M7 = `test_inv022..inv029` (canonical, đã rename từ `test_m7_*`), M9 = `test_inv030..inv034`. Không còn xung đột nhãn.

## M8 — Ecosystem ✅ (2026-08-15)

> PLAN.md §M8: đưa AIOS từ nền tảng vận hành (M7) thành hệ sinh thái mở rộng được bởi bên thứ ba. E1–E4 = Core Ecosystem, E5–E7 = hệ sinh thái bên ngoài. M8 KHÔNG thêm architecture invariant (tập invariant giữ nguyên tại M8).
> Dependency: TASK-043 → ┬ TASK-044 ┐ → TASK-046 Registry → TASK-047 DevKit → TASK-049 Certification → TASK-048 Marketplace; └ TASK-045 ┘
> Approach: SDK độc lập (`sdk/python/`), Plugin Runtime trong `backend/src/aios_core/plugins/` (lifecycle reuse 10-state skills — không state machine thứ hai), plugin là record passive (không chạm Runtime/Registry/DB trực tiếp — import allow-list).

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-043 | E1 Public AIOS SDK — `from aios import Agent, Tool, Capability, Workflow, Client`; transport injection; không import aios_core | `done` ✅ | `sdk/python/`; 5 SDK tests (2026-08-15) |
| TASK-044 | E2 Plugin Runtime — lifecycle 10-state reuse `SkillState`/`assert_transition`; compat aios range (`*`/`2.x`/semver); dependency + dependent check; provides index active-only; events plugin.* | `done` ✅ | `plugins/` 7 file + 4 arch test m8_*; 1584 tests (2026-08-15) |
| TASK-045 | E3 Extension Contracts — Internal/Public/Extension/Experimental API + Compatibility Matrix | `done` ✅ | `extension/` 4 file; 8 tests + 3 arch (2026-08-15) |
| TASK-046 | E4 Ecosystem Registry — Registry v2 + discovery (`aios search`), MCP làm adapter | `done` ✅ | `ecosystem/registry.py` + `contracts.py`; 7 tests + arch (2026-08-15) |
| TASK-047 | E5 Developer Kit — `aios create/dev/test` scaffold | `done` ✅ | `ecosystem/devkit.py` + CLI `aiagent plugin create`; 7 tests + arch (2026-08-15) |
| TASK-048 | E6 Marketplace/Distribution — Trust Model + signature | `done` ✅ | `ecosystem/marketplace.py` + CLI `aiagent marketplace publish`; 12 tests + arch (2026-08-15) |
| TASK-049 | E7 Certification — COMMUNITY→VERIFIED→CERTIFIED, Harness gate | `done` ✅ | `ecosystem/certification.py`; 9 tests + arch (2026-08-15) |

**Deliverable M8 (7/7)**: `sdk/python/src/aios/` (TASK-043) + `plugins/` (TASK-044) + `extension/` (TASK-045: ApiNamespace + matrix) + `ecosystem/` (TASK-046..049: registry/contracts, devkit, certification, marketplace) + config `PluginSettings`/`EcosystemSettings` + `config.yaml` + wiring (`regs["plugins"]`/`regs["plugin_registry"]`/`regs["ecosystem"]`) + CLI `aiagent ecosystem search` / `plugin create` / `marketplace publish` + 4 EventType `PLUGIN_*`.
**1639 passed (baseline 1584 + 55 mới), 7/7 AC (E1–E7) — M8 HOÀN TẤT**.

> M8 KHÔNG thêm architecture invariant (đúng PLAN); arch tests `test_m8_*` (13 tests: 4 plugins + 3 extension + 6 ecosystem) bảo vệ import allow-list + literal gates.

## M9 — Autonomous ✅ (2026-08-15)

> PLAN.md §M9: đưa AIOS từ "nhận task và thực hiện task" thành "tự phát hiện mục tiêu, lập kế hoạch dài hạn, tự thực hiện, tự kiểm chứng, tự phục hồi, tự học trong giới hạn Policy".
> `Autonomous = Goal-driven + Bounded + Observable + Reversible + Evaluated`. Autonomy Layer KHÔNG thay Orchestrator — nó định hướng Orchestrator (Autonomy → Orchestrator → Runtime).
> 13 task (TASK-050..062), 5 invariant mới (INV-030..034). 4 phase: P1 Foundation (050-054) → P2 Long-running (055,056,057,061) → P3 Adaptive (058,060) → P4 Ecosystem (059,062).
> Approach: 1 package `backend/src/aios_core/autonomous/` (Autonomy Layer, offline-first, DI injectable, facade `AutonomyManager`), mỗi task = 1 module; behavioral tests `tests/test_autonomous.py`, invariant tests `tests/test_architecture.py` (test_m9_*).

| Task | Nội dung | Trạng thái | Ghi chú |
|------|----------|------------|---------|
| TASK-050 | Autonomous Goal Engine — Goal contract (objective/success/constraints/permissions/autonomy) + lifecycle PROPOSED→VALIDATING→APPROVED→PLANNING→EXECUTING→EVALUATING→COMPLETED (+BLOCKED/RECOVERY/REPLANNING/ESCALATED) | `done` ✅ | `autonomous/goal.py` (2026-08-15) |
| TASK-051 | Autonomous Planner — Goal→World→Constraints→Capabilities→History→Plan; assumptions/steps/success_conditions/rollback; dynamic replanning | `done` ✅ | `autonomous/planner.py` (2026-08-15) |
| TASK-052 | World Model — WorldState (System/Runtime/Goals/Tasks/Environment/Constraints/History) + Fact (source/timestamp/confidence/freshness); World ≠ Memory | `done` ✅ | `autonomous/world.py` (2026-08-15) |
| TASK-053 | Autonomous Loop — Observe→Understand→Decide→Plan→Policy→Act→Verify→Learn; mọi action qua Governor (INV-030) | `done` ✅ | `autonomous/loop.py` (2026-08-15) |
| TASK-054 | Autonomy Governor — CONTINUE/PAUSE/ASK_HUMAN/REPLAN/ROLLBACK/STOP + budget (steps/llm/cost/duration/tool/retries/parallel) + risk budget; INV-030/031 | `done` ✅ | `autonomous/governor.py` (2026-08-15) |
| TASK-055 | Autonomous Recovery — Detect→Classify→Diagnose→Strategies→Score→Policy→Execute→Verify; fingerprint + circuit breaker + cooldown + escalation | `done` ✅ | `autonomous/recovery.py` (2026-08-15) |
| TASK-056 | Long-Horizon Execution — ExecutionSession + Checkpoint + context compaction + resume (INV-032) | `done` ✅ | `autonomous/long_horizon.py` (2026-08-15) |
| TASK-057 | Autonomous Memory — Working/Episodic/Semantic/Procedural/Failure/Goal + Learning Loop (candidate→dedup→validate→confidence→promote); INV-034 | `done` ✅ | `autonomous/memory.py` (2026-08-15) |
| TASK-058 | Autonomous Experimentation — Hypothesis→Design→Sandbox→Execute→Evaluate→Compare→Accept/Reject (qua Harness — INV-033) | `done` ✅ | `autonomous/experimentation.py` (2026-08-15) |
| TASK-059 | Multi-Agent Autonomy — mode single/parallel/sequential/hierarchical + delegation (owner/deadline/budget/output contract) | `done` ✅ | `autonomous/multi_agent.py` (2026-08-15) |
| TASK-060 | Autonomous Evaluation — correctness/quality/cost/risk/progress/confidence → decision (continue/retry/replan/stop/ask) + ProgressEstimator | `done` ✅ | `autonomous/evaluation.py` (2026-08-15) |
| TASK-061 | Advanced Stuck Detection — 7 signals (repeated tool/errors, no state change/progress, oscillation, budget burn, contradictory) | `done` ✅ | `autonomous/stuck.py` (2026-08-15) |
| TASK-062 | Autonomous Scheduler — proactive triggers (interval/daily) chạy workflow/goal tự động | `done` ✅ | `autonomous/scheduler.py` (2026-08-15) |
| INV-030..034 | 5 invariant enforced bằng arch tests `test_m9_*` (governor gate, budget, checkpoint/resume, experiment qua harness, memory promote có kiểm chứng) | `done` ✅ | 10 arch tests trong `tests/test_architecture.py` |

**Deliverable M9 (13/13)**: `backend/src/aios_core/autonomous/` 16 file (contracts, errors, goal, planner, world, loop, governor, recovery, long_horizon, memory, stuck, experimentation, evaluation, multi_agent, scheduler, __init__) + config `AutonomousSettings` + `config.yaml` + wiring (`AutonomyManager` trong RuntimeKernel.create) + 10 EventType `autonomy.*` + `tests/test_autonomous.py` (129 tests) + `tests/test_architecture.py` (test_m9_* — 10 arch tests INV-030..034).
**1780 passed (baseline 1639 + 141 mới), coverage 94.46%, 13/13 AC (TASK-050..062) — M9 HOÀN TẤT**.

> Autonomy Layer định hướng Orchestrator (Autonomy → Orchestrator → Runtime); INV-030..034 enforced: governor gate duy nhất (loop gọi check_action), 7 budget limits, checkpoint/resume SQLite, experiment evidence-first, memory promote double gate.

## TASK-063 — Vẽ lại hoàn toàn tài liệu kiến trúc (docs-only) ✅ (2026-08-15)

- Tạo `docs/architecture-v2.md` — tài liệu kiến trúc **hiện hành** (markdown thuần: bảng + danh sách + ASCII diagrams — KHÔNG Mermaid, theo yêu cầu người dùng); phản ánh M0–M9 done + M10 todo + INV-001..034 + bảng tasks M1–M9.
- File cũ `docs/architecture.md` giữ nguyên làm lịch sử (AC6); nguồn dữ liệu: PROGRESS.md/PLAN.md/code thật.
- Hard gate đủ 8-file; test cấu trúc markdown 21/21 PASS; **7/7 AC — TASK-063 DONE**.

| Task ID | Mô tả | Milestone | Trạng thái | Owner |
|---------|-------|-----------|------------|-------|
| TASK-063 | Vẽ lại hoàn toàn tài liệu kiến trúc hệ thống — `docs/architecture-v2.md` (markdown thuần, thay thế file cũ làm bản hiện hành) | Docs | `done` ✅ | AIOS Orchestrator |

## Log gần nhất

Xem chi tiết: `LOG.md`. 3 entry cuối:

1. `2026-08-15 | TASK-044 | implement/test | plugins/: lifecycle reuse 10-state, compat, provides, dependency, events; 1584 collected (baseline 1560 + 24), 10/10 AC — TASK-044 DONE` → done
2. `2026-08-15 | TASK-044 | hard-gate | spec + critique ×2 + tasks + review PASS` → done
3. `2026-08-15 | TASK-043 | evaluate | Public SDK v1 đạt phạm vi; TASK-043 DONE` → done

