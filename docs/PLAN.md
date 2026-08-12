# Plan v6: AI Operating System — Runtime-First, Plugin-First, Offline-First, Milestone-Driven

> **Master Plan — Nguồn sự thật của dự án.** File này nằm trong repo, được git-tracked.
> Mọi phiên làm việc: BẮT ĐẦU = đọc file này + `aios/progress/`; KẾT THÚC = cập nhật `aios/progress/` + commit.

## TL;DR
Xây AIOS (AI Operating System) chạy local desktop: Runtime gồm các service nội bộ tách rời, Contract-First version hóa, DI container, capability discovery động, skill lifecycle đầy đủ, workflow snapshot/resume, prompt registry + evaluation framework, sandbox pool, AIOS SDK. AIOS Orchestrator dùng **Decision Pipeline 4 tầng offline-first** (Normalizer → Rule Engine → Workflow Matcher → Planner LLM): 70–90% request xử lý deterministic không cần LLM. LangGraph chỉ là một workflow engine có thể thay thế. **Phát triển dự án qua VS Code Custom Agent "AIOS Orchestrator" + hệ thống progress/log bắt buộc** (aios/progress/). Delivery theo 4 milestone, mỗi milestone là sản phẩm hoàn chỉnh dùng được.

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

### Vị trí trong milestones
- **M1 (P0.5–P2)**: Policy Engine core + System Catalog (index/search từ registry) + Knowledge Graph (đồ thị metadata) xây cùng kernel/registry
- **M2 (P3)**: Orchestrator v1 — Decision Pipeline đầy đủ (Normalizer, Rule Engine, Workflow Matcher, Planner LLM), Workflow Library, Goal Manager + Task Queue v1, Permission Broker, Failure Recovery, System Knowledge, Capability Router
- **M4 (P8)**: Orchestrator v2 — Improvement Advisor (self-improvement), Execution Supervisor nâng cao, Evaluation Collector đầy đủ, Goal Manager nâng cao (progress tracking + báo cáo)

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
│   └── progress/        # PROGRESS.md, LOG.md, STATS.md, tasks/TASK-xxx/ (spec, critique-1/2, tasks, review, implementation, test, evaluation)
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

### M5 – Enterprise Edition (tương lai, không làm v1)
Multi-user, RBAC, marketplace server, distributed runtime, remote agents, cluster GPU

## Verification (theo milestone)
- M0: **agent picker hiển thị AIOS Orchestrator** — chọn được, mọi request đi qua nó; **hard gate**: yêu cầu implement task chưa có spec+critique → agent từ chối; **bypass**: fix nhỏ → thực hiện nhưng LOG.md có entry `[bypass]` kèm lý do; **progress**: sau mỗi bước PROGRESS.md/LOG.md được cập nhật, TASK-xxx có đủ 8 file (spec, critique-1, critique-2, tasks, review, implementation, test, evaluation); **critique ×2**: task không thể hoàn thành khi chỉ có 1 critique
- M1: contract tests; đổi engine langgraph→mock không đổi workflow definition; simulation chạy không Docker/LLM; snapshot→kill→resume; **Policy pre-check**: request cần internet nhưng policy deny → reject trước khi execution; **Catalog search** không quét registry; **Knowledge Graph**: "agent nào dùng execute_code" trả lời O(1)
- M2: capability swap (execute_code: docker→mock) không đổi agent code; skill lifecycle test đủ 10 trạng thái; sandbox pool reuse + warm-start; **Offline-first**: tắt LLM (mock model 0 lần gọi) → 70–90% request vẫn routing đúng qua Rule Engine ("Generate API"→Coder, "medical question"→Doctor, "system status"→System Doctor); **Planner LLM chỉ gọi khi thật sự cần** (nhiệm vụ mở); **Orchestrator chỉ chọn capability không chọn tool trực tiếp**; **Permission Broker**: workflow cần network/shell → gom permission → user approve → mới chạy; **Failure Recovery**: agent lỗi → retry → fallback agent → report; **Isolation**: agent Worker không truy cập được registry trực tiếp (bị Permission Service + Policy Engine chặn); **Goal Manager**: goal "Xây AIOS" → tasks → progress persist qua phiên; **Task Queue**: pause/resume/reorder/priority hoạt động
- M3: event timeline realtime qua WebSocket; 9 lệnh extension end-to-end; artifact browser hiển thị đủ loại
- M4: upgrade giả lập fail → rollback; evaluator ghi score vào knowledge; resource manager reject workflow vượt budget; **Improvement Advisor** sinh đề xuất từ log/evaluation
- Xuyên suốt: pytest + contract tests CI; permission enforcement test (ask→deny); rule engine unit test với kết quả xác định trước

## Scope
- In: M0 (development foundation: VS Code agent + progress/log system) + 4 milestone (M1–M4), AIOS Orchestrator v1+v2 (Decision Pipeline 4 tầng offline-first, 22 module) + 3 assistant + system doctor, 6 tool types, skill 3 nguồn + lifecycle 10 trạng thái, SDK python + typescript, upgrade pipeline, evaluation framework, sandbox pool, policy engine, goal manager + task queue, system catalog, knowledge graph
- Excluded (M5 tương lai): multi-user, RBAC, marketplace server, distributed runtime, remote agents, fine-tune
