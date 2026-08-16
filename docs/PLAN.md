# Plan v6: AI Operating System — Runtime-First, Plugin-First, Offline-First, Milestone-Driven

> **Master Plan — Nguồn sự thật của dự án.** File này nằm trong repo, được git-tracked.
> Mọi phiên làm việc: BẮT ĐẦU = đọc file này + `aios/progress/`; KẾT THÚC = cập nhật `aios/progress/` + commit.

## TL;DR
Xây AIOS (AI Operating System) chạy local desktop: Runtime gồm các service nội bộ tách rời, Contract-First version hóa, DI container, capability discovery động, skill lifecycle đầy đủ, workflow snapshot/resume, prompt registry + evaluation framework, sandbox pool, AIOS SDK. AIOS Orchestrator dùng **Decision Pipeline 4 tầng offline-first** (Normalizer → Rule Engine → Workflow Matcher → Planner LLM): 70–90% request xử lý deterministic không cần LLM. LangGraph chỉ là một workflow engine có thể thay thế. **Phát triển dự án qua VS Code Custom Agent "AIOS Orchestrator" + hệ thống progress/log bắt buộc** (aios/progress/). Delivery theo **11 milestone** (M0–M4 core, M5–M10 nâng cao), mỗi milestone là sản phẩm hoàn chỉnh dùng được.

## Kiến trúc tổng thể
```
Tầng 1 UI           Dashboard SPA · CLI · VS Code Extension · AIOS SDK
Tầng 2 Runtime      Runtime Kernel = 9 services (tách rời, thay thế được từng phần)
Tầng 3 Workflow     Workflow Definition (declarative contract) → compile → engine (LangGraph/Mock/khác)
Tầng 4 Agents       AIOS Orchestrator (Control Plane) + Worker Plane:
                    General · Coder Pipeline · Doctor Pipeline · System Doctor
Tầng 5 Capability   Capability Registry (dynamic discovery từ tools)
Tầng 6 Tools        Python · Docker · REST · MCP · Shell · Git
Tầng 7 Infra        Model Providers · Memory 4 loại · Knowledge Base + Graph · Sandbox Pool · Filesystem
```
Mô hình phân cấp: **Control Plane** = AIOS Orchestrator (điều phối, lập kế hoạch, giám sát, quản trị); **Worker Plane** = các agent chuyên môn (chỉ làm nghiệp vụ, truy cập hệ thống qua Capability + Runtime).

## Nguyên tắc nguồn sự thật (Source of Truth = Repo, không phải bộ nhớ phiên)

**Quy tắc bất biến khi vận hành dự án:**
1. **Mọi file cấu trúc hệ thống phải nằm trong repo trước khi làm việc** — không bao giờ chỉ tồn tại trong bộ nhớ tạm/chat session
2. File gốc chuẩn (canonical):
   - `docs/PLAN.md` — master plan (bản v6 này, sao chép từ session vào repo NGAY đầu M0, git-tracked)
   - `aios/progress/PROGRESS.md` — trạng thái tiến độ hiện tại (đọc đầu phiên, cập nhật cuối phiên)
   - `aios/progress/LOG.md` — nhật ký hành động (mỗi bước đều ghi)
   - `AGENTS.md` — hướng dẫn bắt buộc mọi agent session: đọc từ repo trước, ghi vào repo sau
3. **Mỗi phiên làm việc (kể cả khi chuyển session/agent mới)**: BẮT ĐẦU = đọc `docs/PLAN.md` + `aios/progress/` từ repo; KẾT THÚC = cập nhật repo files + commit. Nếu không nhớ "đã làm tới đâu" → đọc PROGRESS.md, không hỏi chat memory
4. Autopilot/checkpoint trong session chỉ là bản sao — **repo là bản chính**

## Quyết định vận hành: Start Implementation vs Start with Autopilot

- **M0 (bước đầu, có gate cần xác nhận) → chọn "Start Implementation"**: chạy từng bước trong phiên hiện tại, mỗi gate (tạo agent file → tạo progress system → verify hard gate) bạn xem và xác nhận trước khi sang bước kế. Lý do: M0 nhỏ, cần người xác nhận hành vi agent đúng trước khi mở rộng
- **M1–M4 (các phase dài, nhiều bước lặp) → có thể dùng "Start with Autopilot"**: chạy tự động nhiều phase, nhưng KÈM ĐIỀU KIỆN: agent phải (a) cập nhật repo files (PROGRESS.md/LOG.md) sau MỖI phase, (b) commit, (c) dừng lại xin xác nhận khi gặp hard gate/approval cần người — checkpoint session chỉ là phụ, repo mới là chính
- Khuyến nghị thực dụng: bắt đầu M0 bằng "Start Implementation"; từ M1 trở đi dùng "Start with Autopilot" cho từng phase con, kết thúc mỗi phase bằng việc đối chiếu PROGRESS.md trong repo

## VS Code Custom Agent: AIOS Orchestrator (Development Control Plane)

File: `.github/agents/aios-orchestrator.agent.md` (workspace scope) — agent DUY NHẤT người dùng chọn trong VS Code agent picker (thay vì Plan/Ask), mọi thao tác phát triển đi qua agent này.

**Frontmatter**: `description` keyword-rich (plan, spec, critique, task, review, implement, test, evaluate, progress, log — để tự invoke đúng); `tools: [read, edit, search, execute, todo, agent, web]`; `user-invocable: true`; `model: []` fallback array.

**Body — persona & luật bắt buộc**:
- Là "Development Control Plane": phiên bản offline-first của AIOS Orchestrator chạy ngay trong VS Code, áp dụng cùng triết lý (deterministic trước, LLM sau)
- **Bắt buộc đọc `aios/progress/PROGRESS.md` + `LOG.md` đầu mỗi phiên** — biết tiến độ trước khi làm gì
- **Ghi `LOG.md` sau mỗi hành động** (timestamp, task id, bước, việc đã làm, kết quả, artifact)
- **Cập nhật `PROGRESS.md`** sau mỗi trạng thái thay đổi
- **Hard gate**: từ chối implement nếu task chưa hoàn thành đủ chuỗi: plan → spec → critique ×2 (đã resolve) → task → review → implement → test → evaluate
- **Bypass fix nhỏ** (1 dòng, typo, fix nhanh): được phép bỏ qua pipeline NHƯNG phải ghi vào LOG.md với lý do bypass
- Chia nhỏ mọi công việc thành task có id (`TASK-xxx`) trong `aios/progress/tasks/`
- Khi AIOS backend hoàn thiện (M2+): agent này tiến hóa thành cầu nối tới AIOS Orchestrator thật (MCP/REST), nhưng quy trình progress/log giữ nguyên

**Subagents phụ trợ** (cùng thư mục, `user-invocable: false`, invoke qua `agent` tool): `spec-writer.agent.md` (viết spec), `critic.agent.md` (phản biện spec — 2 vòng bắt buộc, độc lập quan điểm), `reviewer.agent.md` (review code trước khi đánh dấu done).

## Progress & Log System (aios/progress/) — quản lý tiến độ dự án

```
aios/progress/
├── PROGRESS.md            # Chỉ mục tổng: milestones, phases, tasks, trạng thái (todo/in-progress/done/blocked), owner
├── LOG.md                 # Nhật ký thời gian thực: timestamp | task id | bước | việc đã làm | kết quả | artifact
├── STATS.md               # Tổng hợp định kỳ: task hoàn thành/thất bại, tỷ lệ critique resolve, thời gian/bước
└── tasks/
    └── TASK-xxx/
        ├── spec.md           # Đặc tả: mục tiêu, phạm vi, input/output, tiêu chí chấp nhận
        ├── critique-1.md     # Phản biện vòng 1 (bởi critic agent) + resolution
        ├── critique-2.md     # Phản biện vòng 2 (bắt buộc, sau khi resolve vòng 1) + resolution
        ├── tasks.md          # Breakdown checklist các bước con (checkbox)
        ├── review.md         # Review trước khi đánh dấu done (bởi reviewer agent)
        ├── implementation/   # Code + artifact của task
        ├── test.md           # Kết quả test (unit/integration/manual)
        └── evaluation.md     # Đánh giá cuối: đạt/không đạt spec, bài học, đề xuất cải tiến
```

**Workflow Gate (chuỗi bắt buộc mỗi task)**:
1. **Plan** — ghi vào PROGRESS.md, chia nhỏ task
2. **Spec** — viết `spec.md` (mục tiêu, phạm vi, tiêu chí chấp nhận)
3. **Critique ×2** — `critique-1.md` → resolve → `critique-2.md` → resolve (phản biện độc lập, bắt buộc đủ 2 vòng)
4. **Task** — breakdown `tasks.md` thành các bước nhỏ có checkbox
5. **Review** — `review.md` (trước implement: đánh giá spec/sắp xếp; sau implement: kiểm tra code)
6. **Implement** — code theo spec, cập nhật LOG.md song song
7. **Test** — `test.md` + chạy test thật (pytest/sandbox)
8. **Evaluate** — `evaluation.md`: đối chiếu tiêu chí chấp nhận, đánh giá hệ thống tổng thể, bài học

**Bypass hợp lệ** (fix nhỏ): quy trình rút gọn nhưng BẮT BUỘC ghi LOG.md + đánh dấu `[bypass]` trong PROGRESS.md. Mọi task khác đều hard gate.

**Branching Model (BẮT BUỘC — chi tiết [ADR-0005](adr/0005-branching-model.md) + [ADR-0006](adr/0006-issue-pr-workflow.md))**:
- `master` = ổn định, CHỈ nhận từ `verify` (không commit/merge trực tiếp).
- Nhánh chức năng tạo TỪ `verify` (tiền tố: `feature/`, `fix/`, `docs/`, `operation/`, `refactor/`, `test/`...).
- Chuỗi: nhánh chức năng → merge vào `verify` → kiểm tra (test + hard gate + review) → PASS → merge `verify` → `master`.
- **Issue-Driven (bắt buộc từ 2026-08-16)**: mọi thay đổi bắt đầu từ GitHub Issue (3 template) → nhánh `<type>/ISSUE-N-slug` từ `verify` → PR draft (base `verify`) → sửa → merge thủ công vào `verify` → PR promotion `release: verify → master (YYYY-MM-DD)` do người dùng duyệt & merge thủ công. Action `pr-validation.yml` kiểm tra title/base/link issue tự động. Chi tiết: `docs/workflows/issue-pr-workflow.md`.

**Definition of Done — Closing Checklist (bắt buộc sau MỖI task/yêu cầu xử lý xong)**:
Trước khi đánh dấu task `done` hoặc kết thúc phiên, đối chiếu đủ (chi tiết: AGENTS.md §3.1):
1. `LOG.md` — entry mới (thời gian | task | bước | việc đã làm | kết quả | artifact)
2. `PROGRESS.md` — cập nhật trạng thái task/milestone/phase (todo/in-progress/done/blocked)
3. `docs/PLAN.md` — cập nhật nếu milestone/phase/plan/ADR bị ảnh hưởng
4. `STATS.md` — cập nhật nếu kết thúc milestone
5. Task folder — đủ 8-file hard gate + artifact
6. Commit — sau mỗi bước hoàn chỉnh, working tree sạch khi kết thúc

**Đặt ở milestone**: Phase M0 (Development Foundation) — tạo ngay khi khởi động dự án, TRƯỚC M1. Đây cũng là nơi "dogfood" triết lý Orchestrator (offline-first, deterministic, có log) trước khi có hệ thống thật.

## AIOS Orchestrator (Control Plane — bộ não hệ thống)

Trợ lý mặc định của AIOS. Nguyên tắc: **không để LLM tham gia routing mặc định**.

### Decision Pipeline 4 tầng (offline-first)
```
Request
  ↓
Normalizer (không dùng LLM)
  ↓
Rule Engine (deterministic)
  ↓
Workflow Matcher
  ↓
Planner (LLM — chỉ khi thật sự cần)
  ↓
Execution Plan
```
- **Normalizer**: phân tích CLI/API/UI, chuẩn hóa tham số, alias, macro → `NormalizedRequest` (VD: "review project" → `{intent: review_code, target: workspace}`)
- **Rule Engine**: deterministic, xử lý trường hợp rõ ràng (chat/coding/doctor/system/skill/upgrade/diagnose). **70–90% request dừng ở đây**, 0 token, test được unit test
- **Workflow Matcher**: tìm workflow/template/macro phù hợp trong Workflow Library (VD: "Create CRUD API" → CRUD Generator workflow — không cần Planner)
- **Planner (LLM)**: chỉ dùng khi không có workflow phù hợp / cần kết hợp nhiều workflow / cần sinh workflow mới / nhiệm vụ mở (VD: "Phân tích toàn bộ dự án rồi đề xuất kiến trúc mới")

Thứ tự ưu tiên: **1. Rule Engine → 2. Workflow Library → 3. Planner LLM → 4. Human Approval** (nếu policy yêu cầu).

### Các module nội bộ (Orchestrator v2 — 22 module)

**Decision Pipeline (4 tầng):**
- **Normalizer**: CLI/API/UI → `NormalizedRequest` (chuẩn hóa tham số, alias, macro) — không dùng LLM
- **Rule Engine**: deterministic rules cho intent rõ ràng (chat/coding/doctor/system/skill/upgrade/diagnose) — 70–90% request dừng tại đây
- **Workflow Matcher**: tìm workflow/template/macro phù hợp trong Workflow Library
- **Planner (LLM)**: chỉ khi Workflow Matcher không tìm thấy / cần kết hợp nhiều workflow / sinh workflow mới / nhiệm vụ mở

**Điều phối & thực thi:**
- **Task Planner**: tạo Execution Plan từ NormalizedRequest
- **Agent Selector**: chọn agent phù hợp (Generate API → Coder; medical question → Doctor; analyze system → System Doctor); hỗ trợ chuỗi nhiều agent (Coder → Tester)
- **Capability Router**: chỉ chọn Capability, KHÔNG chọn tool trực tiếp
- **Resource Scheduler**: trao đổi với Resource Service (GPU available? → Run hoặc Queue)
- **Execution Supervisor**: theo dõi running workflows, queue, events
- **Failure Recovery**: Agent lỗi → Retry → Fallback Agent → Fallback Workflow → Report
- **Context Coordinator**: quyết định context nào truyền/xóa/cache
- **Memory Coordinator**: quyết định lưu Conversation/Knowledge/Artifact hay bỏ qua

**Quản trị & policy:**
- **Policy Engine**: quyết định Có được chạy không / Cần approve không / Cần sandbox không / Giới hạn tài nguyên / Cho phép Internet — Permission chỉ là MỘT PHẦN của Policy
- **Permission Broker**: gom permission của workflow (filesystem/network/shell/docker...) → hiển thị → xin user approve (thuộc Policy Engine)
- **Skill Manager Proxy**: tìm/cài/update/rollback/enable/disable skill, resolve dependency, kiểm tra compatibility
- **Goal Manager**: goal dài hạn nhiều phiên (VD: "Xây AIOS") → tasks → workflows → theo dõi progress, persist qua phiên
- **Task Queue**: queue logic (pause/resume/reorder/priority) — khác Scheduler Service (kỹ thuật: cron/one-shot)
- **System Catalog**: "mục lục" của AIOS — index + search metadata từ toàn bộ registry, Orchestrator KHÔNG quét registry mỗi lần
- **System Knowledge**: trả lời trực tiếp dựa trên Catalog + Knowledge Graph: "Có bao nhiêu skill?", "Agent nào dùng execute_code?", "Workflow nào đang chạy?", "Docker khỏe không?", "Skill nào phụ thuộc MCP?"

**Cải tiến & học hỏi:**
- **Evaluation Collector**: thu thập evaluation sau mỗi workflow
- **Improvement Advisor**: định kỳ đọc workflow/log/evaluation → đề xuất skill/workflow/prompt/capability mới
- **Knowledge Graph**: đồ thị liên kết Agent–Skill–Workflow–Capability–Tool–Artifact (VD: capability `execute_code` được dùng bởi agent nào → trả lời nhanh O(1))

### Quyền hạn (đặc biệt)
Orchestrator là agent DUY NHẤT truy cập trực tiếp: Runtime Services, Event Bus, Resource Service, Scheduler, Policy Engine, Capability/Agent/Workflow/Tool/Skill/Prompt/Contract/Model Registry, Knowledge Base + Graph, Observability, Health System, System Catalog.
Mọi agent khác (Worker Plane) chỉ truy cập qua Capability + Runtime — enforced bởi Permission Service + Policy Engine.

**Architecture Invariants (INV-001..INV-034)** — bất biến kiến trúc bắt buộc, vi phạm = FAIL architecture review. Xem [ADR-0004](adr/0004-architecture-invariants.md) + `docs/architecture.md` §7 + enforcement tự động `backend/tests/test_architecture.py`. 4 invariant chốt cốt lõi (M0–M4): Orchestrator không God Object; Agent không chạm Tool; Workflow không biết Engine; Execution không bypass Policy. 6 invariant bổ sung (M5 — Core Intelligence): INV-011 Memory Isolation; INV-012 Context Budget; INV-013 Model Routing Policy; INV-014 Plan Validation; INV-015 Graph Acyclicity; INV-016 Scheduler Separation. 5 invariant bổ sung (M6 — Harness): INV-017 Harness Isolation; INV-018 Evidence First; INV-019 Verification Before Verdict; INV-020 Evaluation Determinism; INV-021 Release Gate. 8 invariant bổ sung (M7 — Enterprise): INV-022 Identity First; INV-023 Tenant Isolation; INV-024 Credential Isolation; INV-025 Resource Fairness; INV-026 Distributed Execution Safety; INV-027 Audit Completeness; INV-028 Sandbox Boundary; INV-029 Control Plane Isolation. 5 invariant bổ sung (M9 — Autonomous): INV-030 Autonomous Action Boundary; INV-031 Autonomy Bounded; INV-032 Long-running Resumable; INV-033 Self-Improvement via Harness; INV-034 Autonomous Memory No Unverified Promote. **M10 — AIOS 1.0 freeze toàn bộ INV-001..INV-034 (không thêm invariant mới), vi phạm = release blocker**.

### Vị trí trong milestones
- **M1 (P0.5–P2)**: Policy Engine core + System Catalog (index/search từ registry) + Knowledge Graph (đồ thị metadata) xây cùng kernel/registry
- **M2 (P3)**: Orchestrator v1 — Decision Pipeline đầy đủ (Normalizer, Rule Engine, Workflow Matcher, Planner LLM), Workflow Library, Goal Manager + Task Queue v1, Permission Broker, Failure Recovery, System Knowledge, Capability Router
- **M4 (P8)**: Orchestrator v2 — Improvement Advisor (self-improvement), Execution Supervisor nâng cao, Evaluation Collector đầy đủ, Goal Manager nâng cao (progress tracking + báo cáo)
- **M5 (P9–P10)**: Core Intelligence — nâng cấp Memory Coordinator (TASK-023) + Context Optimizer (TASK-024) + Model Router (TASK-025) + Planning Engine (TASK-026) + Execution Graph (TASK-027, DAG) + Parallel Scheduler (TASK-028). Bổ sung 6 invariant (INV-011..016: Memory Isolation, Context Budget, Model Routing Policy, Plan Validation, Graph Acyclicity, Scheduler Separation). Các năng lực lõi này được Runtime, Orchestrator và Harness (M6) dùng chung — không tạo hệ thống song song
- **M6 (P11)**: AIOS Harness — subsystem `aios/harness/` hỗ trợ AIOS kiểm thử/xác minh/quan sát/cải tiến chính nó (5 năng lực H1–H5: Kernel, Execution Verification, Test & Simulation, Evaluation & Benchmark, Doctor & Readiness; TASK-029..034). Bổ sung 5 invariant (INV-017..021: Harness Isolation, Evidence First, Verification Before Verdict, Evaluation Determinism, Release Gate). Không sửa Runtime/Orchestrator, chỉ gọi qua API

## Runtime Kernel = 9 services
- **Execution Service**: chạy workflow từ Execution Plan, retry/cancel/timeout, checkpoint/snapshot/resume
- **Context Service**: quản lý 6 loại context có vòng đời riêng
- **Event Service**: pub/sub event bus + audit log
- **Artifact Service**: lưu/quản lý artifact (checksum, metadata, version)
- **Permission Service**: policy allow/deny/ask, enforce trên 8 scopes
- **Policy Service**: Policy Engine core — quyết định Có chạy được không / Cần approve / Cần sandbox / Giới hạn tài nguyên / Internet — Permission chỉ là 1 phần. Chạy trước Execution (pre-check), enforce xuyên suốt
- **Scheduler Service**: lịch chạy workflow (cron/one-shot/queue) — queue KỸ THUẬT
- **State Service**: state machine, checkpointing, snapshot/resume
- **Resource Service**: Resource Manager (CPU/RAM/GPU/Disk/token budget/concurrent workflows/docker containers) — Grant/Queue/Reject

## Context 6 loại (Context Service)
System Context (môi trường, cấu hình) · User Context (hồ sơ, preferences) · Workflow Context (chạy 1 workflow) · Agent Context (vòng đời agent) · Execution Context (1 lần thực thi) · Shared Context (chia sẻ giữa workflow). Mỗi loại có vòng đời + TTL + quyền truy cập riêng.

## Workflow Definition (độc lập engine)
```yaml
workflow:
  name, version, description
  nodes: [...]
  edges: [...]
  retries: n
  timeout: s
  resources: {gpu: 1, tokens: 50000}
  permissions: [...]
```
→ compile sang engine (LangGraph hiện tại; Mock cho simulation; sau này CrewAI/AutoGen chỉ cần thêm compiler).

## Execution Plan
Request → Planner → Execution Plan (artifact: nodes dự kiến, resource estimate, permission pre-scan, cost estimate) → Executor. Execution Plan xem được trên Dashboard, chạy được ở Simulation Mode, lưu làm audit.

## Contracts (version hóa)
7 contract + 3 trường version: contract_version, schema_version, compatibility (major/minor: major = breaking, minor = backward-compatible). AiOS Metadata (id, name, version, author, created, updated, license, dependencies, permissions, tags, health, checksum) cho mọi component.

## DI Container
Runtime → Container (đăng ký service, lazy resolve, lifecycle hooks, scope: singleton/scoped/transient) → Agent. Agent nhận dependency qua constructor injection. Test bằng cách đăng ký mock implementation.

## Capability Discovery động
Tool tự khai báo `capabilities: [execute_code, run_python, run_tests]` trong ToolContract. Runtime scan registry → auto-map capability ↔ tool. Capability có thể map nhiều tool; router chọn theo health/availability/priority.

## Skill Lifecycle đầy đủ
Resolve → Validate → Install → Enable → Disable → Unload → Reload → Upgrade → Rollback → Remove
Enable/Disable/Unload cho phép tắt tạm plugin không cần gỡ. Trạng thái persist trong DB.

## Snapshot & Resume
Execution checkpoint mỗi node boundary (state + context + artifacts refs) → snapshot (artifact) → resume sau crash/restart. Đi kèm retry policy.

## Prompt Registry
Template (v1: **str.format subset** — `{identifier}` thuần; **jinja2 → M4**) → Variables (schema) → Version (semver) → Evaluation (điểm) → hỗ trợ A/B testing sau này. Prompt là first-class component (có id, version, metadata), skill có thể đóng góp prompt.

## Evaluation Framework
Sau mỗi workflow: Output → Evaluator → Score → Knowledge (lưu vào memory để cải thiện). Metrics: success, cost, tokens, time, quality, user feedback. API chuẩn để plug evaluator mới.

## Knowledge Base (tách khỏi vector DB thô)
Raw Docs → Indexer (parser theo loại file) → Chunks → Embeddings → Knowledge Store (ChromaDB + metadata) → Retriever (semantic + keyword + hybrid). Hỗ trợ nhiều nguồn: docs local, web, PDF, codebase.

## Knowledge Graph
Đồ thị liên kết: Agent–Skill–Workflow–Capability–Tool–Artifact–Model–Prompt (nodes + edges có thuộc tính, có version). Xây từ metadata các registry, cập nhật theo sự kiện (event bus). Mục đích: trả lời quan hệ nhanh ("capability execute_code được dùng bởi agent nào", "skill nào phụ thuộc MCP") mà không cần quét; nền tảng cho System Knowledge + Improvement Advisor.
> **Amend TASK-009 (2026-08-12)**: v1 graph **in-memory** + populate THỦ CÔNG (index/add qua API); SQLite persist + auto-build từ registry/event bus → M2/M4 (quyết định đã qua critique — ghi PROGRESS).

## Workflow Library
Kho workflow/template/macro có thể tái sử dụng (kèm metadata: input/output, capabilities cần, đánh giá hiệu suất). Orchestrator ưu tiên **tái sử dụng trước khi sinh mới**: Search → Reuse → Planner. Workflow chạy thành công nhiều lần được "thăng hạng" (promote) trong library.

## Policy Engine
Policy (cấu hình, có version) quyết định trước khi chạy: Có được chạy không / Cần approve không / Cần sandbox không / Giới hạn tài nguyên / Có cho phép Internet không. Permission chỉ là MỘT PHẦN của policy. Cấu trúc: Policy (rules có version) → Policy Service (đánh giá) → Quyết định (allow/deny/ask với lý do). Skill/Workflow khai báo yêu cầu (permissions, resources, network) trong manifest; Policy Service đối chiếu với policy hiện hành → cho phép hoặc chặn từ trước khi execution.

## Goal Manager + Task Queue
- **Goal Manager**: goal dài hạn nhiều phiên (VD: "Xây AIOS") → chia tasks → mỗi task là workflow → theo dõi progress, persist trong DB, tiếp tục được qua phiên mới
- **Task Queue**: queue LOGIC của Orchestrator (khác Scheduler Service là queue kỹ thuật) — hỗ trợ pause/resume/reorder/priority; goal đẩy task vào queue, Execution Supervisor lấy ra chạy

## Sandbox Pool
Pool tái sử dụng container theo ngôn ngữ (python/node/go...), warm-start, health check, reset state giữa lần chạy, eviction khi idle. Giảm đáng kể latency so với tạo container mỗi lần.

## AIOS SDK (đồng bộ từ đầu)

## Architecture Decisions (ADR)
Xem [`docs/adr/`](adr/): 0001-engine-independence, 0002-capability-first, 0003-policy-first, 0004-architecture-invariants, 0005-branching-model.

## Architecture Health (kế hoạch M4 — P8)
Ngoài health hạ tầng (Docker/model/memory), M4 bổ sung **Architecture Health**: contract violations, layer violations, dependency violations, capability bypass, permission bypass, orphan components, broken registrations, circular dependencies, deprecated contracts — phù hợp hướng System Doctor + System Evolution Engine (TASK-016 đã ghi nhận, chưa enforce).
- sdk/python: decorators + base classes để viết Agent, Tool, Capability, Skill, Prompt, Workflow (ví dụ @aios.tool, @aios.agent, @aios.workflow)
- sdk/typescript: client cho extension + dashboard + viết tool bằng TS
- SDK dùng chung contract schemas (generate từ backend contracts)

## Cấu trúc monorepo
> **Quy ước layout M1 (TASK-002, đã qua critique/review)**: toàn bộ code Python gom vào
> `backend/src/<package>/` (src layout). `backend/core/` theo bảng dưới chính là package
> `aios_core` (code tại `backend/src/aios_core/`); các thư mục `backend/<module>/` khác là
> placeholder `.gitkeep` làm định hướng, code thật của chúng đặt tại `backend/src/<package>/`
> tương ứng (VD DI container TASK-003 → `backend/src/aios_core/container.py`).

```
aiagent/
├── .github/
│   └── agents/          # VS Code custom agents: aios-orchestrator.agent.md (Control Plane),
│                        # spec-writer.agent.md, critic.agent.md, reviewer.agent.md
├── aios/
│   ├── progress/        # PROGRESS.md, LOG.md, STATS.md, tasks/TASK-xxx/ (spec, critique-1/2, tasks, review, implementation, test, evaluation)
│   └── harness/         # M6 AIOS Harness subsystem: contracts/ + kernel/ (H1) + execution/ (H2 Verification) + testing/ (H3) + evaluation/ (H4) + doctor/ (H5) — xem M6
├── sdk/python/          # SDK viết agent/tool/skill/workflow
├── sdk/typescript/      # SDK TS cho extension/dashboard
├── backend/
│   ├── core/            # config, logging, AIOS metadata, healthcheck, DI container
│   ├── contracts/       # contract schemas + versioning + compatibility checker
│   ├── kernel/          # 9 services (execution, context, event, artifact, permission,
│   │                    # policy, scheduler, state, resource)
│   ├── orchestrator/    # AIOS Orchestrator: decision pipeline (normalizer, rule_engine,
│   │                    # workflow_matcher, planner_llm), task_planner, agent_selector,
│   │                    # capability_router, skill_manager_proxy, resource_scheduler,
│   │                    # permission_broker, context_coordinator, memory_coordinator,
│   │                    # execution_supervisor, failure_recovery, evaluation_collector,
│   │                    # improvement_advisor, goal_manager, task_queue, system_knowledge
│   ├── catalog/         # System Catalog: index + search toàn bộ registry
│   ├── policy/          # Policy Engine: policy definitions + evaluation
│   ├── goals/           # Goal Manager + Task Queue (logic queue)
│   ├── models/          # ModelContract + providers (OpenAI, Ollama, Mock)
│   ├── memory/          # 4 loại memory
│   ├── knowledge/       # indexer, chunks, embeddings, store, retriever, knowledge graph
│   ├── workflow/        # workflow definitions + compilers (langgraph, mock) + workflow library
│   ├── agents/          # General, Coder, Doctor, System Doctor
│   ├── capabilities/    # capability registry + discovery
│   ├── tools/           # tool registry + 6 tool types
│   ├── skills/          # skill manager + lifecycle
│   ├── sandbox/         # sandbox pool + images
│   ├── evaluation/      # evaluator framework + metrics
│   ├── prompts/         # prompt registry + templates + versions
│   ├── observability/   # metrics, health, audit, simulation, profiler
│   ├── api/             # FastAPI REST + WebSocket
│   └── cli/
├── dashboard/           # React + Vite SPA
├── extension/           # VS Code extension (TS)
├── skills/              # skill packs mặc định (coding, health)
├── docker/              # sandbox images
└── docs/
```

## Milestones (mỗi milestone = sản phẩm hoàn chỉnh)

### M0 – Development Foundation (khởi động dự án, TRƯỚC M1)
- **Bước 0 (bắt buộc đầu tiên — trả lời lo ngại "quên đã làm tới đâu")**: git init + sao chép master plan v6 từ session → `docs/PLAN.md` + tạo `AGENTS.md` gốc → commit ngay. Từ thời điểm này, repo là nguồn sự thật, mọi phiên sau đọc từ repo
- Tạo VS Code custom agent: `.github/agents/aios-orchestrator.agent.md` (persona + hard gate + bypass rules) + `spec-writer.agent.md`, `critic.agent.md`, `reviewer.agent.md`
- Tạo `aios/progress/`: PROGRESS.md, LOG.md, STATS.md, `tasks/` template (TASK-001 mẫu hoàn chỉnh: spec + critique-1/2 + tasks + review + test + evaluation)
- Tạo `AGENTS.md`/`copilot-instructions.md` gốc: đọc PROGRESS.md đầu phiên, ghi LOG.md sau mỗi hành động
- → Kết quả: mọi công việc từ giờ đi qua AIOS Orchestrator agent + progress/log đầy đủ, **toàn bộ trạng thái nằm trong repo (đã commit), không phụ thuộc bộ nhớ phiên chat**

### M1 – Core Runtime (P0–P2)
P0 Infrastructure: scaffold monorepo, config, logging, AIOS metadata, healthcheck
P0.5 Runtime Kernel: DI container + 9 services + contracts version hóa + event bus + artifact + permission + **policy service** + context + state/snapshot + resource manager + execution plan
P1 Model + Memory + Knowledge: ModelContract (OpenAI/Ollama/Mock), memory 4 loại, knowledge pipeline (indexer→store→retriever)
P2 Workflow + Capability + Catalog: workflow definition declarative + compilers (langgraph + mock) + workflow library (v1), capability discovery, prompt registry (v1), **System Catalog** (index/search registry), **Knowledge Graph (v1 in-memory, populate thủ công — xem amend section Knowledge Graph)**
→ Kết quả: `aiagent run workflow.yaml --simulate` chạy được, test unit phủ contract, policy pre-check chặn request không được phép

### M2 – Developer Edition (P3–P4)
P3 Orchestrator v1 + Assistants: **Decision Pipeline đầy đủ** (Normalizer, Rule Engine deterministic, Workflow Matcher + Workflow Library, Planner LLM fallback), Goal Manager + Task Queue v1, Permission Broker, Failure Recovery, System Knowledge, Capability Router; General, Coder pipeline (Requirement→Planner→Generator→Static Analysis→Formatter→Unit Test→Integration Test→Self Fix→Repeat), Doctor pipeline (Symptom Extractor→Medical Knowledge→Risk Assessment→Recommendation→Safety Layer→Final Response)
P4 Tools + Skills + Sandbox Pool: 6 tool types, skill lifecycle đầy đủ (10 trạng thái), sandbox pool, skill manager (zip/git/pip)
→ Kết quả: dev dùng CLI (mặc định đi qua Orchestrator, **hoạt động offline khi không có LLM**) để agent sinh code + test trong sandbox, cài skill plugin đầy đủ

### M3 – Desktop Edition (P5–P6)
P5 Dashboard 10 view: Chat, Workflow Viewer (execution plan + live), Event Timeline (WebSocket), Tool Usage, Memory Viewer, Artifact Browser, Skill Marketplace, Model Usage, Prompt Inspector, Health Dashboard
P6 VS Code Extension 9 lệnh: Chat, Explain, Fix selection, Generate test, Review PR, Refactor, Rename, Ask Workspace, Chat với repo
→ Kết quả: sản phẩm desktop hoàn chỉnh cho người dùng cuối

### M4 – Platform Edition (P7–P8)
P7 Upgrade pipeline: Compatibility Check (contract version) → Dependency Resolution → Backup → Migration → Health Check → Rollback if failed
P8 Observability & Diagnostics + Orchestrator v2: metrics, audit log, prompt history, simulation mode, system doctor, performance profiler, health score, evaluation framework v2 (gắn vào workflow); Orchestrator v2 — Improvement Advisor (tự đề xuất skill/workflow/prompt mới từ log + evaluation), Execution Supervisor nâng cao, Evaluation Collector đầy đủ, Goal Manager nâng cao (progress tracking + báo cáo)
→ Kết quả: nền tảng tự giám sát + tự nâng cấp an toàn + tự cải thiện

### M5 – Core Intelligence (P9–P10)
> M5 nên được xem là **milestone nâng cấp "bộ não vận hành" của AIOS**, KHÔNG phải thêm agent hay thêm UI.
> Mục tiêu: AIOS phải hiểu tốt hơn request, biết lấy đúng thông tin, chọn đúng model, lập kế hoạch tốt hơn và thực thi được các task có dependency/parallel.
> Hiện M0–M4 đã xây **execution infrastructure** khá đầy đủ. M5 giải quyết khoảng trống giữa:
> ```
> Request → Orchestrator → ExecutionPlan → Runtime
> ```
> thành:
> ```
> Request → Understand → Retrieve Knowledge/Memory → Optimize Context → Select Model
>        → Plan → Build Execution Graph → Schedule → Runtime
> ```

#### 1. M5 KHÔNG nên làm gì? (scope guard — tránh scope creep)
M5 **không làm**: Multi-tenant · Distributed Runtime · Marketplace · Plugin ecosystem · Autonomous self-modification · Production-grade real Tool execution · UI lớn · Multi-agent conversation framework. Các phần đó để M7–M9. M5 tập trung vào **Intelligence Core**.

#### 2. Năm năng lực chính
```
M5 Core Intelligence
├── Memory Intelligence    → TASK-023 Memory Coordinator
├── Context Intelligence   → TASK-024 Context Optimizer
├── Model Intelligence     → TASK-025 Model Router
├── Planning Intelligence  → TASK-026 Planning Engine
└── Execution Intelligence → TASK-027 Execution Graph + TASK-028 Parallel Scheduler
```
| Năng lực | Trả lời câu hỏi |
|----------|-----------------|
| Memory | AIOS cần nhớ gì? |
| Context | AIOS cần đưa gì vào lần chạy này? |
| Model Router | Nên dùng model nào? |
| Planning | Nên làm những bước nào? |
| Execution Graph | Các bước phụ thuộc nhau thế nào? |
| Scheduler | Chạy chúng khi nào và song song ra sao? |

#### 3. TASK-023 — Memory Coordinator (quan trọng nhất M5)
Hiện AIOS có 4 loại Memory (Conversation/Session/Knowledge/Artifact) nhưng thiếu tầng quyết định: *"Trong tất cả những gì AIOS biết, cái gì thực sự cần đưa vào execution hiện tại?"*
```
                 Memory Stores
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
 Conversation      Session       Knowledge
       │              │              │
       └──────────────┼──────────────┘
                      ▼
              Memory Coordinator
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Retrieve      Rank      Compress
                      │
                      ▼
               Memory Context → ContextService
```
**Trách nhiệm**: Retrieve → Filter → Rank → Deduplicate → Compress → Prioritize → Inject. **Agent KHÔNG được truy cập Memory trực tiếp** — mở rộng nguyên tắc `Agent → Capability → Tool` thành `Memory → Coordinator → Context → Agent`.

**3.1 Retrieval Strategy** — không chỉ semantic: `Exact · Keyword · Semantic · Metadata · Recency · Importance · Hybrid`. VD: "tiếp tục sửa lỗi Oracle hôm qua" → tìm Conversation ("Oracle TIMESTAMP issue") + Session (debugging) + Knowledge (timezone) + Artifact (code patch).

**3.2 Ranking** — không chỉ similarity. `MemoryScore = semantic + relevance + recency + importance + source_priority`. **Ưu tiên deterministic ranking trước**, không nhất thiết dùng LLM.

**3.3 Memory Budget** — VD context 20,000 tokens: System 3K · Task 2K · Knowledge 6K · History 5K · Artifacts 3K · Reserve 1K. Tiền đề cho Context Optimizer.

**3.4 Contract** — tạo `MemoryQuery · MemoryCandidate · MemoryScore · MemorySelection · MemoryContext`. Coordinator không phụ thuộc implementation cụ thể của vector store.

#### 4. TASK-024 — Context Optimizer
Memory Coordinator trả lời *"Nên lấy memory nào?"*; Context Optimizer trả lời *"Trong những thông tin đó, nên đưa bao nhiêu và dưới dạng nào vào model?"* — hai trách nhiệm khác nhau.
```
Memory → Retrieve → Rank → Context Optimizer → Deduplicate → Compress
       → Prioritize → Token Budget → Final Context
```

**5. Context Priority** (loại bỏ từ dưới lên nếu thiếu token, không truncate ngẫu nhiên):
`P0 System/Safety · P1 User Request · P2 Current Execution State · P3 Relevant Knowledge · P4 Relevant Memory · P5 Historical · P6 Optional`.

**6. Context Compression** (3 cấp, giữ triết lý **Deterministic First → LLM Last**):
- Level 1 Deterministic: loại duplicate, metadata thừa, message cũ, merge fragments
- Level 2 Extractive: giữ phần liên quan
- Level 3 LLM compression: chỉ khi cần

#### 7. TASK-025 — Model Router
Provider Registry trả lời *"Model nào tồn tại?"*; Model Router trả lời *"Request này nên dùng model nào?"*
```
                Request
                   │
                   ▼
             Model Router
       ┌───────────┼───────────┐
       ▼           ▼           ▼
     Quality      Cost       Latency
                   │
                   ▼
             Model Selection
```

**8. Routing Policy** (VD yaml):
```yaml
routing:
  default: balanced
  policies:
    cheap:    { max_cost: 0.01 }
    fast:     { max_latency_ms: 2000 }
    quality:  { min_quality: 0.9 }
    local:    { providers: [ollama] }
```

**8.1 Model Capability** — Registry bổ sung metadata: `model_id, provider, context_window, input_cost, output_cost, latency_class, reasoning, coding, vision, tool_calling, structured_output, availability` → Router deterministic filter được.

**9. Fallback** — `GPT → timeout → DeepSeek → rate limit → Ollama`, NHƯNG phải tuân Policy; không tự ý đổi model nếu policy cấm.

**10. Model Router KHÔNG được thành God Object** — chia: `ModelRouter → ModelSelector · RoutingPolicy · CostEstimator · AvailabilityChecker · FallbackResolver · ModelHealth`. Router chỉ điều phối.

#### 11. TASK-026 — Planning Engine (nâng cấp lớn nhất Orchestrator)
Hiện `Planner → ExecutionPlan` nên thành:
```
Goal → Goal Analyzer → Task Decomposer → Dependency Analyzer
     → Capability Resolver → Risk Analyzer → Execution Planner → Execution Graph
```

**12. Task Decomposition** — VD "Review module authentication và viết test" → T1 Analyze → (T2 vuln, T3 missing tests) → T4 Write tests → T5 Run → T6 Report, với dependency T1→{T2,T3}→T4→T5→T6.

**13. Planning KHÔNG nhất thiết dùng LLM** (giữ offline-first): `Known workflow → Template planning → Rule planning → LLM planning`. Workflow Library có sẵn → KHÔNG gọi LLM. Task đơn giản → KHÔNG gọi LLM. Chỉ task phức tạp mới Planner LLM.

**14. Plan Validation** — ExecutionPlan phải validate trước Runtime: `Contract · Capability · Permission · Policy · Dependency · Resource · Cycle · Timeout`. VD T1→T2→T3→T1 → reject (circular dependency).

#### 15. TASK-027 — Execution Graph
ExecutionService hiện thiên về linear (Node1→2→3); M5 nâng thành DAG:
```
        A
      /   \
     B     C
      \   /
        D
```

**16. Graph Contract** — `ExecutionGraph · GraphNode · GraphEdge · Dependency · Condition · JoinPolicy · FailurePolicy`. VD nodes [analyze, test_backend, test_frontend, report] + edges analyze→{test_backend,test_frontend}→report.

**17. Graph State** — mở rộng State Service: `PENDING · READY · RUNNING · SUCCEEDED · FAILED · SKIPPED · CANCELLED · BLOCKED` — foundation cho parallel execution.

#### 18. TASK-028 — Parallel Scheduler
ResourceService: *Có thể chạy không?*; Scheduler: *Khi nào chạy?*; M5 thêm: *Task nào có thể chạy đồng thời?* VD Backend/Frontend test chạy parallel sau Analyze.

**19. Scheduler Architecture** — KHÔNG sửa ResourceService thành God Object:
```
Planning → Execution Graph → Graph Scheduler → Resource Service → Execution Service → State Service
```
| Thành phần | Trách nhiệm |
|------------|-------------|
| Graph Scheduler | dependency |
| Scheduler Service | thời điểm |
| Resource Service | resource |
| Execution Service | execution |
| State Service | state |

#### 20. M5 Execution Flow hoàn chỉnh
```
User → API → Normalizer → Rule Engine → Workflow Matcher → Memory Coordinator
  → Context Optimizer → Policy/Requirements → Model Router → Planner/Planning Engine
     → Execution Graph → Policy → Graph Scheduler → Resource Service
     → Execution Service → Agent → Capability → Tool
```
Model Router chỉ cần chạy khi request cần model; với workflow/template/rule đã biết, pipeline được rút gọn và không gọi LLM. Policy phải được kiểm tra trước model selection và trước execution.

#### 21. Tránh Pipeline quá dài (adaptive intelligence)
- **Request đơn giản**: `Request → Normalizer → Rule → Workflow → Execution`
- **Request cần knowledge**: `Request → Rule → Memory → Context → Execution`
- **Request phức tạp**: `Request → Rule → Memory → Context → Planning → Model Router → Graph → Execution`

#### 22. M5 Architecture Invariants (bổ sung INV-011..016)
| ID | Invariant |
|----|-----------|
| INV-011 | Memory Isolation — Agent không truy cập Memory implementation trực tiếp |
| INV-012 | Context Budget — Context không được vượt budget |
| INV-013 | Model Routing Policy — Model selection phải qua Routing Policy |
| INV-014 | Plan Validation — Execution Plan phải validate trước execution |
| INV-015 | Graph Acyclicity — Execution Graph không được circular dependency |
| INV-016 | Scheduler Separation — Scheduler không sở hữu Resource/Execution implementation |

#### 23. Test strategy (mỗi task)
`Unit → Contract → Integration → Architecture → E2E → Regression`.
- Memory Coordinator: 100 memories → retrieve → rank → budget 4K → expected selection
- Model Router: cheap policy → expected cheap model; quality policy → expected quality model; timeout → expected fallback
- Graph: `A→B→C` và `A→B, A→C, B/C→D` → verify execution order

#### 24. Thứ tự triển khai M5 (không máy móc 023→028)
```
Phase 1: TASK-023 Memory Coordinator → TASK-024 Context Optimizer   (cặp Memory→Context)
Phase 2: TASK-025 Model Router                                      (độc lập tương đối)
Phase 3: TASK-026 Planning Engine → TASK-027 Execution Graph → TASK-028 Parallel Scheduler (chuỗi phụ thuộc)
```

#### 25. Definition of Done cho M5
- **Intelligence**: Memory không truy cập trực tiếp từ Agent; Context có budget + priority; Model routing theo policy + có fallback; Planner tạo task graph; Graph hỗ trợ dependency + parallel; Scheduler không sở hữu Resource/Execution
- **Architecture**: INV-011→INV-016; AST enforcement; Contract purity; không circular dependency; không God Object
- **Testing**: Unit + Integration + Contract + Architecture + E2E + Regression + Performance benchmark
- **Observability**: mỗi execution đo được memory retrieval latency, context size, context compression, model selected, model fallback, planning latency, graph execution time, parallelism, queue time, resource usage

#### 26. Kết quả mong muốn sau M5
Trước M5: `User → Orchestrator → Planner → ExecutionPlan → Runtime`.
Sau M5: AIOS tách thành **Intelligence** (Memory / Context / Model Router / Planning / Graph) và **Runtime** (Execution), Intelligence điều phối Runtime. **Biến AIOS từ hệ thống "có Orchestrator" thành hệ thống có khả năng reasoning/orchestration thực sự** — mà **KHÔNG thay đổi triết lý**: Runtime-first, Contract-first, Deterministic-first, Policy-first, Event-driven chỉ hoạt động ở mức thông minh và quy mô cao hơn.

→ Kết quả: AIOS tự hiểu request, tự lấy đúng memory/context, tự chọn model theo policy, tự lập kế hoạch dạng task graph DAG và thực thi song song có dependency — dùng chung cho Runtime, Orchestrator và Harness (M6)

### M6 – AIOS Harness (P11)
> M6 Harness **không phải một tầng mới đứng trên AIOS**, mà là một **subsystem hỗ trợ AIOS kiểm thử, xác minh, quan sát và cải tiến chính nó**. Phù hợp xu hướng "harness engineering": harness là lớp kiểm soát context, tool access, state, verification, permissions, observability và evaluation quanh agent, thay vì chỉ là test runner.
> Sau M5, AIOS có pipeline `Request → Memory → Context → Model Router → Planning → Execution Graph → Runtime` nhưng thiếu câu hỏi: *"Làm sao AIOS biết execution đó đúng, tốt, an toàn và không làm hệ thống suy giảm sau mỗi thay đổi?"* M6 giải quyết điều đó. Harness **không thay Runtime**.

#### 1. Phạm vi M6 — 5 năng lực chính
Thay vì 8–10 loại Harness, M6 tập trung 5 năng lực (Experiment/Evolution dùng chung nền tảng này nhưng chưa thành scope lớn của M6):
```
M6 Harness
├── H1 — Harness Kernel
├── H2 — Execution Verification
├── H3 — Test & Simulation
├── H4 — Evaluation & Benchmark
└── H5 — Doctor & Readiness
```

#### 2. H1 — Harness Kernel (TASK-029)
Nền tảng chung — không để mỗi Harness tự tạo logger/trace/result/artifact/config/lifecycle riêng, mà tạo contract chung: `Harness → Context · Run · Event · Result · Artifact · Report`.

**Cấu trúc** `aios/harness/`: `contracts/` (harness, run, result, assertion, report) · `kernel/` (runner, registry, lifecycle, context) · `execution/` · `testing/` · `evaluation/` · `doctor/`.

**Harness Contract lifecycle**: `CREATED → PREPARING → VALIDATING → RUNNING → VERIFYING → COMPLETED`; nếu lỗi: `RUNNING → FAILED → DIAGNOSED`.

**HarnessRun**: mọi lần chạy có `HarnessRun` (run_id, harness, target, version, environment, started_at, status). Quan trọng để truy ngược: `Release → Harness Run → Execution Trace → Evaluation → Failure`.

#### 3. H2 — Execution Verification (TASK-030 — quan trọng nhất M6)
> Execution thành công ≠ Task thành công. VD: Agent "Đã sửa xong" + exit code 0, nhưng test thực tế fail. Harness phải kiểm tra **post-condition**.

**Verification Contract**: mỗi Execution có `Preconditions · Execution · Postconditions · Invariants · Evidence`. VD task "Viết test cho module config" → PRE: module tồn tại; POST: test file tồn tại + test chạy thành công + coverage ≥ 90%.

**Verification Pipeline**: `Execution → Collect Evidence → Deterministic Checks → Policy Checks → Tests → Evaluation → Verdict`. Verdict: `PASS · PASS_WITH_WARNING · FAIL · INCONCLUSIVE` (không chỉ success=true/false).

**Evidence Package** (audit/replay thay vì chỉ final output):
```
Evidence Package
├── request.json · normalized-request.json · plan.json
├── execution-graph.json · events.json
├── tool-results/ · test-results/ · evaluation.json
├── artifacts/ · verdict.json
```
**Replay**: Production Run → Trace → Replay → Simulation → Debug (không cần chạy lại Tool thật). Kết nối với Runtime State/Event/Audit (M1).

#### 4. H3 — Test & Simulation (TASK-031)
> Kiểm thử AIOS mà không cần thực hiện side effect thật.

**Test levels** (Harness điều phối, không thay pytest/vitest): Unit · Contract · Architecture · Integration · Workflow · Agent · Capability · Tool · Policy · Permission · E2E · Regression.
```
AIOS Test Harness → pytest · vitest · architecture tests · workflow simulation · agent evaluation
```

**Simulation Mode**: tận dụng `simulate` hiện tại — `aiagent harness test workflow.review --simulate` → Request → Orchestrator → Planner → Execution Graph → Fake Runtime → Fake Tool → Expected Result (không side effect).

**Scenario Definition** (không hard-code test):
```yaml
scenario:
  id: coding-review-001
  input: { request: "review authentication module" }
  environment: { mode: simulation }
  expect: { intent: coding, agent: coder, policy: allow,
            required_capabilities: [filesystem, python] }
  verification: { tests_pass: true, no_policy_bypass: true }
```
→ trở thành **Golden Scenario**.

**Failure Injection** (Chaos nhẹ): `faults: [{target: model, type: timeout}, {target: tool.python, type: failure}, {target: resource, type: exhausted}]` → kiểm tra Retry/Fallback/Recovery/Policy/Final state.

#### 5. H4 — Evaluation & Benchmark (TASK-032, TASK-033)
Phân biệt **Test** ("Có đúng điều kiện không?") vs **Evaluation** ("Chất lượng tốt đến mức nào?" — VD HTTP 200 vs answer relevance 0.91).

**Evaluation Model** (thứ tự, LLM Judge không mặc định): `Deterministic → Semantic → LLM Judge → Human → Composite`.

**Evaluation Suite**:
```yaml
suite:
  id: coder-v1
  dataset: coding-golden-v3
  metrics: [task_completion, correctness, policy_compliance, tool_accuracy, cost, latency]
  thresholds: { task_completion: 0.90, correctness: 0.85, policy_compliance: 1.0 }
```
**Trajectory Evaluation**: không chỉ Input→Output mà đánh giá cả trajectory (Decision → Tool A → Tool B → Recovery → Final Output). VD final đúng nhưng gọi sai tool → bị deny → retry → gọi đúng → đánh dấu `Final Correct / Trajectory Warning`. Thông tin giá trị cho Improvement Advisor.

**TASK-032 — Evaluation**: đánh giá output và trajectory theo suite, evaluator và thresholds; kết quả phải lưu được để tái lập.

**TASK-033 — Benchmark**: "AIOS phiên bản mới có tốt hơn cũ không?" — chạy 100 scenarios, theo dõi đồng thời Quality/Cost/Latency/Token/Failure Rate/Policy Violations (không chỉ score).

**Regression Gate**: Before Task success 91% → After 86% → **FAIL**. Quality +2% nhưng Cost +80% → WARNING/FAIL tùy policy. Eval làm quality gate chặn release khi regression vượt threshold.

#### 6. H5 — Doctor & Readiness (TASK-034)
Nâng cấp `aiagent doctor` + `aiagent arch-health` thành **AIOS Doctor Harness** (không tạo Doctor mới hoàn toàn).

**Doctor Architecture**: Architecture · Runtime · Workflow · Agent · Capability · Tool · Memory · Model · Policy · Registry · Performance · Security · Evidence. Mỗi Doctor trả về `PASS · WARNING · ERROR · UNKNOWN`.

**Readiness Score** (không chỉ 1 con số, phải có hard gates):
```
Architecture 100% · Contracts 98% · Tests 97% · Evaluation 91%
Security 95% · Performance 88% · Observability 96% · Overall 94.1%
```
Hard gate: `Policy violation > 0 → RELEASE BLOCKED` dù overall 99%.

#### 7. M6 Architecture
```
                         AIOS
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
        Runtime      Orchestrator       Harness
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                           Test          Eval          Doctor
                                            │
                                            ▼
                                        Evidence → Improvement
```
Harness **đọc/quan sát và gọi API**, không chui vào implementation của Runtime.

#### 8. Harness API
```
POST /api/v1/harness/run
GET  /api/v1/harness/runs/{id}
GET  /api/v1/harness/runs/{id}/evidence
POST /api/v1/harness/test
POST /api/v1/harness/evaluate
POST /api/v1/harness/benchmark
POST /api/v1/harness/doctor
GET  /api/v1/harness/readiness
```
CLI: `aiagent harness run | test | evaluate | benchmark | doctor | readiness | replay`.

#### 9. M6 Architecture Invariants (bổ sung INV-017..021)
> ⚠️ **Ghi chú đánh số**: M5 đã dùng INV-011..INV-016, nên M6 tiếp tục INV-017..INV-021 (không ghi đè INV-011..015 như bản nháp) để giữ ID invariant toàn cục duy nhất, tránh xung đột với enforcement test.
| ID | Invariant |
|----|-----------|
| INV-017 | Harness Isolation — Harness chỉ qua Runtime API / Orchestrator API, không chui vào RuntimeService implementation |
| INV-018 | Evidence First — mọi Harness Run phải tạo evidence có thể truy xuất |
| INV-019 | Verification Before Verdict — không `PASS` chỉ vì execution không exception |
| INV-020 | Evaluation Determinism — nếu dùng LLM Judge phải lưu model, prompt version, temperature, input, output, score để reproducible |
| INV-021 | Release Gate — regression nghiêm trọng phải có khả năng block release |

#### 10. M6 Task Breakdown (6 task)
| Task | Nội dung | Ưu tiên |
|------|----------|---------|
| TASK-029 | Harness Kernel + Contract + Registry + Run | ⭐⭐⭐⭐⭐ |
| TASK-030 | Execution Verification + Evidence + Replay | ⭐⭐⭐⭐⭐ |
| TASK-031 | Test Harness + Scenario + Simulation | ⭐⭐⭐⭐⭐ |
| TASK-032 | Evaluation Harness + Metrics | ⭐⭐⭐⭐⭐ |
| TASK-033 | Benchmark + Regression Gate | ⭐⭐⭐⭐ |
| TASK-034 | Doctor + Readiness | ⭐⭐⭐⭐⭐ |

#### 11. Thứ tự triển khai
```
TASK-029 → TASK-030 → ┬─ TASK-031 ─┐
                       └─ TASK-032 ─┘ → TASK-033 → TASK-034
```
(Kernel trước, rồi Verification song song với Test/Eval, rồi Benchmark, cuối cùng Doctor/Readiness)

#### 12. Definition of Done cho M6
AIOS thực hiện được `aiagent harness test --suite core` với 10 bước: Load scenarios → Run simulation → Capture trace → Validate execution → Evaluate result → Generate evidence → Compare baseline → Detect regression → Generate report → Return PASS/FAIL. Và `aiagent harness readiness` trả về tất cả PASS + Overall READY.

#### 13. M6 tạo vòng lặp quan trọng
```
AIOS Execute → Trace → Harness (Test/Evaluate) → Failure/Score
            → Advisor → Improvement → AIOS New Version → Harness
```
**Harness trở thành hệ thống kiểm chứng của AIOS**, không phải hệ thống đứng trên AIOS. M6 ưu tiên kiểm chứng cả **execution trajectory, tool usage, policy, state, evidence và post-condition** — không chỉ "test agent có trả lời đúng không". Nếu làm đúng, AIOS có thể **tự chứng minh một thay đổi trong chính nó không làm hệ thống tệ đi trước khi cho phép thay đổi đó hợp lệ**.

→ Kết quả: AIOS có subsystem kiểm thử/xác minh/quan sát/cải tiến chính nó (H1–H5), dùng chung Runtime + Core Intelligence (M5), không tạo hệ thống song song, không phá architecture (INV-017..021)

### M7 – Enterprise (P12)
> M7 **không biến AIOS thành hệ thống cloud/distributed khổng lồ ngay lập tức**. Mục tiêu: đưa AIOS từ **single-instance AIOS mạnh** thành **AIOS vận hành an toàn trong môi trường doanh nghiệp**. Enterprise chủ yếu giải quyết 7 vấn đề: `Identity · Multi-tenancy · Isolation · Distributed Execution · Governance · Security · Operations`.

#### 1. Mục tiêu tiến hóa
```
Sau M4: AIOS → Single Runtime
Sau M5: AIOS → Intelligent Memory/Context/Model Routing/Planning/Execution Graph
Sau M6: AIOS → Core Intelligence + Harness + Verification/Evaluation
M7:    AIOS Enterprise = Identity + Tenancy + Governance + Distributed Runtime + Isolation + HA + Audit
```

#### 2. M7 gồm 7 nhóm (Identity, Tenancy, Distributed Runtime, Distributed Scheduler, Governance, Security, Operations)
```
M7 Enterprise
├── E1 Identity & Access            (bắt buộc)
├── E2 Multi-Tenancy                (bắt buộc)
├── E3 Distributed Runtime          (nền tảng scale)
├── E4 Distributed Scheduler        (lease / failover)
├── E5 Enterprise Resource Governance (enterprise governance)
├── E6 Security & Data Isolation   (enterprise governance)
└── E7 Enterprise Operations        (vận hành production)
```

#### 3. E1 — Identity & Access (TASK-035 — Identity Foundation)
Hiện AIOS có Permission/Policy/Permission Broker nhưng permission thiên về `Execution → ask_scopes()`. Enterprise cần biết **"Ai đang yêu cầu?"** → đưa identity vào mọi request: `User → Identity → Tenant → Role → Permission → Policy → Execution`.

**Principal Model** (contract): `Principal = User | Service | Agent | Workflow | System`.
```yaml
principal: { id: user-123, type: user, tenant: company-a, roles: [developer] }
principal: { id: agent-coder, type: agent, tenant: company-a }  # Agent cũng có identity
```
Quyền không chỉ thuộc user; agent hành động qua chuỗi delegation → cần **composite principals + capability attenuation** thay vì chỉ kiểm tra request ban đầu.

**RBAC + ABAC** (không chỉ RBAC):
- RBAC: `Developer → filesystem.read, git.read`
- ABAC: `user.department == "IT" AND resource.environment == "development" AND action == "write" → allow`
- Hỗ trợ: Role · Attribute · Resource · Action · Environment · Tenant

#### 4. E2 — Multi-Tenancy (TASK-036 — Tenant Model, quan trọng nhất M7)
AIOS phải hiểu: `Organization → Tenant → Project → Workspace → Execution`. VD Company A có Project HR/Finance/IT.

**Tenant Boundary**: mọi object quan trọng có ownership: `Execution · Workflow · Agent · Memory · Artifact · Skill · Credential · Evaluation · Harness Run`. Phải enforce boundary ở: `API · Context · Memory · Registry · Runtime · Storage · Tool · Audit` — **không chỉ thêm `tenant_id` vào DB**.

**Memory Isolation** (đặc biệt quan trọng với AIOS): KHÔNG được `Tenant A Memory → Retriever → Tenant B`. Phải: `Tenant A → Memory Namespace A → Retriever A` và `Tenant B → Memory Namespace B → Retriever B`. Isolation phải bao phủ data, compute và credentials.

**Tenant Isolation Levels** (spectrum, không bắt buộc đồng nhất):
| Tier | Isolation |
|------|-----------|
| Development | Shared |
| Standard | Logical Isolation |
| Secure | Sandbox |
| Enterprise | Dedicated Runtime |

#### 5. E3 — Distributed Runtime (TASK-037 — Runtime Node)
Tách `RuntimeKernel` (1 process) thành `AIOS Control Plane → Runtime Nodes`: `Orchestrator → Runtime Router → Runtime-01 / Runtime-02 / Runtime-03`.

**Runtime Node Contract**: `node_id · capabilities · capacity · health · version · region · tenant_classes`.
```yaml
node: { id: runtime-vn-01, region: ap-southeast, capacity: {cpu: 32, memory: 64GB},
        capabilities: [python, docker, ollama] }
```

**Runtime Router**: Orchestrator KHÔNG tự chọn server — Router chọn theo `Tenant · Region · Capability · Capacity · Latency · Policy · Cost · Health`.

#### 6. E4 — Distributed Scheduler (TASK-038) + Execution Lease
M5 có Graph Scheduler + Resource Service; M7 mở rộng: `Graph Scheduler → Distributed Scheduler → Runtime Node`. Xử lý: queue · retry · node failure · lease · heartbeat · stale execution · rescheduling.

**Execution Lease** (nhờ State Service M1): `Execution → Lease Runtime-01`; Runtime-01 chết → `Lease expired → Scheduler → Runtime-02 → Resume Snapshot`.

#### 7. E5 — Enterprise Resource Governance (TASK-039 — Tenant Quota)
Không để 1 tenant tiêu hết Runtime.
```yaml
tenant: { quota: { concurrent_executions: 20, cpu: 8, memory: 16GB,
                   llm_tokens_per_day: 5M, storage: 100GB } }
```
**AI-specific Quota**: LLM calls · Tokens · Model cost · Tool calls · Execution time · Memory retrieval · Storage · Sandbox time.

**Cost Governance**: `Cost Estimator → Budget Policy → Execution → Actual Cost → Billing`. VD estimate $0.20 > budget $0.10 → DENY; hoặc estimate GPT $0.25 vs Ollama $0.01 → Route Ollama (kết hợp M5 Model Router + M7 Governance).

#### 8. E6 — Security & Data Isolation (TASK-040)
**Credential Manager** (Agent/Tool KHÔNG giữ credential trực tiếp): `Agent → Capability → Credential Broker → Scoped Credential → Tool`. Credential phải: tenant-scoped · project-scoped · capability-scoped · short-lived · audit được.

**Secret Isolation**: Tenant A (GitHub, Oracle) / Tenant B (GitHub, AWS) — Agent A không resolve được credential của B.

**Network Policy**: `Agent→Tool · Tool→Internet · Tool→Internal API · Runtime→DB · Runtime→Model Provider`. Default-deny rồi mở kết nối cần: `network: { deny: [metadata-service], allow: [github.com, api.openai.com] }`.

**Sandbox thật** (M2 chỉ mock): `Policy → Permission → Sandbox → Tool` (không bypass). Sandbox profile: filesystem read/write scoping, network on/off, cpu/memory/timeout.

#### 9. E7 — Enterprise Operations (TASK-041 HA + Audit + Recovery, TASK-042 Enterprise Operations + Dashboard)
**HA Runtime**: không SPOF (Single Runtime/DB/Queue). Tối thiểu Runtime Pool A/B/C.
**Health & Failover**: `Heartbeat → Health Monitor → Runtime unhealthy → Drain → Reschedule` (không kill mù quáng execution đang chạy).
**Control Plane / Data Plane**: chính thức hóa `CONTROL PLANE (API, Orchestrator, Registry, Policy, Scheduler, Tenant, Governance) → EXECUTION PLANE (Runtime Nodes, Worker Agents, Tools, Sandbox)`.
**Audit Enterprise**: M4 audit SQLite → `Audit Event → Structured Event → Central Audit Store → Immutable/Tamper-evident`. Audit trả lời Who/What/When/Which tenant/agent/workflow/tool/credential scope/policy/result.
**Enterprise Observability**: M6 Evidence + dimensions `tenant · project · user · agent · workflow · model · runtime · region` → Tenant Dashboard (executions, success rate, token, cost, policy violations, latency).
**TASK-042** gom HA + audit + metrics + health + backup + recovery + operational dashboard (không tạo quá nhiều service).

#### 10. M7 Architecture hoàn chỉnh
```
                    AIOS ENTERPRISE
            ┌───────────────────┴───────────────────┐
            │                                       │
      CONTROL PLANE                            GOVERNANCE
   ┌────────┼────────┐                    ┌─────────┼─────────┐
   │        │        │                    │         │         │
 API   Orchestrator Registry            IAM      Policy     Audit
   │        │        │                    │         │
   └────────┼────────┘                    └─────────┘
            │
      Runtime Router
   ┌────────┼────────┐
   ▼        ▼        ▼
Runtime-01 Runtime-02 Runtime-03
   │        │        │
Worker   Worker    Worker
   │        │        │
Capability Capability Capability
   │        │        │
 Tools    Tools     Tools
   │        │        │
Sandbox  Sandbox   Sandbox
```

#### 11. M7 Task Breakdown (8 task)
| Task | Nội dung | Ưu tiên |
|------|----------|---------|
| TASK-035 | Identity + Principal + RBAC/ABAC | ⭐⭐⭐⭐⭐ |
| TASK-036 | Multi-Tenancy + Tenant Boundary | ⭐⭐⭐⭐⭐ |
| TASK-037 | Distributed Runtime + Runtime Node | ⭐⭐⭐⭐⭐ |
| TASK-038 | Distributed Scheduler + Lease + Failover | ⭐⭐⭐⭐⭐ |
| TASK-039 | Quota + Cost + Resource Governance | ⭐⭐⭐⭐ |
| TASK-040 | Credential + Network + Sandbox Isolation | ⭐⭐⭐⭐⭐ |
| TASK-041 | HA + Audit + Recovery | ⭐⭐⭐⭐ |
| TASK-042 | Enterprise Operations + Dashboard | ⭐⭐⭐⭐ |

#### 12. Dependency
```
TASK-035 → TASK-036 → ┬─ TASK-037 ─┐
                       └─ TASK-040 ─┘ → TASK-038 → TASK-039 → TASK-041 → TASK-042
```
Identity + Tenant phải trước Distributed Runtime (nếu distributed trước rồi thêm tenancy sẽ phải sửa gần như toàn bộ execution boundary).

#### 13. M7 Architecture Invariants (bổ sung INV-022..INV-029)
> ⚠️ **Ghi chú đánh số**: M5 dùng INV-011..016, M6 dùng INV-017..021, nên M7 tiếp tục INV-022..INV-029 để giữ ID invariant toàn cục duy nhất, tránh xung đột với enforcement test.
| ID | Invariant |
|----|-----------|
| INV-022 | Identity First — mọi execution phải có Principal |
| INV-023 | Tenant Isolation — cross-tenant access deny mặc định |
| INV-024 | Credential Isolation — credential chỉ resolve trong authorized scope |
| INV-025 | Resource Fairness — tenant không vượt quota nếu không có policy override |
| INV-026 | Distributed Execution Safety — một execution chỉ một active lease tại một thời điểm |
| INV-027 | Audit Completeness — security-sensitive action phải có audit evidence |
| INV-028 | Sandbox Boundary — untrusted tool execution phải qua sandbox policy |
| INV-029 | Control Plane Isolation — tenant workload không truy cập Control Plane nội bộ ngoài API contract |

#### 14. Definition of Done cho M7
Identity (user/agent/service, RBAC, ABAC, delegation) · Tenancy (tenant/project/workspace, memory/artifact/workflow/credential isolation) · Distributed (Runtime Node/Registry/Router, lease/heartbeat/failover/resume) · Governance (quota/cost/rate limit/fairness/model policy) · Security (Credential Broker/Network Policy/Sandbox/Secret isolation/Audit) · Operations (HA/backup/recovery/health/metrics/tenant dashboard).

#### 15. Một request Enterprise chạy thế nào?
VD "Công ty A yêu cầu Agent Coder sửa repo": `User → Identity → Tenant A → Project X → Orchestrator → Policy → Memory Tenant A → Planning → Model Router → Execution Graph → Distributed Scheduler → Runtime Node 02 → Permission Broker → Credential Broker → Sandbox → Git Tool → Artifact → Evaluation → Audit → Tenant Dashboard`. Failover: Runtime-02 chết → Lease expired → Scheduler → Runtime-03 → Snapshot → Resume. Cross-tenant: Agent request memory Tenant B → Tenant boundary → DENY → Audit. Over-budget: Cost estimate > Budget → DENY/downgrade/ask.

#### 16. M7 không nên biến AIOS thành Kubernetes
AIOS **không tự xây** container orchestrator / VM manager / network overlay / distributed DB / service mesh / object storage / secret vault. AIOS chỉ định nghĩa **contract và governance**: `AIOS → RuntimeNode Contract → Kubernetes/Docker/VM/Bare Metal`; `AIOS Credential Broker → Vault/Cloud Secret Manager`. AIOS vẫn là **AI Operating System**, không thành cloud platform.

#### 17. Ranh giới M6 → M7 → M8
```
M5: "AIOS có thông minh không?"
M6: "AIOS có tự kiểm chứng được không?"
M7: "AIOS có vận hành an toàn ở quy mô doanh nghiệp không?"
M8: "AIOS có mở rộng thành hệ sinh thái không?"
M9: "AIOS có thể tự vận hành theo Goal không?"
```
M7 **không làm self-evolution** — governance-by-design, centralized visibility, continuous monitoring phải hoàn thiện trước khi AIOS tự đổi chính nó.

→ Kết quả: AIOS giữ nguyên lõi Runtime → Orchestrator → Workflow → Capability → Tool → Infrastructure, nhưng có thêm **Identity → Tenant → Governance → Distributed Runtime → Isolation → HA → Audit** để thành nền tảng triển khai cho nhiều team/doanh nghiệp mà không phá vỡ Architecture Invariants (INV-022..INV-029)

### M8 – Ecosystem (P13)
> M8 đưa AIOS từ **"một nền tảng có thể vận hành"** (M7) thành **"một hệ sinh thái có thể mở rộng bởi bên thứ ba"**. **M8 không biến AIOS thành marketplace trước tiên** — Core vẫn là Runtime + Orchestrator; Ecosystem chỉ là **lớp mở rộng bao quanh Core**.
> Đích cuối: *"Một developer bên ngoài AIOS có thể xây Agent / Skill / Capability / Tool / Workflow / Model Provider / Integration mà không cần sửa AIOS Core."*

#### 1. Mục tiêu chiến lược
```
Sau M7: AIOS = Core Runtime + Intelligence + Harness + Enterprise
M8 thêm:
                    AIOS
          ┌──────────┼──────────┐
       Core     Enterprise    Ecosystem
          └──────────┼──────────┘
              ┌───────┼───────┐
            SDK      Plugin   Extension
              │        │        │
           Agent     Tool    Workflow
           Skill    Model    Integration
```

#### 2. 7 trụ cột của M8
```
M8
├── E1 Public SDK
├── E2 Plugin System
├── E3 Extension Contracts
├── E4 Ecosystem Registry
├── E5 Developer Experience
├── E6 Marketplace / Distribution
└── E7 Compatibility & Certification
```
**E1–E4 = Core Ecosystem** (nền tảng mở rộng). **E5–E7 = hệ sinh thái bên ngoài**.

#### 3. E1 — Public SDK (TASK-043 — quan trọng nhất)
Biến `AIOS SDK 🔲` thành **public developer interface**. Developer KHÔNG import internal:
```python
# ❌ SAI
from aios_core.internal.runtime.service_x import ...
# ✅ ĐÚNG
from aios import Agent, Capability, Tool, Workflow
```
**SDK che giấu Core**: `Public SDK → Public Contracts → AIOS Runtime → Internal implementation`. Developer viết `class MyAgent(Agent)` mà không cần biết RuntimeKernel/ExecutionService/ResourceService/EventBus/StateService/PolicyService.
**SDK Components** (không expose internal service): `Agent · Capability · Tool · Skill · Workflow · Model · Memory · Context · Artifact · Event · Policy · Harness · Client`.

#### 4. E2 — Plugin System (TASK-044 — trái tim M8)
Plugin lifecycle phải tái sử dụng **Skills Manager lifecycle 10 states** từ M2/M4, không xây hệ thống lifecycle thứ hai: `RESOLVE → VALIDATE → INSTALL → ENABLE → DISABLE → UNLOAD → RELOAD → UPGRADE → ROLLBACK → REMOVE`. `DISCOVERED`, `LOADED` và `RUNNING` là các trạng thái quan sát/triển khai của plugin, không được tạo một state machine cạnh tranh.
**Plugin Contract**:
```yaml
plugin:
  id: github.integration
  version: 1.2.0
  aiOS: { min: 1.8.0, max: 2.x }
  provides: [capability: github.repository, tool: github.search, tool: github.create_pr]
  permissions: [repository.read, repository.write]
```
Plugin KHÔNG tự ý chạm Runtime/Registry/Database/Filesystem/Network — phải qua contract.
**Plugin Types**: Agent · Capability · Tool · Skill · Workflow · Model Provider · Memory · UI · Integration Plugin (VD `github.plugin`, `jira.plugin`, `oracle.plugin`, `ollama.plugin`, `openai.plugin`).

#### 5. E3 — Extension Contracts (TASK-045 — bảo vệ Core)
Phân biệt rõ: `Internal API (aios.core.internal.* ❌) · Public API (aios.sdk.* ✅) · Extension API (aios.extension.* ✅) · Experimental API (aios.experimental.* ⚠️)`.
**Contract Versioning**: plugin khai báo `requires: { capability_contract: ^2.0 }`; AIOS kiểm tra compatibility trước khi load. **Compatibility Matrix**: `Plugin A 1.2 → compatible · Plugin B 2.0 → compatible · Plugin C 1.0 → deprecated · Plugin D 3.0 → incompatible` — không để plugin crash Runtime lúc startup.

#### 6. E4 — Ecosystem Registry (TASK-046 — Registry v2)
Mở rộng Registry hiện tại thành `AIOS Ecosystem Registry`: Agents · Capabilities · Tools · Skills · Workflows · Models · Providers · Plugins · Integrations · Extensions. Lưu đủ: `identity · metadata · contract · permissions · dependencies · compatibility · security · capabilities · artifacts · publisher · signature` (không chỉ name/version).
**Discovery**: `aios search github` / `aios plugin search database` → trả `github.integration, oracle.integration, postgres.integration`. Orchestrator discovery: `User request → System Knowledge → Ecosystem Registry → Capability Discovery → Plugin`.
**MCP là adapter, không phải Core**:
```
AIOS Capability → Native Tool | MCP Adapter | REST API   (đúng)
AIOS → MCP → Everything                          (sai)
```
MCP = ecosystem protocol adapter (resources/prompts/tools), KHÔNG phải abstraction chính.

#### 7. E5 — Developer Experience (TASK-047 — AIOS Developer Kit)
Developer mới phải có thể: `aios create plugin github` / `aios create agent code-reviewer` / `aios create capability database` → sinh scaffold (`aios.plugin.yaml`, `src/plugin.py`, `src/agent.py`, `src/capability.py`, `tests/`, `README.md`, `pyproject.toml`).
**Local Development**: `aios dev` chạy plugin hot-reload trên Local Runtime (không cần cài vào production).
**Plugin Testing** (nối trực tiếp M6 Harness): SDK tự sinh Contract/Security/Permission/Compatibility/Behavior/Harness Tests → `aios plugin test` chạy Harness.

#### 8. E6 — Marketplace / Distribution (TASK-048 — Ecosystem Hub)
Chỉ làm **sau** Registry + SDK + Certification. Marketplace chứa Plugins/Agents/Skills/Tools/Workflows/Integrations/Models, NHƯNG **không phải source of truth**. Kiến trúc: `Marketplace → Registry → Package → Signature → Compatibility → Certification → Install`.
**Trust Model** (điểm M7 ∩ M8): `Download → Manifest validation → Signature verification → Dependency check → Permission analysis → Compatibility check → Security scan → Harness certification → Install`. Mỗi package có `publisher { id, signing_key }` — AIOS biết Publisher/Package/Version/Signature/Certification (không chỉ `pip install xxx`).

#### 9. E7 — Certification (TASK-049 — sức mạnh hệ sinh thái)
Plugin states: `COMMUNITY → VERIFIED → CERTIFIED → ENTERPRISE CERTIFIED`. VD `github.plugin ✓ Contract ✓ Security ✓ Permission ✓ Compatibility ✓ Harness ✓ Performance`.
**Harness là gate của Ecosystem** (M6 không tồn tại độc lập): `Plugin → Harness { Contract, Behavior, Security, Policy, Regression, Performance, Compatibility }` → nếu fail → `CERTIFICATION = FAIL`. Ecosystem càng mở, attack surface càng lớn → guardrails/tracing/evaluation là production component.
**Agent-to-Agent Ecosystem**: mở rộng Agent Contract. Hai kiểu: **Manager** (`Orchestrator → Agent A/B/C`) và **Handoff** (`Agent A → handoff → Agent B`). Nhưng handoff vẫn phải qua `Policy · Capability · Context · Identity` — không cho Agent tự ý phá Control Plane.
**Agent Contract**:
```yaml
agent:
  id: code-reviewer
  version: 2.1
  accepts: [code_review_request]
  produces: [review_report]
  capabilities: [filesystem.read, git.read]
  permissions: [repository.read]
```
**Workflow Ecosystem**: Workflow Library → `Workflow Ecosystem` (code-review, bug-fix, database-migration, release, security-audit, documentation, test-generation); workflow bên ngoài khai báo `requires: [coder, test-runner, git, harness]`, AIOS check dependency rồi mới chạy.
**UI Ecosystem**: plugin đăng ký `UI Extension Contract` (VD GitHub plugin thêm GitHub tab/panel/PR status) — KHÔNG sửa trực tiếp Dashboard source.

#### 10. Ecosystem Architecture
```
                    AIOS CORE
           ┌───────────┴───────────┐
     Public Contracts            SDK
           └───────────┬───────────┘
                  Extension API
        ┌──────────┬──────────┬──────────┐
      Plugins    Adapters   Extensions
        │          │          ├── UI
     Agent Tool  MCP        └── CLI
       Skill
        │
  Ecosystem Registry → Certification → Marketplace
```

#### 11. M8 Task Plan (7 task)
| Task | Nội dung | Kết quả |
|------|----------|---------|
| TASK-043 | Public AIOS SDK | Developer API |
| TASK-044 | Plugin Runtime | Plugin lifecycle |
| TASK-045 | Extension Contracts | Stable API |
| TASK-046 | Ecosystem Registry | Discovery |
| TASK-047 | Developer Kit | `aios create/dev/test` |
| TASK-048 | Ecosystem Hub | Distribution |
| TASK-049 | Certification | Trust ecosystem |
```
043 SDK → ┬─ 044 ─┐
            └─ 045 ─┘ → 046 Registry → 047 DevKit → 049 Certification → 048 Marketplace
```

#### 12. Definition of Done cho M8
Developer bên ngoài có thể: `aios create plugin jira → aios dev → aios test → aios certify → aios package → aios publish`; rồi trên AIOS khác: `aios install jira` → `Verify → Install → Register → Discover → Policy → Use` **không sửa một dòng code trong AIOS Core**. Đó là tiêu chí quan trọng nhất.

#### 13. Những gì KHÔNG làm trong M8 (scope guard)
❌ AIOS Cloud · ❌ SaaS billing hoàn chỉnh · ❌ Social network cho Agent · ❌ Public agent marketplace bắt buộc · ❌ Blockchain/package provenance phức tạp · ❌ Tự xây container orchestration · ❌ Tự xây distributed database · ❌ AIOS thay thế Kubernetes. Marketplace chỉ là **một consumer của Ecosystem infrastructure**, không phải mục tiêu cốt lõi.

#### 14. Ranh giới M5→M8 & kiến trúc chồng lớp
```
M5 — CORE INTELLIGENCE: "AIOS biết suy nghĩ và lập kế hoạch."
M6 — HARNESS:           "AIOS biết kiểm tra, đánh giá và chứng minh kết quả."
M7 — ENTERPRISE:        "AIOS biết vận hành an toàn ở quy mô doanh nghiệp."
M8 — ECOSYSTEM:         "Người khác có thể xây trên AIOS mà không cần sửa AIOS."
```
```
ECOSYSTEM   (SDK · Plugin · Marketplace · Agents · Tools · Workflows)
   ↓
ENTERPRISE  (IAM · Tenant · Security · HA · Governance · Audit)
   ↓
HARNESS     (Test · Eval · Verify · Replay · Evidence)
   ↓
CORE INTEL  (Planning · Memory · Reasoning · Model Router · Learning)
   ↓
AIOS CORE   (Runtime · Workflow · Agent · Capability · Tool · Infra)
```
**M8 làm biên AIOS mở hơn nhưng Core ổn định hơn** — không nhét thêm chức năng vào Core. Đặt **TASK-043 Public SDK + TASK-045 Extension Contracts** làm hai task quan trọng nhất; nếu thiết kế sai, toàn bộ Plugin/Marketplace về sau sẽ khóa chặt AIOS vào API nội bộ.

→ Kết quả: AIOS có hệ sinh thái mở rộng (SDK công khai, Plugin System tái dùng lifecycle M2/M4, Extension Contracts ổn định, Ecosystem Registry, Developer Kit, Marketplace, Certification) — developer bên thứ ba xây extension mà **không sửa Core**, Ecosystem kết nối chặt với Harness (M6) và Enterprise (M7)

### M9 – Autonomous (P14)
> M9 đưa AIOS từ **"nhận task và thực hiện task"** (M0–M8) thành **"tự phát hiện mục tiêu, lập kế hoạch dài hạn, tự thực hiện, tự kiểm chứng, tự phục hồi, tự học và tiếp tục hành động trong giới hạn Policy"**.
> Nhưng M9 **không** biến AIOS thành "AI tự do làm mọi thứ".
> ```
> Autonomous ≠ Uncontrolled
> Autonomous = Goal-driven + Bounded + Observable + Reversible + Evaluated
> ```
> Phù hợp cách các hệ thống agent hiện đại vận hành: agent chạy vòng lặp **plan → act → observe → adjust**, có stopping conditions và human checkpoints khi cần ([Anthropic](https://www.anthropic.com/research/trustworthy-agents?utm_source=chatgpt.com)).

#### 1. Vị trí M9 trong lộ trình
```
M0 Foundation → M1 Core Runtime → M2 Orchestrator → M3 Desktop → M4 Platform
→ M5 Core Intelligence → M6 Harness → M7 Enterprise → M8 Ecosystem → M9 Autonomous
```
Kiến trúc (M9 dùng M5–M8, không thay thế):
```
              ┌──────────────────────┐
              │     M9 AUTONOMOUS    │
              │ Goal → Plan → Act    │
              │ Observe → Learn      │
              │ Recover → Continue   │
              └──────────┬───────────┘
                         │
              ┌──────────▼──────────┐
              │   M5 INTELLIGENCE   │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │     M6 HARNESS      │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │    M7 ENTERPRISE    │
              └──────────┬──────────┘
                         ▼
                    AIOS CORE
```

#### 2. Mục tiêu thực sự của M9
- M8 trả lời: *"AIOS cho người khác xây thêm cái gì?"*
- M9 trả lời: **"AIOS có thể tự vận hành đến mức nào?"**
- VD user: `"Giữ hệ thống này ổn định và cải thiện nó."` → M9 biến thành vòng lặp `Goal → Understand → Observe → Detect → Prioritize → Plan → Execute → Verify → Learn → Next Goal → Continue`.

#### 3. Năm cấp độ Autonomy (A0–A4)
```
A0 — Reactive:       User → Request → AIOS → Result
A1 — Task Autonomous: fix test fail → find → plan → modify → test → retry → verify
A2 — Goal Autonomous: "giảm tech debt" → scan → prioritize → tasks → execute → evaluate
A3 — Long-Horizon:   "trong tuần cải thiện độ ổn định" → 7 ngày tự chia việc, không cần 1 conversation
A4 — Self-Improving: phát hiện "workflow X thường fail ở Y" → hypothesis → experiment → evaluation → candidate → approval → deploy (KHÔNG tự sửa Core production vô điều kiện)
```
A0–A4 là **năng lực của hệ thống**. Không nhầm với `LEVEL 0–5` ở §29, là **mức quyền được policy cấp cho từng môi trường/tenant/goal**; một hệ thống A3 vẫn có thể chỉ được vận hành ở LEVEL 1.

#### 4. TASK-050 — Autonomous Goal Engine
Nâng `Goal Manager + Task Queue + Goal Reporter` (M2/M4) thành **Autonomous Goal Engine**. Goal không còn `goal = "do X"` mà là contract:
```yaml
goal:
  id: improve-system-reliability
  objective: "Increase system reliability"
  success: { availability: ">99.9%", failure_rate: "<1%" }
  constraints: { max_cost: 100, max_duration: 7d }
  permissions: { filesystem: read-write, production: approval-required }
  autonomy: { level: A2 }
```

#### 5. Goal Lifecycle
```
PROPOSED → VALIDATING → APPROVED → PLANNING → EXECUTING → EVALUATING → COMPLETED
EXECUTING → BLOCKED → RECOVERY → REPLANNING → EXECUTING
EXECUTING → ESCALATED → HUMAN
```

#### 6. TASK-051 — Autonomous Planner
Từ `Request → Execution Plan` thành:
```
Goal → World State → Constraints → Available Capabilities → History → Plan
```
Plan phải có `assumptions · steps · success_conditions · rollback(enabled)`.

#### 7. Dynamic Replanning
Autonomous không coi plan ban đầu bất biến:
```
A → observe → B → unexpected → replan ┬─ C1
                                       ├─ C2
                                       └─ C3
```
OpenAI Agents SDK cũng phân biệt orchestration bằng code và model, cho phép hybrid — M9 nên dùng hybrid thay giao toàn quyền cho LLM ([OpenAI GitHub](https://openai.github.io/openai-agents-python/multi_agent/?utm_source=chatgpt.com)).

#### 8. TASK-052 — World Model
M9 cần abstraction mới **Autonomous World State** kế thừa `System Catalog + Knowledge Graph + System Knowledge + Observability + Memory`:
```
WORLD
├── System (services, agents, workflows, dependencies)
├── Runtime (active executions, resources, failures)
├── Goals
├── Tasks
├── Environment
├── Constraints
└── Historical State
```

#### 9. World State ≠ Memory
```
Memory  = những gì AIOS nhớ
World State = AIOS tin thế giới hiện tại như thế nào
```
Mỗi fact có `source · timestamp · confidence · freshness`:
```yaml
fact: { name: migration_status, value: pending,
        source: database, observed_at: 2026-08-14T20:00, confidence: 1.0 }
```

#### 10. TASK-053 — Autonomous Loop (trái tim M9)
```
┌─────────────────────────────┐
│       AUTONOMOUS LOOP       │
│  Observe ↓ Understand ↓    │
│  Decide ↓ Plan ↓ Policy ↓   │
│  Act ↓ Verify ↓ Learn ──────┘→ Observe
└─────────────────────────────┘
```

#### 11. Autonomy Governor (tham chiếu TASK-054)
Loop KHÔNG được `while True: agent.run()`. Phải qua **Autonomy Governor** quyết định: `CONTINUE · PAUSE · ASK_HUMAN · REPLAN · ROLLBACK · STOP` (xem §33 INV-030).

#### 12. TASK-054 — Autonomy Governor
Governor là architecture invariant (INV-030): **không autonomous action nào thực hiện ngoài Governor**.
```
Agent → Autonomy Governor → Policy → Permission → Capability → Tool
❌ Agent → Tool      ❌ Planner → Shell      ❌ Loop → Runtime side effect
```

#### 13. Autonomy Budget
```yaml
autonomy_budget:
  max_steps: 100
  max_llm_calls: 50
  max_cost: 10.00
  max_duration: 2h
  max_tool_calls: 200
  max_retries: 5
  max_parallel_agents: 4
```
Hết budget → `STOP` hoặc `ASK_HUMAN`.

#### 14. Risk Budget
```
Read → autonomous
Edit source → autonomous
Commit → approval
Push production → approval
Delete database → impossible / explicit approval
```

#### 15. TASK-055 — Autonomous Recovery
Từ `retry/fallback/report` (M4) thành:
```
Detect → Classify → Diagnose → Generate strategies → Score → Policy check → Execute → Verify
```
VD: Test failed → dependency issue? → repair dependency → rerun → nếu fail → Strategy B/C → Human escalation.

#### 16. Recovery Limits
KHÔNG `retry forever`. Phải có: `retry budget · failure fingerprint · circuit breaker · cooldown · escalation`.

#### 17. TASK-056 — Long-Horizon Execution
AIOS chạy được 30p/2h/8h/24h/nhiều ngày mà không phụ thuộc context window:
```
Goal → Execution Session → Checkpoint → Context Compaction → Persisted State → Resume
```
Structured persistent notes là kỹ thuật quan trọng cho long-running agents ([Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents?utm_source=chatgpt.com)).

#### 18. Autonomous Checkpoint
```
Checkpoint #17
Completed: ✓ analysis ✓ 12 files migrated ✓ tests 1–120
Current:   → fixing dependency injection
Pending:   - tests 121–150 - integration - arch review
```
Process chết → restart → load checkpoint #17 → continue.

#### 19. TASK-057 — Autonomous Memory
Nâng Memory Coordinator (M5) thành nhiều loại:
```
Working · Episodic · Semantic · Procedural · Failure · Goal Memory
```
VD Failure Memory: `When: Oracle migration · Failure: TIMESTAMP mismatch · Cause: timezone · Fix: FROM_TZ(...) · Confidence: 0.92`.

#### 20. Learning Loop
```
Execution → Evaluation → Failure/Success → Extract Lesson → Validate → Memory → Future Planning
```
Không ghi mọi thứ vào KB — phải `candidate → deduplicate → validate → confidence → promote`.

#### 21. TASK-058 — Autonomous Experimentation (→ A4)
```
Hypothesis → Experiment Design → Sandbox → Execute → Evaluate → Compare baseline → Accept/Reject
```
VD: `retry=3 insufficient → experiment retry=5 → success 91%→96% → candidate improvement`.

#### 22. Self-Improvement không thẳng Production
```
Production → Observation → Hypothesis → Sandbox → Harness → Evaluation → Approval/Auto-policy → Canary → Production
```
Đây là nơi M5+M6+M7+M9 kết hợp (INV-033).

#### 23. TASK-059 — Multi-Agent Autonomy
M9 tận dụng M8 Ecosystem:
```
Goal → Autonomous Planner → ┬ Research ┬ Coder ┬ Tester → Evaluator → Decision Maker
```
AIOS tự quyết `single vs parallel vs sequential vs hierarchical` — chỉ thêm complexity khi tạo giá trị đo được ([Anthropic Resources](https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf?utm_source=chatgpt.com)).

#### 24. Autonomous Delegation
```
Task A → Agent 1 (owner, deadline, budget, output contract)
Task B → Agent 2
Task C → Agent 3
```

#### 25. TASK-060 — Autonomous Evaluation
M6 Harness đã có Evaluation; M9 biến nó thành **decision mechanism**:
```
Evaluation { correctness · quality · cost · risk · progress · confidence } → Decision
Should I continue / retry / replan / stop / ask human?
```
Agent evaluation phải đánh giá cả trajectory và outcome ([Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents?utm_source=chatgpt.com)).

#### 26. Progress Estimator
```
Goal completion: 73%  Confidence: 0.88  Risk: Medium  Budget remaining: 42%
```
Nếu 3 iterations không tăng progress → `STUCK` → replan.

#### 27. TASK-061 — Advanced Stuck Detection
M4 stuck detection → M9 nâng cấp. STUCK signals: `repeated tool calls · repeated errors · no state change · no progress · oscillation · budget burn · contradictory plans`. VD `A → B → A → B` → oscillation detected → stop/replan.

#### 28. TASK-062 — Autonomous Scheduler
Từ `WHEN execute?` thành **Autonomous Scheduler** chủ động:
```
Every night: inspect failed workflows → evaluate memory quality → detect stale skills → run regression → analyze arch health
```
Proactive AIOS: `User ↔ AIOS → System → Observation → Goal → AIOS acts`; nếu risk cao → `Ask Human`.

#### 29. Autonomous Governance (Autonomy Level)
```
LEVEL 0 Observe only
LEVEL 1 Recommend
LEVEL 2 Execute read-only
LEVEL 3 Execute reversible changes
LEVEL 4 Execute bounded production changes
LEVEL 5 Fully autonomous within policy
```
Enterprise: `default_level: 2, production: 1, development: 4`.

#### 30. Human-in-the-loop → Human-on-the-loop
M7: `AI → Ask → Human → Continue`. M9: `AI → Execute → Monitor → Human observes → Intervene if needed` (human-on-the-loop). Nhưng action nguy hiểm vẫn **human-in-the-loop**.

#### 31. AIOS Architecture sau M9 (Autonomy Layer)
```
USER
 │
▼ AUTONOMY LAYER (Goal Engine · World Model · Planner · Governor · Recovery · Learning)
 │
▼ ORCHESTRATOR (Control Plane)
 │
▼ Runtime · Agents · Workflow → Capability → Tools → Infra
```
**Autonomy Layer không thay Orchestrator — nó định hướng Orchestrator** (Control Plane vẫn là Orchestrator).

#### 32. Điểm kiến trúc cốt lõi
```
❌ Autonomous Agent → Runtime
✅ Autonomy → Orchestrator → Runtime
```
Vì Orchestrator vẫn là Control Plane của AIOS; M9 chỉ bổ sung **Autonomy Control Layer** phía trên.

#### 33. M9 Architecture Invariants (bổ sung INV-030..INV-034)
> ⚠️ **Ghi chú đánh số**: M5 dùng INV-011..016, M6 INV-017..021, M7 INV-022..029, M8 không thêm. M9 tiếp tục **INV-030..INV-034** (không ghi đè INV-011..015 như bản nháp) để giữ ID invariant toàn cục duy nhất, tránh xung đột với enforcement test `backend/tests/test_architecture.py`.
| ID | Invariant |
|----|-----------|
| INV-030 | Autonomous Action Boundary — mọi autonomous action phải qua Autonomy Governor |
| INV-031 | Autonomy Bounded — autonomous execution phải có budget/limit (step/cost/duration/risk) |
| INV-032 | Long-running Resumable — execution dài hạn phải checkpoint/resume được |
| INV-033 | Self-Improvement via Harness — cải thiện tự thân phải qua Experiment → Harness → Evaluation → Evidence → Decision → Deploy |
| INV-034 | Autonomous Memory No Unverified Promote — autonomous memory không được tự promote thành Knowledge chưa kiểm chứng |

Đặc biệt **INV-033**: `AIOS: "tôi nghĩ cải thiện này tốt hơn" → ❌ deploy` phải thành `Hypothesis → Experiment → Harness → Evaluation → Evidence → Decision → Deploy`.

#### 34. M9 Task Plan (13 task)
| Task | Nội dung | Kết quả |
|------|----------|---------|
| TASK-050 | Autonomous Goal Engine | Goal contract + lifecycle |
| TASK-051 | Autonomous Planner | Dynamic plan |
| TASK-052 | World Model | World State ≠ Memory |
| TASK-053 | Autonomous Loop | plan→act→observe→learn |
| TASK-054 | Autonomy Governor | INV-030 gate |
| TASK-055 | Autonomous Recovery | circuit breaker |
| TASK-056 | Long-Horizon Execution | checkpoint/resume |
| TASK-057 | Autonomous Memory | Failure/Goal Memory |
| TASK-058 | Autonomous Experimentation | A4 self-improve |
| TASK-059 | Multi-Agent Autonomy | delegation |
| TASK-060 | Autonomous Evaluation | decision mechanism |
| TASK-061 | Advanced Stuck Detection | oscillation detect |
| TASK-062 | Autonomous Scheduler | proactive |
```
050 Goal → 051 Planner → 052 World → 053 Loop → 054 Governor
                                                    ├─ 055 Recovery
                                                    └─ 056 LongHorizon
057 Memory → 058 Experiment → 059 MultiAgent → 060 Eval → 061 Stuck → 062 Scheduler
```

#### 35. M9 chia 4 Phase
- **M9-P1 Autonomous Foundation**: TASK-050/051/052/053/054 → AIOS có Autonomous Loop an toàn
- **M9-P2 Long-running Autonomy**: TASK-055/056/057/061 → chạy goal dài hạn, recover, resume
- **M9-P3 Adaptive Autonomy**: TASK-058/060 → thử nghiệm, đánh giá, tự cải thiện có kiểm soát
- **M9-P4 Autonomous Ecosystem**: TASK-059/062 → tự chọn agent/plugin/workflow, vận hành theo lịch/trigger

#### 36. Definition of Done cho M9
Không đánh giá bằng "thông minh hơn" mà bằng capability test:
1. **Autonomous Task**: "Fix toàn bộ test fail" → discover→diagnose→plan→fix→test→recover→verify→report
2. **Long Horizon**: goal 100+ actions → checkpoint → restart → resume → finish
3. **Failure Recovery**: tool fail → detect→diagnose→alternative→retry→verify
4. **Stuck**: `A→B→A→B` → detect→stop→replan
5. **Budget**: `max_steps=20` → không vượt 20 actions
6. **Dangerous Action**: production deploy + `approval-required` → AIOS DỪNG
7. **Self Improvement**: hypothesis→experiment→evaluation→evidence→candidate (KHÔNG LLM-says-better→production)

#### 37. M9 Success Metric
```
AUTONOMY SCORE
Goal Success       91%   Goal Completion    87%   Recovery Rate      82%
Replan Success     79%   Stuck Avoidance    94%   Policy Compliance 100%
Budget Compliance 100%   Regression Safety  99%   Human Escalation    8%
```
Thêm `pass@1` / `pass^k` cho task autonomous quan trọng ([Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents?utm_source=chatgpt.com)).

#### 38. Nguyên tắc giữ nguyên & kết luận
M9 **không** thành "Claude Code clone". AIOS đã có Runtime/Workflow/Orchestrator/Capability/Tools/Memory/Knowledge/Policy/Scheduler/Resource/State/Artifact/Observability/Harness/Enterprise/Ecosystem — M9 tận dụng toàn bộ để tạo **Autonomy Layer** định hướng Orchestrator theo vòng lặp:
```
OBSERVE → THINK → PLAN → ACT → RESULT → VERIFY → EVALUATE → LEARN (→ OBSERVE)
```
> M5 = "AIOS có Intelligence"; M6 = "AIOS biết Intelligence có đúng không"; M7 = "AIOS dùng Intelligence an toàn trong Enterprise"; M8 = "người khác mở rộng AIOS"; **M9 = "AIOS tự vận hành theo Goal trong thế giới có trạng thái, giới hạn, chính sách, bằng chứng và khả năng phục hồi"**.
> 4 thành phần cốt lõi nhất M9: **Autonomy Governor + World Model + Long-Horizon Execution + Evaluation-driven Self-Improvement**.

→ Kết quả: AIOS có Autonomy Layer (Goal Engine, World Model, Planner, Governor, Recovery, Learning) vận hành theo Goal dài hạn, bounded bởi Policy/Budget/Risk,可逆 qua Checkpoint, tự kiểm chứng qua Harness (M6) và Enterprise (M7), mở rộng qua Ecosystem (M8) — enforced bởi 5 invariant mới INV-030..INV-034

### M10 – AIOS 1.0 (P15 — Productization + Stabilization + Certification)
> ✅ **DONE 2026-08-15** — 13/13 task (TASK-063..075), 5 phase hoàn tất; `aiagent conformance` → **AIOS 1.0 READY** (9/9 areas · 20/20 GS · 5/5 gates); full suite **1939 pass** + vitest 13+19; Constitution 1.0 (INV-001..034 frozen); 75 task toàn dự án. Chi tiết: `aios/progress/PROGRESS.md` + `reviews/M10-review.md`.
> M10 **không phải là "thêm nhiều feature cuối cùng"**. M10 = **Productization + Stabilization + Certification**: biến toàn bộ M0–M9 thành một AI Operating System có contract ổn định, runtime đáng tin cậy, autonomous bounded, ecosystem mở và đủ chuẩn để gọi là **AIOS 1.0**.
> ```
> M10 = Freeze Architecture, không phải Freeze Innovation.
> ```
> Sau M10: `AIOS 1.x` chỉ gồm bug/security/performance fixes, backward-compatible features, ecosystem extensions. Thay đổi fundamental architecture → **AIOS 2.0**. Xu hướng production agent hiện nay: tracing, guardrails, human-in-the-loop, resumable execution, tool-level enforcement phải là runtime component, không chỉ demo ([OpenAI GitHub](https://openai.github.io/openai-agents-js/guides/guardrails/?utm_source=chatgpt.com)).
```
M0–M4 nền móng · M5 Intelligence · M6 Harness · M7 Enterprise
M8 Ecosystem · M9 Autonomous · M10 AIOS 1.0
```
AIOS 1.0 phải chứng minh: **Stable · Reliable · Secure · Observable · Autonomous · Extensible · Compatible · Operable** — xây trên Core + Harness + Enterprise + Ecosystem + Autonomous.

#### 1. Mục tiêu & 8 trụ cột
```
M10
├── F1 Architecture Freeze
├── F2 Contract 1.0
├── F3 Runtime Hardening
├── F4 Autonomous Safety
├── F5 Reliability & Recovery
├── F6 Security & Governance
├── F7 Developer / Operator Experience
└── F8 Certification & Release
```

#### 2. M10 ≠ M11
> **M10 = Freeze Architecture, không phải Freeze Innovation.**
Sau M10: `bug fixes · security fixes · performance · backward-compatible features · ecosystem extensions`. KHÔNG: đổi Runtime contract / Agent model / Capability model / phá Plugin API. Muốn đổi fundamental → **AIOS 2.0**.

#### 3. F1 — Architecture Freeze

#### 4. TASK-063 — AIOS Architecture 1.0
Chốt kiến trúc 7 layers: `UI/SDK/API · Autonomy Control · Orchestrator Control Plane · Workflow/Agent/Capability · Runtime Kernel · Tools/State/Events · Infra`. Sinh:
```
docs/architecture/AIOS-1.0.md
docs/architecture/layer-model.md
docs/architecture/control-plane.md
docs/architecture/execution-plane.md
docs/architecture/autonomy.md
```
Kiến trúc cuối:
```
USER/SYSTEM → UI/SDK/API → AUTONOMY CONTROL (Goal/Planner/Governor/World)
   → ORCHESTRATOR (Control Plane) → Workflow/Agent/Capability
   → Runtime Kernel → Tools/State/Events → Infra
```

#### 5. AIOS Architecture Constitution 1.0
> ⚠️ **Ghi chú quan trọng (bản dựng này)**: bản nháp M10 liệt kê 15 "core invariant". Tuy nhiên tập invariant thực tế được **freeze tại M10 = toàn bộ INV-001..INV-034** (10 core M0–M4 + 6 M5 + 5 M6 + 8 M7 + 5 M9). Nếu chỉ giữ 15 sẽ **làm mất 19 invariant M5/M6/M7** đang được enforcement test (`backend/tests/test_architecture.py`) quản lý. Do đó Constitution 1.0 chính thức = **INV-001..INV-034**.
> **Vi phạm invariant = release blocker** (không còn warning).

**15 core principle (thematic, theo bản nháp M10) + canonical INV:**
| Core Principle | Canonical INV |
|---------------|---------------|
| Runtime Isolation | INV-001 |
| Capability Isolation | INV-002 |
| Workflow Independence | INV-003 |
| Tool Independence | INV-004 |
| Control Plane Isolation | INV-005 |
| Contract First | INV-006 |
| Policy First | INV-007 |
| Artifact First | INV-008 |
| Event Driven | INV-009 |
| Deterministic First | INV-010 |
| Autonomous Action Boundary | INV-030 |
| Bounded Autonomy | INV-031 |
| Durable Execution | INV-032 |
| Evaluation Before Improvement | INV-033 |
| Validated Memory Promotion | INV-034 |

**Các nhóm M5/M6/M7 (cũng thuộc Constitution 1.0, không được bỏ):**
- M5: INV-011 Memory Isolation · INV-012 Context Budget · INV-013 Model Routing Policy · INV-014 Plan Validation · INV-015 Graph Acyclicity · INV-016 Scheduler Separation
- M6: INV-017 Harness Isolation · INV-018 Evidence First · INV-019 Verification Before Verdict · INV-020 Evaluation Determinism · INV-021 Release Gate
- M7: INV-022 Identity First · INV-023 Tenant Isolation · INV-024 Credential Isolation · INV-025 Resource Fairness · INV-026 Distributed Execution Safety · INV-027 Audit Completeness · INV-028 Sandbox Boundary · INV-029 Control Plane Isolation

> Renumber 34 → 15 ID sạch (INV-001..INV-015) là breaking change (cần update `test_architecture.py` + mọi milestone + ADR-0004) → **deferred to AIOS 2.0** nếu cần.

#### 6. F2 — Contract 1.0

#### 7. TASK-064 — Public Contract Freeze (task quan trọng nhất M10)
AIOS freeze 10 contracts: `Agent · Capability · Tool · Workflow · Runtime · Event · Artifact · Plugin · Model · Memory`. Mỗi contract có: `name · version · schema · compatibility · lifecycle · deprecation · migration`.

#### 8. Semantic Versioning thật
```
Capability v1.2.0
 Patch  = bug fix
 Minor  = backward compatible
 Major  = breaking change
```
AIOS có: `compatibility checker · migration checker · deprecated API detector`.

#### 9. Contract Compatibility Matrix
```
aiagent contract-check
→ Runtime ✓ · Agent ✓ · Capability ✓ · Tool ✓ · Workflow ✓
  Plugin ⚠ deprecated v1 · Event ✓
Breaking changes: 0 · Warnings: 2
```

#### 10. F3 — Runtime Hardening

#### 11. TASK-065 — Runtime Production Hardening
9 services (State/Event/Execution/Resource/Scheduler/Policy/Permission/Context/Artifact) phải chứng minh **hoạt động đúng khi gặp lỗi thật**.

#### 12. Failure Matrix
Phải test: `Model chết · Tool chết · Agent chết · Process chết · Network mất · Database mất · Plugin lỗi · Worker timeout · Resource hết · Memory corruption · Checkpoint lỗi · Event consumer chết`.
Mục tiêu: `failure → detect → contain → recover → resume` (KHÔNG `entire execution lost`). Durable/resumable execution đặc biệt quan trọng vì restart từ đầu vừa tốn chi phí vừa mất trạng thái ([TechRadar](https://www.techradar.com/pro/trustworthy-ai-starts-with-surviving-production-failures?utm_source=chatgpt.com)).

#### 13. TASK-066 — Durable Execution 1.0
M9 có checkpoint/snapshot/resume → M10 biến thành **production-grade guarantee**:
```
Execution #A123: Node1✓ Node2✓ Node3✓ Node4 ← crash
Restart: load checkpoint → verify → resume Node4 (KHÔNG chạy lại 1–3 trừ khi policy yêu cầu)
```

#### 14. Exactly-once / At-least-once
```
Read operation        → safe retry
Idempotent write      → retry
Non-idempotent write  → approval / transaction / compensation
```
Phân loại này cực quan trọng cho Autonomous AIOS.

#### 15. F4 — Autonomous Safety

#### 16. TASK-067 — Autonomy Safety 1.0
M9 có Governor/Budget/Risk/Policy/Approval → M10 biến thành **mandatory runtime enforcement**:
```
Autonomous Agent → Action Proposal → Risk Classifier → Autonomy Governor
 → Policy Engine → Permission Broker → Capability → Tool   (không shortcut)
```

#### 17. Stop Anywhere
> **Mọi autonomous side effect phải có khả năng bị chặn tại boundary trước khi thực thi.**
```
Agent → Tool request → STOP   (phải được)
❌ Agent → tool → side effect
```
Guardrails ở cấp tool (pre/post mỗi invocation) bảo vệ tốt hơn chỉ check input/output đầu/cuối ([OpenAI GitHub](https://openai.github.io/openai-agents-js/guides/guardrails/?utm_source=chatgpt.com)).

#### 18. TASK-068 — Kill Switch
```
aiagent stop execution <id>
aiagent stop goal <id>
aiagent emergency-stop   # Autonomous loops STOP · New tasks STOP · New tool calls BLOCK · Pending approvals CANCEL · Running reversible ROLLBACK
```

#### 19. F5 — Reliability

#### 20. TASK-069 — Reliability Engineering
SLO: `Runtime availability · Execution success · Recovery success · Checkpoint durability · Policy enforcement · Event delivery · API availability`. Target: `Policy bypass = 0 · Lost execution = 0 · Checkpoint corruption = 0 · Unauthorized tool call = 0 · Contract-breaking release = 0` — những metric **không được phép trung bình hóa**.

#### 21. AIOS Reliability Score vs Release Gate
```
Runtime 99.98% · Execution 98.7% · Recovery 96.2% · Policy 100% · Architecture 100%
Contract 100% · Autonomy 94% · Harness 97% · Security 99%
```
Health 98% nhưng `Policy bypass = 1` → **Release FAIL**.

#### 22. F6 — Security & Governance

#### 23. TASK-070 — AIOS Security Baseline
Security baseline 1.0: `Identity · Authentication · Authorization · Secrets · Encryption · Audit · Plugin signing · Supply chain · Sandbox · Network policy · Data boundary`.

#### 24. Agent Identity & Delegation Chain
Agent = **principal có identity** (không chỉ object Python): `Agent → Identity → Delegation → Capabilities → Permissions`. Delegation chain: `User → Orchestrator → Coder → Test`, quyền con **≤ parent** (capability attenuation). Nghiên cứu governance runtime nhấn mạnh composite principals + attenuation + structured audit ([arXiv](https://arxiv.org/abs/2606.12320?utm_source=chatgpt.com)).

#### 25. Tamper-Evident Audit
`audit SQLite` → `Structured Evidence Ledger`: mỗi action `{who, what, when, why, policy, permission, input, output, artifact, decision, result}` + `previous_hash → current_hash` để phát hiện sửa audit history.

#### 26. F7 — Developer / Operator Experience

#### 27. TASK-071 — AIOS 1.0 Developer Experience
Gom CLI/Dashboard/Extension/REST/WebSocket/SDK thành UX thống nhất. Command tree:
```
aiagent run · chat · goal {create,list,pause,resume,stop} · agent · workflow · plugin
        · skill · capability · execution · harness · doctor · health · arch-health · upgrade · system
```

#### 28. `aiagent doctor` first-class
Kiểm tra Runtime/Contracts/Registry/Models/Memory/Knowledge/Filesystem/Sandbox/Tools/Plugins/Policies/Permissions/DB/Events/Scheduler/Autonomy/Harness/Enterprise → output `✓/⚠/✗ + Health: 94/100`.

#### 29. TASK-072 — AIOS Dashboard 1.0
Tổ chức tab: `Overview · Operations · Autonomy · Agents · Workflows · Knowledge · Memory · Harness · Enterprise · Ecosystem · System`. Đặc biệt **Execution Timeline** (Goal→Plan→Agent→Capability→Tool→Result→Evaluation) — tracing là thành phần quan trọng của agent runtimes hiện đại ([GitHub](https://github.com/openai/openai-agents-python/blob/main/docs/tracing.md?utm_source=chatgpt.com)).

#### 30. F8 — AIOS Test & Certification

#### 31. TASK-073 — AIOS 1.0 Certification Suite (task lớn nhất M10)
13 categories: `Unit · Integration · Contract · Architecture · Security · Policy · Harness · Autonomous · Recovery · Performance · Compatibility · Upgrade · Ecosystem`.

#### 32. Golden Scenarios (GS-001..GS-020)
`GS-001 simple chat … GS-020 emergency stop` (bao phủ chat/coding/workflow/tool fail/agent fail/policy deny/human approval/checkpoint-resume/autonomous goal/long-horizon/multi-agent/plugin install/incompat/upgrade/rollback/security violation/arch violation/memory learning/self-improvement/emergency stop). Mỗi release phải pass.

#### 33. AIOS Conformance
```
aiagent conformance → Architecture PASS · Contracts PASS · Runtime PASS
  Policy PASS · Security PASS · Autonomy PASS · Harness PASS · Enterprise PASS · Ecosystem PASS
→ Result: AIOS 1.0 READY
```

#### 34. TASK-074 — Upgrade & Migration 1.0
Hỗ trợ `0.x→1.0 · 1.0→1.1 · plugin v0→v1 · contract v0→v1 · workflow v0→v1` với `migration plan · backup · dry-run · validation · rollback`. Biến Upgrade Pipeline (M4) thành **release-grade migration engine**.

#### 35. TASK-075 — Performance & Cost + Model Independence
Đo `latency · throughput · LLM cost · tool cost · memory cost · storage · concurrency` + dashboard `Cost/Goal · Cost/Workflow · Cost/Agent · Cost/Tool · Cost/Success`. Model Provider Contract độc lập:
```
AIOS → OpenAI | Ollama | Mock | Other   (KHÔNG thành OpenAI wrapper)
```

#### 36. AIOS 1.0 Release Gates (5 gates)
```
Gate A Architecture: INV violations = 0
Gate B Security:     critical = 0, high = 0
Gate C Contract:     breaking compatibility = 0
Gate D Reliability:  critical scenario failures = 0
Gate E Autonomous:   policy bypass = 0, budget bypass = 0, kill-switch bypass = 0
```
Chỉ 1 gate fail → **AIOS 1.0 = NOT READY**.

#### 37. M10 chia 5 Phase
- **M10-P1 Freeze**: TASK-063 + TASK-064 → AIOS Architecture 1.0 + Contracts 1.0
- **M10-P2 Harden**: TASK-065 + TASK-066 + TASK-069 → Production-grade Runtime
- **M10-P3 Secure**: TASK-067 + TASK-068 + TASK-070 → Bounded Autonomous AIOS
- **M10-P4 Productize**: TASK-071 + TASK-072 + TASK-075 → Developer/Operator Edition
- **M10-P5 Certify**: TASK-073 + TASK-074 → AIOS 1.0 RC → Certification → AIOS 1.0

#### 38. Tổng hợp task M10 (13 task)
| Task | Nội dung | Vai trò |
|------|----------|---------|
| TASK-063 | Architecture Freeze | Kiến trúc |
| TASK-064 | Contract 1.0 | API stability |
| TASK-065 | Runtime Hardening | Reliability |
| TASK-066 | Durable Execution 1.0 | Recovery |
| TASK-067 | Autonomy Safety | Safety |
| TASK-068 | Kill Switch | Emergency |
| TASK-069 | Reliability Engineering | SLO |
| TASK-070 | Security Baseline | Security |
| TASK-071 | Developer Experience | DX |
| TASK-072 | Dashboard 1.0 | Operations |
| TASK-073 | Certification Suite | Quality |
| TASK-074 | Migration 1.0 | Upgrade |
| TASK-075 | Performance & Cost | Efficiency |

#### 39. AIOS 1.0 Reference Implementation
`examples/`: `simple-agent · coding-agent · autonomous-agent · enterprise-agent · plugin · workflow · multi-agent · long-running-goal` — mỗi cái chạy được `aiagent run examples/coding-agent`.

#### 40. AIOS 1.0 Golden Demo
User: *"Phân tích module X, tìm vấn đề, tạo kế hoạch sửa, thực hiện, chạy test, tự recover nếu fail, đánh giá và báo cáo."* → toàn bộ pipeline `Request→Normalizer→Rule→Workflow→Goal→Planner→Policy→Governor→Coder→Capability→Tools→Tests→Failure→Recovery→Replan→Verify→Evaluation→Evidence→Goal Complete`, Dashboard hiển thị execution trace. **Đây là AIOS 1.0 moment.**

#### 41. 10 năng lực checklist
```
1. Execute? 2. Orchestrate? 3. Reason/Plan? 4. Recover? 5. Resume?
6. Autonomous bounded? 7. Prove result? 8. Extensible? 9. Enterprise? 10. Stable under change?
```
Cả 10 = YES → AIOS vượt mức "agent framework", thực sự là **AI Operating System**.

#### 42. Nguyên tắc cứng: Không thêm Core feature
```
M10: BUILD NOTHING ── PROVE EVERYTHING → AIOS 1.0 CERTIFIED
```
M10 = milestone khó nhất về engineering nhưng ít feature mới nhất.

#### 43. Definition of Done cuối cùng
```
Architecture=FROZEN · Contracts=STABLE · Runtime=DURABLE · Policy=ENFORCED
Security=CERTIFIED · Autonomy=BOUNDED · Harness=PASS · Recovery=PASS
Ecosystem=COMPATIBLE · Upgrade=SAFE · Observability=COMPLETE · Documentation=COMPLETE
Golden Scenarios=PASS · Critical Bugs=0 · Architecture Viol.=0 · Policy Bypass=0
```
Và quan trọng nhất: `Core Runtime + Orchestrator + Intelligence + Harness + Enterprise + Ecosystem + Autonomous → ONE COHERENT SYSTEM`.
Sau M10: **không tạo M11 = thêm feature**; thay vào đó `AIOS 1.1 Compatibility · 1.2 Performance · 1.3 Ecosystem · 1.x Enterprise · 2.0 Architecture Evolution`.
> ⚠️ **AMEND 2026-08-16 (Issue #4)**: user duyệt tạo **M11 — Deterministic Artifact & Interaction Runtime** (P16) — milestone bổ sung sau M10, additive trên AIOS 1.0, giới thiệu INV-035 (xem §M11 bên dưới).
> ⚠️ **AMEND 2026-08-16 (Issue #7)**: user duyệt tạo **M12 — AIOS 1.1 Compatibility** (P17) — bước đầu của roadmap §43, KHÔNG thêm Core feature/invariant, INV-001..035 giữ nguyên (xem §M12 bên dưới).

→ Kết quả: AIOS 1.0 — một AI Operating System hoàn chỉnh, có kiến trúc bị freeze (INV-001..INV-034), contract ổn định (semantic versioning), runtime durable, autonomous bounded (Governor/Kill-Switch), secure (Identity/Audit/Tamper-evident), observable, có Certification Suite + Golden Scenarios + Conformance + Migration engine, chứng minh qua 10 năng lực và Golden Demo — đủ chuẩn gọi là **AIOS 1.0**

### M11 – Deterministic Artifact & Interaction Runtime (P16 — Creative/Asset/UI Engineering)
> ✅ **DONE 2026-08-16 (Issue #4)** — 6/6 task (TASK-078..083), 5 phase hoàn tất; full suite **2052 pass**; conformance **AIOS 1.0 READY** (10 areas + 6 gates, có verification INV-035); doctor healthy + arch-health 0 violations. 12 nâng cấp R1–R12 xong (P0 Verification Integrity → P1 Deterministic Visual Runtime → P2 Visual Observability → P3 Asset Capability Architecture + Creative/Vendor/Reference → P4 Ecosystem & DX). Proposal `docs/proposals/m11-creative-engineering.md` (review user 8.8/10, branch-independent). M11 giới thiệu **INV-035** (Core Invariant MỚI — không vi phạm INV-001..034): Constitution update (M11 amendment trên M10 Constitution) + Governance update + Conformance rule update (10 areas/6 gates) + Contract/Policy registry update + version bump. Chi tiết: `aios/progress/PROGRESS.md`.
> ```
> M10: AIOS can reliably execute logic.
> M11: AIOS can reliably execute AND verify logic + state + render + asset + interaction.
> ```
> M11 = **Deterministic Artifact & Interaction Runtime** — không phải "creative expansion". 12 nâng cấp R1–R12, roadmap 5 tầng. Nguồn evidence: xây dựng webgame Yuniebel's Cat (vanilla → Phaser 4, 158 files +13,527/−1; nâng cấp sprite sheet PNG + fx + parallax + transition, 88/88 test / 23/23 AC) — false-positive verification có thật (visual test "17/17 PASS" nhưng thực chất `toHaveScreenshot` bị skip), worker reimplement primitive (PNG encoder/seeded PRNG/vendor-hash) thay vì route tới skill có sẵn.

#### 1. Mục tiêu & 12 nâng cấp (R1–R12)
```
M11
├── P0  R2  INV-035 Verification Fail-Closed (CORE INVARIANT, ưu tiên #1)
├── P1  R3  RenderReplay / DeterministicHarness (FOUNDATION)
├── P2  R1  VisualEvidence / VisualRegressionProbe
├── P2b R10 UI State Contract (nền cho R1)
├── P3  R9  AssetPipeline Contract
│        R4  Asset Capability Registry (kind=asset)
│        R11 Capability Discovery & Routing (đóng gap "reuse vs reimplement")
├── P3b R6  Creative/Game domain trong Decision Pipeline
├── P3c R8  Vendor Integrity (độc lập Security Baseline)
├── P3d R12 Reference-Asset Understanding (vision ingest → structured description)
├── P4a R5  SkillDistiller (Ecosystem Extension)
└── P4b R7  Static Deploy (optional)
```

#### 2. INV-035 — Verification Fail-Closed (CORE INVARIANT)
> *Không một verification mechanism nào được phép chuyển trạng thái `UNKNOWN / NOT EXECUTED / MISSING EVIDENCE` thành `PASS`.*

**Verification State Model** (contract chính thức của R2):
- Terminal success duy nhất: `PASS`
- Terminal failure: `FAIL | ERROR | BLOCKED`
- **Non-terminal (KHÔNG được coi là success)**: `UNKNOWN | NOT_EXECUTED | MISSING_EVIDENCE | SKIPPED`
- Cấm chuyển đổi: `SKIPPED → PASS`, `UNKNOWN → PASS`, `MISSING_EVIDENCE → PASS`
- Áp dụng đồng nhất: visual test, E2E, artifact validation, security-check, contract-check, deployment verification
- Enforcement: `aiagent conformance` + Security Baseline + Contract-check; vi phạm = release blocker

#### 3. Dependency order (kiến trúc)
```
R2 → R3 → (R10 ∥ R1) → R9 → (R4 ∥ R11) → R6 → (R8 ∥ R12) → R5 → R7
```
- R3 nền cho cả R10 (UIState) và R1 (VisualEvidence) — chạy song song dưới Determinism
- R9 Asset Contract → R4 Registry ∥ R11 Discovery/Routing — cùng một architectural slice
- R8 độc lập Security Baseline, không phụ thuộc R11; R5 rút xuống Ecosystem Extension; R7 trì hoãn P4

#### 4. Roadmap 5 tầng & tasks
| Phase | Nội dung | Nâng cấp | Task | Trạng thái |
|-------|----------|----------|------|------------|
| P0 | Verification Integrity | R2 INV-035 + Verification State Model + conformance visual policy + CI fail-closed gate + retroactive audit | TASK-078 | `done` ✅ (12/12 AC — Verification Kernel + 10 areas/6 gates conformance) |
| P1 | Deterministic Visual Runtime | R3 RenderReplay/DeterministicHarness (record input timeline + seed → replay → assert pixel-stable) | TASK-079 | `done` ✅ (10/10 AC — rendering/ package) |
| P2+P2b | Visual Observability | R1 VisualEvidence (Screenshot + DOM Snapshot + Render State + Input Timeline + Seed + Pixel Diff — pixel-diff KHÔNG thành SLO sớm) + R10 UI State Contract (`UI State → Render → Screenshot`) | TASK-080 | `done` ✅ (10/10 AC — probe bắt state_diff scale 3→2) |
| P3 | Asset Capability Architecture (1 slice) | R9 AssetPipeline Contract (Sprite/Tileset/Map/Audio/Animation/UI Asset) + R4 Registry kind=asset + R11 Creative Matcher Discovery/Routing | TASK-081 | `done` ✅ (10/10 AC — registry wire skill thật) |
| P3b/c/d | Creative Domain + Vendor + Reference | R6 domain creative trong Decision Pipeline + R8 VendorIntegrity vào `aiagent security-check` + R12 Reference-Asset Understanding | TASK-082 | `done` ✅ (11/11 AC — pre-route 0.85 + vendor check #12 + reference) |
| P4a/b | Ecosystem & DX | R5 SkillDistiller (`aiagent skill distill <url>`) + R7 Static Deploy (`aiagent deploy --static <dir>`, optional) | TASK-083 | `done` ✅ (11/11 AC — **M11 HOÀN TẤT 6/6**) |

#### 5. Compliance & version
- Constitution: M11 amendment trên M10 Constitution (INV-035 thêm vào, INV-001..034 giữ nguyên frozen)
- Governance: policy registry thêm verification policy
- Conformance: rule update (skip/error normalization, missing reference detection)
- Contract 1.0: +AssetPipeline contract (R9)
- Version bump: AIOS 1.0 → M11 (minor — backward-compatible, additive)

### M12 – AIOS 1.1 Compatibility (P17 — Compatibility & Upgrade)
> 🔄 **IN-PROGRESS 2026-08-16 (Issue #7)** — roadmap §43: `AIOS 1.1 Compatibility · 1.2 Performance · 1.3 Ecosystem · 1.x Enterprise · 2.0 Architecture Evolution`.
> ```
> M10: AIOS can reliably execute logic.
> M11: AIOS can reliably execute AND verify logic + state + render + asset + interaction.
> M12: AIOS 1.1 — mọi thành phần (plugin/contract/workflow/SDK) tương thích 1.0→1.1, migration engine hoạt động thật.
> ```
> M12 = **AIOS 1.1 Compatibility** — KHÔNG thêm Core feature, KHÔNG thêm invariant (INV-001..035 giữ nguyên frozen). Chứng minh hệ thống có thể **nâng cấp an toàn 1.0→1.1** và **chạy backward-compatible**: plugin v0→v1 · contract v0→v1 · workflow v0→v1.

#### 1. Mục tiêu (5 nâng cấp C1–C5)
```
M12
├── P0  C1  Version & Compatibility Baseline — version bump 1.0→1.1 toàn hệ thống (contract/config/CLI/metadata) + Compatibility Matrix registry
├── P1  C2  Migration 1.0→1.1 thật — upgrade pipeline end-to-end trên dữ liệu thật (plan → backup → dry-run → validate → rollback)
├── P2  C3  Backward Compatibility — plugin v0→v1 · contract v0→v1 · workflow v0→v1 chạy được trên 1.1 + test chéo cũ→mới
├── P3  C4  Compatibility Conformance — mở rộng `aiagent conformance` (area `compatibility` + gate) KHÔNG phá 10 areas/6 gates hiện có
└── P4  C5  Docs & ADR — PLAN §M12 + ADR-0007 (compatibility policy) + migration guide 1.0→1.1
```

#### 2. Dependency order (kiến trúc)
```
C1 → C2 → C3 → (C4 ∥ C5)
```
- C1 là nền (version bump đồng bộ trước khi migration/test)
- C2 dựa trên Migration 1.0 (M10 TASK-074 — plan/backup/dry-run/validate/rollback đã có)
- C3 độc lập với C2 (test tương thích, không cần upgrade thật)
- C4 + C5 chạy song song ở cuối (bằng chứng + tài liệu)

#### 3. Roadmap & tasks
| Phase | Nội dung | Nâng cấp | Task | Trạng thái |
|-------|----------|----------|------|------------|
| P0 | Version & Compatibility Baseline | C1 version bump 1.0→1.1 + compatibility matrix | TASK-084 | `todo` |
| P1 | Migration 1.0→1.1 thật | C2 upgrade pipeline end-to-end (plan/backup/dry-run/validate/rollback) | TASK-085 | `todo` |
| P2 | Backward Compatibility | C3 plugin/contract/workflow v0→v1 trên 1.1 + test chéo | TASK-086 | `todo` |
| P3 | Compatibility Conformance | C4 area `compatibility` + gate (giữ 10 areas/6 gates) | TASK-087 | `todo` |
| P4 | Docs & ADR | C5 ADR-0007 + migration guide 1.0→1.1 + PLAN §M12 | TASK-088 | `todo` |

#### 4. Compliance & version
- INV-001..035 giữ nguyên frozen (KHÔNG thêm invariant mới)
- Contract 1.0 → 1.1: bump minor + compatibility matrix (backward-compatible)
- Version: AIOS 1.0 → **1.1** (minor — backward-compatible, additive)
- Conformance: +area `compatibility` (10 areas/6 gates hiện có không đổi)

### M13 – Harness Hardening & Behavioral Conformance (P18 — Trust & Production-Grade Harness)
> 📋 **PLANNED (chưa bắt đầu)** — bước tiếp theo SAU M12 (AIOS 1.1 Compatibility). KHÔNG sửa Runtime/Orchestrator (giữ INV-017..021). Mở rộng Harness từ "test/certify framework" → **trust layer tự xác minh (self-validating) + production-grade**.
> ```
> M10: AIOS can reliably execute logic.
> M11: AIOS can reliably execute AND verify logic + state + render + asset + interaction (INV-035 fail-closed).
> M12: AIOS 1.1 — nâng cấp an toàn 1.0→1.1, backward-compatible.
> M13: Harness tự chứng minh nó đang kiểm chứng ĐÚNG (meta-harness) + behavioral conformance under load/soak/failure + tách System Readiness ≠ Harness Trust.
> ```
> M13 = **Harness Hardening** — biến Harness thành **trust/gating infrastructure** thực thụ: structural → behavioral → temporal → load → soak → failure-recovery, có Meta-Harness chứng minh Harness "thất bại đúng cách" khi bị phá, và release gate yêu cầu CẢ System Readiness VÀ Harness Trust đều PASS.
>
> **Nguồn**: tự đánh giá độ harness 2026-08-16 (4/5 — Certified & Gated, chưa Autonomous) + đề xuất người dùng (5 ưu tiên: Meta-Harness / Behavioral Conformance / Harness Coverage / Self-Healing có permission boundary / tách Harness Trust ≠ System Readiness) + roadmap M12→M14.

#### 1. Bối cảnh — Harness là Trust Layer
```
AIOS Runtime
    │
    ├── Execute / Agent / Workflow / Artifact
    ▼
┌───────────┐
│  Harness  │  Verify · Test · Simulate · Evaluate · Benchmark · Doctor · Certify · Gate
└─────┬─────┘
      │  PASS / BLOCK / FAIL
      ▼
 Release / Stop
```
Điểm mạnh nhất: Harness KHÔNG chỉ là test framework — nó đã là **trust layer** đứng giữa Runtime và Release. M13 đưa tầng này lên mức **self-validating → self-improving → eventually self-healing** (giữ nguyên fail-closed + permission boundary + independent verification).

#### 2. Mục tiêu (5 ưu tiên từ đề xuất)
```
M13
├── P0  Behavioral Conformance — structural → behavioral → temporal → load → soak → failure-recovery
├── P1  Harness Coverage — Runtime/Agent/Workflow/State/Event/Artifact/Failure/Contract/Verification/Scenario + Doctor readiness scoring
├── P2  Meta-Harness — verify the verifier (false ±, malformed evidence, broken verifier, corrupted artifact, replay mismatch)
├── P3  Trust Separation — System Readiness ≠ Harness Trust; release gate = cả 2 PASS
└── P4  Docs & ADR — ADR Harness Trust invariant + behavioral conformance spec + PLAN §M13
```

#### 3. Dependency order
```
P0 → P1 → P2 → (P3 ∥ P4)
```
- P0 nền: behavioral conformance engine (execute N lần + replay + inject faults + compare evidence + deterministic check + regression gate)
- P1 độc lập trên P0: coverage instrumentation + readiness scoring
- P2 dựa trên P0/P1: meta-harness adversarial
- P3 + P4 song song cuối: tách trust + tài liệu

#### 4. Roadmap & tasks
| Phase | Nội dung | Ưu tiên | Task | Trạng thái |
|-------|----------|---------|------|------------|
| P0 | Behavioral Conformance — scenario S001 chạy 10k lần + replay + fault-inject + so sánh evidence + regression gate | Behavioral | TASK-089 | `todo` |
| P1 | Harness Coverage (9 nhóm) + Doctor Readiness scoring (Structural/Contract/Behavioral/Failure/Replay/Scenario/Production) | Coverage | TASK-090 | `todo` |
| P2 | Meta-Harness — cố tình sinh false positive/negative, malformed evidence, broken verifier, corrupted artifact, replay mismatch → chứng minh fail-closed | Meta | TASK-091 | `todo` |
| P3 | Tách System Readiness vs Harness Trust (2 score độc lập) + release gate yêu cầu cả 2 PASS | Trust | TASK-092 | `todo` |
| P4 | Docs & ADR — ADR Harness Trust + behavioral conformance spec + PLAN §M13 | Docs | TASK-093 | `todo` |

#### 5. Behavioral Conformance ladder (P0)
```
Structural        "Có cơ chế này không?"
    + Behavioral     "Hành vi đúng dưới kịch bản?"
    + Temporal       "Deterministic qua thời gian?"
    + Load           "Ổn định dưới tải?"
    + Soak           "Không leak/trễ sau chạy dài?"
    + Failure Recovery "Tự phục hồi đúng cách?"
```

#### 6. Harness Readiness scoring (P1) — ví dụ mục tiêu
```
Harness Readiness
├── Structural   100%
├── Contract      98%
├── Behavioral    91%
├── Failure       87%
├── Replay        96%
├── Scenario      84%
└── Production    62%
Overall: 89%   Status: READY
```

#### 7. Meta-Harness (P2) — verify the verifier
```
AIOS → Harness → Verification → Meta-Harness → Trust Verdict
```
Meta-Harness cố tình tạo: false positive · false negative · malformed evidence · broken verifier · skipped verification · corrupted artifact · inconsistent state · replay mismatch. Mục tiêu: chứng minh Harness **thất bại đúng cách** khi bị phá (quan trọng hơn hàng trăm unit test).

#### 8. Compliance & version
- INV-001..035 giữ nguyên frozen (KHÔNG thêm Core invariant mới trừ khi M13-P3 đề xuất **INV-036 Harness Trust** qua ADR riêng)
- Harness vẫn chỉ gọi Runtime qua public API (INV-017); evidence-first (INV-018); verification fail-closed (INV-035)
- Mọi đề xuất INV phải qua ADR + Constitution amend (không tự ý thêm)
- Version: AIOS 1.1 (không bump version ở M13 trừ khi có thay đổi contract công khai)

> **Forward roadmap (sau M13)**:
> - **M13.1** (tách P1) — Harness Coverage + Production/Soak sâu hơn
> - **M13.2** (tách P2) — Meta-Harness chuyên biệt + CI gate
> - **M14** — Closed-loop Remediation (Detect→Diagnose→Generate→Risk→Simulation→Meta-Verify→Human Approval→Permission Broker→Apply→Re-test→Certify) — **KHÔNG** cho Harness tự sửa tiêu chuẩn để tự PASS (anti-pattern cực nguy hiểm)
> - **M14.1** (phase P3 của M14) — Human Approval + Permission Broker boundary
> - **M14.2** (phase P3 của M14) — Safe Autonomous Repair (human-in-loop + permission gate)
> - **M15** — Autonomous Harness. Kiến trúc đích:
> ```
>                  ┌──────────────────────┐
>                  │       AIOS           │
>                  └──────────┬───────────┘
>                             │
>                  ┌──────────▼───────────┐
>                  │       Harness        │
>                  │ Verify/Test/Simulate │
>                  └──────────┬───────────┘
>                             │
>                  ┌──────────▼───────────┐
>                  │    Meta-Harness      │
>                  │  Verify the verifier │
>                  └──────────┬───────────┘
>                             │
>                  ┌──────────▼───────────┐
>                  │ Improvement Engine   │
>                  └──────────┬───────────┘
>                             │
>                     Risk / Simulation
>                             │
>                  ┌──────────▼───────────┐
>                  │ Permission Broker    │
>                  └──────────┬───────────┘
>                             │
>                       Human Approval
>                             │
>                  ┌──────────▼───────────┐
>                  │ Remediation Executor │
>                  └──────────┬───────────┘
>                             │
>                        Re-verify
>                             │
>                  ┌──────────▼───────────┐
>                  │ Certification Gate   │
>                  └──────────────────────┘
> ```

### M14 – Closed-loop Remediation (P19 — Self-Healing with Permission Boundary)
> 📋 **PLANNED (chưa bắt đầu)** — sau M13 (cần Meta-Harness + Trust Separation làm nền). Đóng vòng lặp tự phục hồi: phát hiện hỏng → chuẩn đoán → đề xuất sửa → mô phỏng xác minh → phê duyệt → áp dụng → tái kiểm → chứng nhận. **NGUYÊN TẮC SỐNG CÒN**: Harness **KHÔNG BAO GIỜ** tự nới lỏng/sửa tiêu chuẩn để tự PASS (anti-pattern). Mọi apply thực phải qua Permission Broker + Human Approval.
> ```
> M13: Harness tự chứng minh nó kiểm chứng ĐÚNG (trust layer).
> M14: Hệ thống tự ĐỀ XUẤT & KIỂM CHỨNG sửa chữa, nhưng apply phải có permission + human approval.
> M15: Vòng lặp chạy tự chủ (autonomous) trong boundary, continuous certification.
> ```
> Nguồn: đề xuất người dùng (Self-Healing có permission boundary + tách trust) + roadmap M13 closed-loop.

#### 1. Bối cảnh — Self-Healing có biên giới
```
Failed Run / Drift
      │
      ▼
┌──────────────┐
│  Detect +    │  evidence từ Harness/Meta-Harness
│  Diagnose    │
└──────┬───────┘
       │ localization + failure signature
       ▼
┌──────────────┐
│  Generate +  │  candidate fixes + risk score
│  Risk        │
└──────┬───────┘
       │ low/med/high
       ▼
┌──────────────┐
│ Simulation + │  chạy fix trong sandbox, verify qua
│ Meta-Verify  │  Harness + Meta-Harness (KHÔNG relax criteria)
└──────┬───────┘
       │ PASS?
       ▼
┌──────────────┐
│ Permission   │  broker + Human Approval
│ Broker       │
└──────┬───────┘
       │ approved?
       ▼
┌──────────────┐
│ Apply + Re-  │  apply thật + re-test + Certify + Audit
│ test+Certify │
└──────────────┘
```

#### 2. Mục tiêu (5 phase)
```
M14
├── P0  Detect & Diagnose — evidence → failure signature → component localization
├── P1  Candidate Generate + Risk Scoring — đề xuất sửa + phân loại rủi ro
├── P2  Simulation + Meta-Verify Gate — verify fix trong sandbox (KHÔNG nới lỏng tiêu chuẩn)
├── P3  Permission Broker + Human Approval + Apply + Re-test + Certify
└── P4  Docs & ADR — closed-loop policy + permission boundary + kill-switch
```

#### 3. Dependency order
```
P0 → P1 → P2 → P3 → (P4 docs song song cuối)
```
- P0 nền: thu thập evidence từ failed runs, localize
- P1 sinh candidate + risk
- P2 mô phỏng + meta-verify (cốt lõi an toàn)
- P3 gate + apply (cần human approval cho med/high risk)
- P4 tài liệu + ADR

#### 4. Roadmap & tasks
| Phase | Nội dung | Task | Trạng thái |
|-------|----------|------|------------|
| P0 | Detect & Diagnose — failure corpus, signature, localization | TASK-094 | `todo` |
| P1 | Candidate Generate + Risk Scoring (low/med/high) | TASK-095 | `todo` |
| P2 | Simulation + Meta-Verify Gate (verify fix, KHÔNG relax criteria) | TASK-096 | `todo` |
| P3 | Permission Broker + Human Approval + Apply + Re-test + Certify + Audit | TASK-097 | `todo` |
| P4 | Docs & ADR — closed-loop policy + permission boundary + kill-switch | TASK-098 | `todo` |

#### 5. Anti-pattern cấm (INV mới đề xuất)
```
CẤM: Harness tự sửa test/expectation để loại bỏ failure.
CẤM: Meta-Harness báo PASS khi verifier bị bypass.
CẤM: Apply tự động lên production cho med/high risk không có Human Approval.
=> Đề xuất INV-037 (Remediation Integrity) qua ADR riêng (M14-P4).
```

#### 6. Compliance & version
- INV-001..035 giữ nguyên; INV-036 (Harness Trust, từ M13-P3) nếu được duyệt; INV-037 (Remediation Integrity) đề xuất tại M14-P4 qua ADR.
- Mọi đề xuất INV phải qua ADR + Constitution amend.
- Version: AIOS 1.1 (không bump trừ khi thay đổi contract công khai).

### M15 – Autonomous Harness (P20 — Self-Validating, Self-Healing, Self-Improving)
> 📋 **PLANNED (chưa bắt đầu)** — đích cuối của harness track (sau M14). Harness tự vận hành vòng lặp detect→diagnose→fix→verify→apply→certify một cách tự chủ, PHÁT HIỆN VÀ TỰ SỬA các hỏng hóc thường quy trong boundary, có Trust Budget / Autonomy Levels theo risk, continuous certification, và kill-switch. Giữ nguyên: fail-closed + permission boundary + independent verification + human oversight cho high-risk.
> ```
> M13: trust layer (verify the verifier)
> M14: self-healing có permission + human approval
> M15: autonomous — vòng lặp chạy tự chủ, continuous improvement, human oversight chỉ cho high-risk
> ```
> Nguồn: đề xuất người dùng (Autonomous Harness — kiến trúc đích) + roadmap M14.

#### 1. Bối cảnh — Harness tự chủ
```
                 ┌──────────────────────┐
                 │       AIOS           │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │       Harness        │
                 │ Verify/Test/Simulate │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │    Meta-Harness      │
                 │  Verify the verifier │
                 └──────────┬───────────┘
                            │
                 ┌──────────▼───────────┐
                 │ Improvement Engine   │
                 └──────────┬───────────┘
                            │
                     Risk / Simulation
                            │
                 ┌──────────▼───────────┐
                 │ Permission Broker    │
                 └──────────┬───────────┘
                            │
                      Human Approval
                            │
                 ┌──────────▼───────────┐
                 │ Remediation Executor │
                 └──────────┬───────────┘
                            │
                       Re-verify
                            │
                 ┌──────────▼───────────┐
                 │ Certification Gate   │
                 └──────────────────────┘
```

#### 2. Mục tiêu (5 phase)
```
M15
├── P0  Autonomous Loop Orchestrator — điều phối vòng lặp không can thiệp thường quy
├── P1  Improvement Engine — học từ failure corpus, rank candidate fixes
├── P2  Continuous Certification — certify mọi change, low-risk không cần gate thủ công
├── P3  Trust Budget / Autonomy Levels — supervised / assisted / autonomous theo risk
└── P4  Docs & ADR — Autonomy Constitution + kill-switch + audit trail
```

#### 3. Dependency order
```
P0 → P1 → P2 → P3 → (P4 docs song song cuối)
```
- Phụ thuộc M14 (closed-loop + permission broker + human approval đã có)
- P0 orchestrator; P1 learning; P2 continuous cert; P3 autonomy levels; P4 constitution

#### 4. Roadmap & tasks
| Phase | Nội dung | Task | Trạng thái |
|-------|----------|------|------------|
| P0 | Autonomous Loop Orchestrator — schedule + coordinate remediation loop | TASK-099 | `todo` |
| P1 | Improvement Engine — failure corpus learning + candidate ranking | TASK-100 | `todo` |
| P2 | Continuous Certification — certify per-change, low-risk auto | TASK-101 | `todo` |
| P3 | Trust Budget / Autonomy Levels (supervised/assisted/autonomous) + kill-switch | TASK-102 | `todo` |
| P4 | Docs & ADR — Autonomy Constitution + audit trail + safe-stop | TASK-103 | `todo` |

#### 5. Autonomy Levels (P3) — ví dụ
```
Level 0  Supervised   — mọi apply cần Human Approval (mặc định an toàn)
Level 1  Assisted     — low-risk auto-apply, med/high cần approval
Level 2  Autonomous   — routine failures tự sửa + tự certify, high-risk vẫn cần human
Kill-switch           — dừng mọi autonomous action tức thì
```

#### 6. Compliance & version
- INV-001..037 giữ nguyên; INV-038 (Autonomy Boundary) đề xuất tại M15-P4 qua ADR.
- BẮT BUỘC: fail-closed + permission boundary + independent verification + human oversight cho high-risk KHÔNG bị gỡ bỏ bởi autonomy.
- Mọi đề xuất INV phải qua ADR + Constitution amend.
- Version: AIOS 1.1 → **1.2** (nếu có thay đổi contract công khai) hoặc giữ 1.1 nếu chỉ nội bộ harness.

### Tỷ trọng toàn dự án (theo thành phần)
| Thành phần | Tỷ trọng |
|-----------|----------|
| Runtime | 25% |
| Orchestrator | 20% |
| Workflow | 10% |
| Capability + Tool | 15% |
| Infrastructure | 10% |
| Observability | 8% |
| **Harness** | **7%** |
| SDK + Ecosystem | 5% |

> Harness chỉ khoảng **7%** tổng hệ thống — phản ánh đúng vai trò là **năng lực hỗ trợ (capability)** chứ không phải trung tâm. Khuyến nghị: hoàn thiện **Core Intelligence (M5)** trước khi làm M6 Harness, vì M5 cung cấp các năng lực chung mà Harness sẽ tận dụng (Memory Coordinator, Model Router, Planning Engine, Execution Graph) thay vì tự cài đặt logic riêng — giữ đúng triết lý "mọi subsystem dùng chung dịch vụ lõi".

## Verification (theo milestone)
- M0: **agent picker hiển thị AIOS Orchestrator** — chọn được, mọi request đi qua nó; **hard gate**: yêu cầu implement task chưa có spec+critique → agent từ chối; **bypass**: fix nhỏ → thực hiện nhưng LOG.md có entry `[bypass]` kèm lý do; **progress**: sau mỗi bước PROGRESS.md/LOG.md được cập nhật, TASK-xxx có đủ 8 file (spec, critique-1, critique-2, tasks, review, implementation, test, evaluation); **critique ×2**: task không thể hoàn thành khi chỉ có 1 critique
- M1: contract tests; đổi engine langgraph→mock không đổi workflow definition; simulation chạy không Docker/LLM; snapshot→kill→resume; **Policy pre-check**: request cần internet nhưng policy deny → reject trước khi execution; **Catalog search** không quét registry; **Knowledge Graph**: "agent nào dùng execute_code" trả lời O(1)
- M2: capability swap (execute_code: docker→mock) không đổi agent code; skill lifecycle test đủ 10 trạng thái; sandbox pool reuse + warm-start; **Offline-first**: tắt LLM (mock model 0 lần gọi) → 70–90% request vẫn routing đúng qua Rule Engine ("Generate API"→Coder, "medical question"→Doctor, "system status"→System Doctor); **Planner LLM chỉ gọi khi thật sự cần** (nhiệm vụ mở); **Orchestrator chỉ chọn capability không chọn tool trực tiếp**; **Permission Broker**: workflow cần network/shell → gom permission → user approve → mới chạy; **Failure Recovery**: agent lỗi → retry → fallback agent → report; **Isolation**: agent Worker không truy cập được registry trực tiếp (bị Permission Service + Policy Engine chặn); **Goal Manager**: goal "Xây AIOS" → tasks → progress persist qua phiên; **Task Queue**: pause/resume/reorder/priority hoạt động
- M3: event timeline realtime qua WebSocket; 9 lệnh extension end-to-end; artifact browser hiển thị đủ loại
- M4: upgrade giả lập fail → rollback; evaluator ghi score vào knowledge; resource manager reject workflow vượt budget; **Improvement Advisor** sinh đề xuất từ log/evaluation
- M5: Memory Coordinator inject context trong token budget; Model Router chọn model đúng policy (cost/latency/quality); Planning Engine sinh task graph; Execution Graph chạy DAG với join node; Parallel Scheduler thực thi song song có dependency
- **M6**: Harness Kernel (contract + registry + run) gọi Runtime API không sửa Runtime; Execution Verification kiểm tra post-condition + tạo Evidence Package + replay; Test Harness + Scenario + Simulation (--simulate, không side effect); Evaluation Harness + Benchmark (100 scenarios, regression gate chặn release); Doctor Harness + Readiness Score (hard gate policy violation); mọi Harness Run tạo evidence truy xuất được (INV-017..021)
- **M7**: Identity/Principal + RBAC/ABAC (TASK-035); Multi-Tenancy + Tenant Boundary + Memory Isolation (TASK-036); Distributed Runtime + Runtime Node/Router (TASK-037); Distributed Scheduler + Lease/Failover (TASK-038); Quota/Cost/Resource Governance (TASK-039); Credential/Network/Sandbox Isolation (TASK-040); HA/Audit/Recovery (TASK-041); Enterprise Operations + Dashboard (TASK-042); 8 invariant INV-022..029 enforced (tenant isolation, identity first, audit completeness)
- **M8**: Public SDK (TASK-043) che giấu Core (`from aios import Agent`); Plugin Runtime (TASK-044) lifecycle tái dùng 10-state M2/M4; Extension Contracts (TASK-045) stable API (Internal/Public/Extension/Experimental) + Compatibility Matrix; Ecosystem Registry (TASK-046) discovery (`aios search`) + MCP làm adapter; Developer Kit (TASK-047) `aios create/dev/test`; Ecosystem Hub (TASK-048) distribution tuân Trust Model; Certification (TASK-049) Harness gate + COMMUNITY→VERIFIED→CERTIFIED; **M8 KHÔNG thêm architecture invariant (tập invariant giữ nguyên tại M8 — M9 bổ sung INV-030..034)**
- **M9**: Autonomous Goal Engine (TASK-050) định nghĩa goal có success/constraints/permissions/autonomy level; Autonomous Planner (TASK-051) + Dynamic Replanning; World Model (TASK-052) tách World State khỏi Memory; Autonomous Loop (TASK-053) plan→act→observe→learn; Autonomy Governor (TASK-054) + Budget/Risk gate (INV-030); Autonomous Recovery (TASK-055) có circuit breaker; Long-Horizon (TASK-056) checkpoint/resume; Autonomous Memory (TASK-057) + Learning Loop; Experimentation (TASK-058) qua Sandbox/Harness (INV-033); Multi-Agent (TASK-059); Evaluation-driven (TASK-060); Stuck Detection (TASK-061); Scheduler (TASK-062); enforced INV-030..INV-034
- **M10**: Architecture Freeze (TASK-063) sinh `docs/architecture/*` + Constitution 1.0 (INV-001..INV-034 frozen, vi phạm = release blocker); Contract 1.0 (TASK-064) freeze 10 contracts + semantic versioning + `aiagent contract-check`; Runtime Hardening (TASK-065) + Durable Execution 1.0 (TASK-066) failure matrix + checkpoint/resume + idempotency; Autonomy Safety (TASK-067) + Kill Switch (TASK-068) mandatory enforcement + `emergency-stop`; Reliability (TASK-069) SLO + non-averaged gates; Security Baseline (TASK-070) + Agent Identity + tamper-evident audit; Developer Experience (TASK-071) + Dashboard 1.0 (TASK-072); Certification Suite (TASK-073) + Golden Scenarios GS-001..020 + `aiagent conformance`; Migration 1.0 (TASK-074); Performance & Cost (TASK-075); 5 release gates (Arch/Sec/Contract/Reliability/Autonomous) đều PASS → AIOS 1.0 READY
- **M11**: Verification Integrity (TASK-078) — R2 INV-035 fail-closed (Verification State Model PASS/FAIL/ERROR/BLOCKED + non-terminal UNKNOWN/NOT_EXECUTED/MISSING_EVIDENCE/SKIPPED, cấm SKIPPED→PASS, conformance visual policy, CI fail-closed gate); Deterministic Visual Runtime (TASK-079) — R3 RenderReplay/DeterministicHarness (record input timeline + seed → replay → assert pixel-stable); Visual Observability (TASK-080) — R1 VisualEvidence (Screenshot + DOM Snapshot + Render State + Input Timeline + Seed + Pixel Diff — metric sau evidence) + R10 UI State Contract (`UI State → Render → Screenshot`, debug bằng reasoning); Asset Capability Architecture (TASK-081) — R9 AssetPipeline Contract + R4 Registry kind=asset + R11 Discovery/Routing (đóng gap "reuse vs reimplement"); Creative Domain + Vendor + Reference (TASK-082) — R6 domain `creative` trong Decision Pipeline + R8 VendorIntegrity trong `aiagent security-check` + R12 Reference-Asset Understanding (vision ingest → structured description); Ecosystem & DX (TASK-083) — R5 SkillDistiller (`aiagent skill distill`) + R7 Static Deploy (`aiagent deploy --static`); INV-035 enforced (vi phạm = release blocker)
- **M12**: Version & Compatibility Baseline (TASK-084) — C1 version bump AIOS 1.0→1.1 đồng bộ (contract/config/CLI/metadata) + Compatibility Matrix registry; Migration 1.0→1.1 thật (TASK-085) — C2 upgrade pipeline end-to-end trên dữ liệu thật: plan → backup → dry-run → validate → rollback (tái dùng Migration 1.0 M10 TASK-074); Backward Compatibility (TASK-086) — C3 plugin v0→v1 · contract v0→v1 · workflow v0→v1 chạy trên 1.1 + test chéo cũ→mới; Compatibility Conformance (TASK-087) — C4 mở rộng `aiagent conformance` area `compatibility` + gate (KHÔNG phá 10 areas/6 gates hiện có); Docs & ADR (TASK-088) — C5 ADR-0007 (compatibility policy) + migration guide 1.0→1.1; INV-001..035 giữ nguyên frozen (KHÔNG thêm invariant mới)
- **M13**: Harness Hardening & Behavioral Conformance — Behavioral Conformance (TASK-089) P0 execute N lần + replay + fault-inject + evidence compare + regression gate; Harness Coverage (TASK-090) 9 nhóm coverage + Doctor readiness scoring; Meta-Harness (TASK-091) verify-the-verifier adversarial (false ±/malformed/broken/corrupted/replay-mismatch → fail-closed); Trust Separation (TASK-092) System Readiness ≠ Harness Trust, release gate cả 2 PASS; Docs/ADR (TASK-093) ADR Harness Trust + behavioral spec; INV-001..035 giữ nguyên, đề xuất INV-036 qua ADR riêng
- **M14**: Closed-loop Remediation — Detect&Diagnose (TASK-094) failure corpus + localization; Candidate Generate+Risk (TASK-095) low/med/high; Simulation+Meta-Verify Gate (TASK-096) verify fix KHÔNG relax criteria; Permission Broker+Human Approval+Apply+Re-test+Certify (TASK-097); Docs/ADR (TASK-098) INV-037 Remediation Integrity + kill-switch; anti-pattern: harness KHÔNG tự sửa tiêu chuẩn để tự PASS
- **M15**: Autonomous Harness — Loop Orchestrator (TASK-099); Improvement Engine (TASK-100) failure-corpus learning; Continuous Certification (TASK-101) low-risk auto; Trust Budget/Autonomy Levels+kill-switch (TASK-102); Docs/ADR (TASK-103) INV-038 Autonomy Boundary + Autonomy Constitution; giữ fail-closed + permission boundary + human oversight high-risk
- Xuyên suốt: pytest + contract tests CI; permission enforcement test (ask→deny); rule engine unit test với kết quả xác định trước

## Scope
- In: M0 (development foundation: VS Code agent + progress/log system) + 10 milestone (M1–M10), AIOS Orchestrator v1+v2 (Decision Pipeline 4 tầng offline-first, 22 module) + 3 assistant + system doctor, 6 tool types, skill 3 nguồn + lifecycle 10 trạng thái, SDK python + typescript, upgrade pipeline, evaluation framework, sandbox pool, policy engine, goal manager + task queue, system catalog, knowledge graph, **M5 Core Intelligence** (Memory Coordinator, Context Optimizer, Model Router, Planning Engine, Execution Graph, Parallel Scheduler), **M6 AIOS Harness** (5 năng lực H1–H5: Kernel, Execution Verification, Test & Simulation, Evaluation & Benchmark, Doctor & Readiness — subsystem dưới `aios/harness/`, không sửa Runtime/Orchestrator, không phá architecture INV-017..021), M7 Enterprise (Identity/Principal/RBAC-ABAC, Multi-Tenancy + isolation levels, Distributed Runtime + Runtime Node/Router, Distributed Scheduler + Lease/Failover, Quota/Cost/Resource Governance, Credential/Network/Sandbox Isolation, HA/Audit/Recovery, Enterprise Operations + Dashboard — INV-022..029), M8 Ecosystem (Public AIOS SDK + Plugin Runtime + Extension Contracts + Ecosystem Registry + Developer Kit + Ecosystem Hub + Certification — TASK-043..049, không thêm invariant), M9 Autonomous (Goal Engine/Planner/World Model/Loop/Governor/Recovery/Long-Horizon/Memory/Experimentation/Multi-Agent/Evaluation/Stuck/Scheduler — TASK-050..062, 5 invariant INV-030..034), M10 AIOS 1.0 (Architecture Freeze/Contract 1.0/Runtime Hardening/Durable Execution/Autonomy Safety/Kill Switch/Reliability/Security Baseline/Developer Experience/Dashboard/Certification/Migration/Performance — TASK-063..075, freeze INV-001..INV-034, không thêm invariant mới), **M11 Deterministic Artifact & Interaction Runtime** (Issue #4 — Verification Integrity INV-035/RenderReplay DeterministicHarness/VisualEvidence + UI State Contract/Asset Capability Architecture + Creative Domain + Vendor Integrity + Reference-Asset/SkillDistiller + Static Deploy — TASK-078..083, thêm INV-035, additive trên M10, không vi phạm INV-001..034), **M12 AIOS 1.1 Compatibility** (Issue #7 — Version & Compatibility Baseline C1/Migration 1.0→1.1 thật C2/Backward Compatibility C3/Compatibility Conformance C4/Docs & ADR C5 — TASK-084..088, KHÔNG thêm invariant, INV-001..035 giữ nguyên frozen)
- Excluded (sau M10, không thuộc v1): fine-tune model riêng, non-Local (cloud-only) deployment
