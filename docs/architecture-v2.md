# AIOS — Kiến trúc hệ thống (v2)

> **📌 TÀI LIỆU HIỆN HÀNH** — thay thế `docs/architecture.md` (bản cũ giữ làm lịch sử).
> Nguồn sự thật: `docs/PLAN.md` (master plan v6) + `aios/progress/PROGRESS.md` (trạng thái build thực tế).
> Cập nhật lần cuối: 2026-08-15 — phản ánh **M0–M9 done, M10 — AIOS 1.0 (todo)**.
> Định dạng: **markdown thuần** (bảng + danh sách + sơ đồ ASCII) — không dùng Mermaid, đọc được ở mọi nơi, không phụ thuộc renderer.

## 0. Cách đọc tài liệu này

- **Nguồn dữ liệu**: mọi trạng thái/số liệu test lấy từ `aios/progress/PROGRESS.md` (cập nhật 2026-08-15) và `docs/PLAN.md`; mọi module code đối chiếu `backend/src/aios_core/`.
- **Quy ước ký hiệu**: `✅` = đã build + test thật (kèm số tests); `🔲` = chưa làm (todo).
- **Thứ tự đọc đề xuất**: §1 (tổng quan) → §2 (3 plane) → §3 (Orchestrator) → §4 (luồng request) → §5–§10 (từng lớp/milestone) → §11 (tiến độ) → §12 (bất biến kiến trúc).
- **Bất biến kiến trúc (INV)**: xem §12 + `docs/adr/0004-architecture-invariants.md`; enforcement tự động qua `backend/tests/test_architecture.py` (AST) + runtime scanner `observability/arch_health.py`.

---

## 1. Kiến trúc tổng thể — 7 tầng lõi (M0–M5) + 4 lớp hệ sinh thái (M6–M9)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 1 — UI Layer (M0–M4)                                            │
│   Dashboard SPA ✅ · CLI aiagent ✅ · VS Code Extension ✅            │
│   REST API + WebSocket ✅ · AIOS SDK Python ✅ (M8)                   │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 2 — Runtime Kernel (M1)                                         │
│   RuntimeKernel (DI Container) → 9 services ✅                       │
│   Execution · Context · Event · Artifact · Permission · Policy ·    │
│   Scheduler · State · Resource                                       │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 3 — Workflow (M1)                                               │
│   Workflow Definition (YAML declarative) ✅ → Compilers ✅           │
│   (Mock + LangGraph stub) → Workflow Library + CLI simulate ✅       │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 4 — Orchestrator + Agents (M2–M4)                               │
│   AIOS Orchestrator — Control Plane ✅                                │
│   Worker Agents: General · Coder · Doctor · System Doctor ✅          │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 4.5 — Core Intelligence (M5)                                    │
│   Memory Coordinator ✅ · Context Optimizer ✅ · Model Router ✅       │
│   Planning Engine ✅ · Execution Graph ✅ · Parallel Scheduler ✅      │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 5–6 — Capability + Tools (M1–M2)                                │
│   Capability Registry + Prompt Registry ✅                            │
│   Tools: Python · Docker · REST · MCP · Shell · Git ✅                │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Tầng 7 — Infrastructure (M1–M4)                                      │
│   Model Providers (Mock/OpenAI/Ollama) ✅ · Memory 4 loại ✅          │
│   Knowledge Base + Graph ✅ · Sandbox Pool + Skills ✅                 │
│   Observability + Upgrade Pipeline ✅                                │
└──────────────────────────────────────────────────────────────────────┘

  Lớp mở rộng — song song, không nằm trong chuỗi chính:
    M6 — AIOS Harness ✅      (tự kiểm thử / xác minh / quan sát / cải tiến)
    M7 — Enterprise ✅        (identity · tenancy · governance · security · ops)
    M8 — Ecosystem ✅         (SDK · plugins · registry · marketplace · certification)
    M9 — Autonomous ✅        (định hướng Orchestrator — Autonomy → Orchestrator → Runtime)
```

> **Dependency một chiều (INV-004)**: Agent → Capability → Tool → Infrastructure. Runtime/Capability KHÔNG phụ thuộc ngược Infra. Enforcement: `tests/test_architecture.py` (AST) + `arch_health.py` (runtime scanner trên cây thật).

### 1.1 Cấu trúc package thật (`backend/src/aios_core/`)

| Nhóm | Package | Nội dung | Milestone |
|------|---------|----------|-----------|
| Kernel | `kernel/` | 9 services (execution, context, event, artifact, permission, policy, scheduler, state, resource) + `graph/` (Execution Graph) + `scheduler/` (Parallel Scheduler) | M1, M5 |
| Core | `core/` · `contracts/` · `semver.py` · `metadata.py` · `logging.py` · `healthcheck.py` · `config.py` · `container.py` | config, logging, metadata, healthcheck, DI container, contracts version hóa | M0–M1 |
| Orchestrator | `orchestrator/` | decision pipeline + advisor + supervisor + collector + goals/ (goal, task_queue, permission_broker, failure_recovery, reporting) | M2, M4 |
| Agents | `agents/` | General · Coder · Doctor · System Doctor (Worker Plane) | M2 |
| Intelligence | `memory/` (Memory Coordinator) · `context/` (Context Optimizer) · `models/` (Model Router) · `orchestrator/planning/` (Planning Engine) | 6 năng lực M5 | M5 |
| Capability/Tools | `capabilities/` · `tools/` · `skills/` · `sandbox/` · `prompts/` | registry, 6 tool types, skill lifecycle 10 state, sandbox pool, prompt registry | M1–M2 |
| Knowledge | `knowledge/` · `knowledge_graph/` | pipeline indexer→chunks→vectors→retriever + đồ thị metadata | M1 |
| Workflow | `workflow/` | definition + compilers + library + CLI simulate | M1 |
| Nền tảng | `observability/` · `upgrade/` · `api/` | metrics/doctor/arch-health, upgrade pipeline, FastAPI routers | M4 |
| Harness | `harness/` | H1 kernel · H2 execution verification · H3 test & simulation · H4 evaluation + benchmark · H5 doctor & readiness | M6 |
| Enterprise | `enterprise/` | identity, tenancy, runtime, scheduler, governance, security, operations, dashboard | M7 |
| Ecosystem | `plugins/` · `extension/` · `ecosystem/` | plugin runtime, extension contracts, registry/devkit/certification/marketplace | M8 |
| Autonomous | `autonomous/` | goal, planner, world, loop, governor, recovery, long_horizon, memory, stuck, experimentation, evaluation, multi_agent, scheduler | M9 |

---

## 2. Ba mặt phẳng — Control / Worker / Autonomy (M2 + M9)

```
┌────────────────────────────────────────────────────────────┐
│ AUTONOMY LAYER — định hướng (M9) ✅                         │
│   Goal Engine · Planner · World Model · Loop · Governor    │
│   Recovery · Long-Horizon · Memory 6 loại · Multi-Agent    │
│   Scheduler                                                │
└───────────────────────────────┬────────────────────────────┘
                                │  định hướng (INV-030: mọi action qua Governor)
                                ▼
┌────────────────────────────────────────────────────────────┐
│ CONTROL PLANE — quyết định (M2–M4) ✅                      │
│   AIOS Orchestrator: Decision Pipeline (4 tầng) ·         │
│   Agent Selector · Capability Router · Permission Broker ·│
│   Goal Manager + Task Queue · System Knowledge · Catalog  │
└───────────────────────────────┬────────────────────────────┘
                                │  chọn agent
                                ▼
┌────────────────────────────────────────────────────────────┐
│ WORKER PLANE — nghiệp vụ (M2) ✅                           │
│   General · Coder Pipeline · Doctor Pipeline + Safety     │
│   Layer · System Doctor                                   │
└───────────────────────────────┬────────────────────────────┘
                                │  thực thi
                                ▼
┌────────────────────────────────────────────────────────────┐
│ EXECUTION PLANE — thực thi (M1 + M5) ✅                    │
│   Runtime Kernel 9 services · Workflow Engine             │
│   (Mock/LangGraph) · Capabilities + Tools + Infra         │
└────────────────────────────────────────────────────────────┘

  Control → Execution: "Runtime API — request, không sở hữu" (INV-005)
```

**Nguyên tắc (INV-005, INV-016, INV-030)**: Orchestrator KHÔNG sở hữu Runtime Service — *request* Runtime qua Runtime API. Autonomy Layer KHÔNG thay Orchestrator — *định hướng* Orchestrator (`Autonomy → Orchestrator → Runtime`). Mọi action của Autonomy Loop phải qua Governor (INV-030).

---

## 3. Bên trong Orchestrator — module theo trạng thái (M2 + M4 + M5)

```
Request (CLI / API / UI)
    ▼
1. Normalizer ✅        — chuẩn hóa tham số, alias, macro (KHÔNG dùng LLM)
    ▼
2. Rule Engine ✅       — deterministic; 70–90% yêu cầu dừng tại đây, 0 token
    ▼
3. Workflow Matcher ✅ — tìm workflow/template/macro trong Workflow Library
    ▼
4. Planner LLM ✅      — chỉ khi cần (task mở / kết hợp workflow / sinh workflow mới)
    ▼
Execution Plan
```

| Nhóm | Module | Trạng thái | Ghi chú |
|------|--------|------------|---------|
| **Điều phối & thực thi** | Agent Selector | ✅ M2 | resolve intent → General/Coder/Doctor/System Doctor |
| | Capability Router | ✅ M2 | chỉ chọn Capability, không chọn Tool trực tiếp (INV-002) |
| | Resource Scheduler | ✅ M1 | trao đổi ResourceService — grant/queue/reject |
| | Execution Supervisor | ✅ M4 | track running từ bus, stuck detect, queue hook |
| | Failure Recovery | ✅ M2 | retry → fallback → report |
| | Context Coordinator + Context Optimizer | ✅ M1+M5 | budget + priority (INV-012) |
| | Memory Coordinator | ✅ M5 | Agent KHÔNG truy cập Memory trực tiếp (INV-011) |
| | Model Router | ✅ M5 | chọn model theo policy + fallback (INV-013) |
| **Quản trị & policy** | Policy Engine | ✅ M1 | pre-check bất khả bypass (INV-007) |
| | Permission Broker | ✅ M2 | ask_scopes, default-deny khi không có approver |
| | Skill Manager | ✅ M2 | lifecycle 10 states + zip/git/pip |
| | Goal Manager + Goal Reporter | ✅ M2+M4 | goal dài hạn nhiều phiên, progress tracking |
| | Task Queue | ✅ M2 | atomic dequeue, reorder, recover stale |
| | System Catalog | ✅ M1 | index + search toàn bộ registry, rebuild/is_stale |
| | System Knowledge | ✅ M2 | trả lời qua Catalog + Knowledge Graph (System Brain) |
| **Cải tiến & học hỏi** | Evaluation Collector | ✅ M4 | evaluator trên EvaluationStore — post-execution observer |
| | Improvement Advisor | ✅ M4 | 5 rules deterministic + suggestions (không tự áp dụng) |
| | Knowledge Graph | ✅ M1 | đồ thị Agent–Skill–Workflow–Capability–Tool–Artifact |
| | Observability | ✅ M4 | metrics · prompt history · profiler · doctor · arch-health |

---

## 4. Luồng xử lý một request

```
Người dùng (CLI / Dashboard / Extension / API)
    ▼
FastAPI — 9 routers (/api/v1)
    ▼
1. Normalizer          — chuẩn hóa tham số, alias (không LLM)
    ▼
2. Rule Engine         — intent rõ ràng? (chat/coding/doctor/system/skill/upgrade/diagnose)
    ▼
3. Workflow Matcher    — có workflow phù hợp trong Library?
    ▼
4. Planner LLM         — chỉ khi cần (sinh/kết hợp workflow)
    ▼
5. Policy pre-check    — allow / deny / ask? (INV-007 — bất khả bypass)
    ▼  (nếu ask → PermissionBroker.ask_scopes → Human Approval; default-deny)
6. ResourceService      — grant / queue / reject (FIFO)
    ▼
7. ExecutionService     — chạy ExecutionPlan (snapshot mỗi node · checkpoint · resume)
    ▼
8. AgentSelector        — resolve agent theo intent
    ▼
9. CapabilityRouter     — yêu cầu capability (KHÔNG gọi tool trực tiếp — INV-002)
    ▼
10. Tools               — Python · Docker · REST · MCP · Shell · Git
    ▼
11. Infra               — Model · Memory · KB · Sandbox · FS
    ▼
12. Kết quả / Artifact  → trả về người dùng
    └── (post-execution) Evaluation Collector → score → memory → Advisor
```

> Thứ tự ưu tiên: **1. Rule Engine (0 token) → 2. Workflow Library (tái sử dụng) → 3. Planner LLM (chỉ khi cần) → 4. Human Approval** (nếu policy yêu cầu). Evaluation = post-execution observer — KHÔNG nằm trong execution chain.

### 4.1 Hành trình một lệnh (module thật)

```
User → Kênh nhập lệnh → FastAPI → Orchestrator (1→4) → Policy pre-check
   → (cần approve? → PermissionBroker.ask_scopes → User xác nhận — default-deny)
   → ResourceService (grant/queue) → ExecutionService (chạy ExecutionPlan)
   → AgentSelector → Worker Agent → CapabilityRouter → Tool → Infra
   → Kết quả trả về User
   └── EventBus phát mọi lifecycle event → audit SQLite + metrics + evaluation_store
```

### 4.2 Trách nhiệm từng bước (module thật)

| # | Bước | Module thật | Trạng thái |
|---|------|-------------|------------|
| 1 | Normalizer | `orchestrator/normalizer.py` — chuẩn hóa, không LLM | ✅ TASK-010 |
| 2 | Rule Engine | `orchestrator/rule_engine.py` — deterministic, 70–90% dừng tại đây | ✅ TASK-010 |
| 3 | Workflow Matcher | `orchestrator/workflow_matcher.py` + Workflow Library | ✅ TASK-010 |
| 4 | Planner LLM | `orchestrator/planner.py` — chỉ khi cần, đếm `llm_calls` | ✅ TASK-010 |
| 5 | Policy pre-check | `PolicyService` + `ask_scopes` (Permission Broker) — bất khả bypass (INV-007) | ✅ TASK-004/012 |
| 6 | Resource | `ResourceService` — Grant/Queue/Reject + `acquire_slot_wait` | ✅ TASK-005/011 |
| 7 | Execution | `ExecutionService` — ExecutionPlan → nodes → snapshot/resume, emit `TOOL_STARTED/FINISHED`, `SNAPSHOT_SAVED`, `WORKFLOW_FAILED/CANCELLED` | ✅ TASK-005/021 |
| 8 | Agent Selector | `agents/registry.py` — resolve intent → worker agent | ✅ TASK-010/013 |
| 9 | Capability Router | `tools/registry.py` + `capabilities/` — agent không chạm tool trực tiếp | ✅ TASK-014 |
| 10 | Tools | 6 loại: Python (ast.parse, no-exec), Docker mock, REST validate, MCP, Shell (no-exec), Git mock | ✅ TASK-014 |
| 11 | Infra | Models (Mock/OpenAI/Ollama) · Memory 4 loại · KB · Sandbox Pool · Skills | ✅ TASK-006/007/015 |
| 12 | Observability | `metrics.py` · `evaluation_store` · `profiler` · `arch_health` · `advisor` | ✅ TASK-021/022 |

> **⚠️ Lưu ý thực tế**: Tools hiện ở mức **stub an toàn** (Python `ast.parse` không exec, Shell no-exec, Docker/Git mock) — đúng thiết kế v1: ưu tiên kiến trúc + test; thực thi thật đến khi policy/sandbox chín muồi.

---

## 5. Runtime Kernel — 9 services (M1: TASK-003→005)

| # | Service | Trách nhiệm | Câu hỏi |
|---|---------|-------------|---------|
| 1 | Execution Service | chạy ExecutionPlan → nodes → snapshot/resume, retry/cancel/timeout | CHẠY như thế nào? |
| 2 | Context Service | 6 loại context (System/User/Workflow/Agent/Execution/Shared), có inherit | |
| 3 | Event Service | pub/sub event bus + audit SQLite | |
| 4 | Artifact Service | lưu/quản lý artifact (checksum, metadata, version) | |
| 5 | Permission Service | policy allow/deny/ask trên 8 scopes | |
| 6 | Policy Service | Policy Engine core — pre-check trước mọi side effect (INV-007) | Có được chạy không? |
| 7 | Scheduler Service | lịch chạy workflow (cron/one-shot) | WHEN chạy? |
| 8 | State Service | state machine, checkpoint, snapshot/resume | |
| 9 | Resource Service | CPU/RAM/GPU/token/concurrency — Grant/Queue/Reject (FIFO) | CÓ THỂ chạy không? |

---

## 6. Core Intelligence — M5 (TASK-023→028, INV-011..016)

```
Request
   ▼
Memory Coordinator ✅   — Retrieve → Filter → Rank → Dedup → Compress → Prioritize → Inject
   ▼
Context Optimizer ✅    — Dedup → Compress → Priority (P0–P6) → Token Budget → Final Context
   ▼
Model Router ✅         — chọn model theo policy + fallback (availability tĩnh)
   ▼
Planning Engine ✅      — Goal → Decompose → Dependency → Capability → Execution Plan
   ▼
Execution Graph ✅      — Node/Edge/Dependency/Join/Failure Policy (DAG)
   ▼
Parallel Scheduler ✅   — Graph → Resource → Execution (KHÔNG sở hữu Resource/Execution)
   ▼
Runtime — Resource + Execution
```

| Năng lực | Trả lời câu hỏi | Task | Trạng thái |
|----------|-----------------|------|------------|
| Memory Coordinator | AIOS cần nhớ gì? | TASK-023 | ✅ 855 tests · 10/10 AC · INV-011 |
| Context Optimizer | Đưa gì vào lần chạy này? | TASK-024 | ✅ 896 tests · 11/11 AC · INV-012 |
| Model Router | Dùng model nào? | TASK-025 | ✅ 949 tests · 11/11 AC · INV-013 |
| Planning Engine | Làm những bước nào? | TASK-026 | ✅ 1003 tests · 11/11 AC · INV-014 |
| Execution Graph | Các bước phụ thuộc nhau thế nào? | TASK-027 | ✅ 1055 tests · 13/13 AC · INV-015 |
| Parallel Scheduler | Chạy khi nào, song song ra sao? | TASK-028 | ✅ 1086 tests · 12/12 AC · INV-016 |

---

## 7. AIOS Harness — M6 (TASK-029→034, INV-017..021)

> Subsystem `harness/` giúp AIOS tự kiểm thử/xác minh/quan sát/cải tiến chính nó. **Không sửa Runtime/Orchestrator — chỉ gọi qua API.**

| Năng lực | Nội dung | Task | Trạng thái |
|----------|----------|------|------------|
| H1 — Harness Kernel | contracts chung + lifecycle 8-state + registry + runner + evidence | TASK-029 | ✅ 1124 tests · INV-017/018 |
| H2 — Execution Verification | Preconditions/Postconditions/Verdict + Evidence Package + Replay | TASK-030 | ✅ 1210 tests · INV-019 |
| H3 — Test & Simulation | Scenario + Simulation Mode (FakeRuntime, FaultInjector) | TASK-031 | ✅ 1299 tests |
| H4 — Evaluation + Benchmark | Evaluation model + suite + trajectory + Regression Gate | TASK-032/033 | ✅ 1387/1450 tests · INV-020/021 |
| H5 — Doctor & Readiness | Doctor architecture 13 kinds + Readiness Score + hard gates | TASK-034 | ✅ 1521 tests |

---

## 8. Enterprise — M7 (TASK-035→042, INV-022..029)

> Đưa AIOS từ single-instance thành nền tảng vận hành an toàn quy mô doanh nghiệp — chỉ định nghĩa contract + governance, không biến thành cloud platform.

| Nhóm | Nội dung | Task | Trạng thái |
|------|----------|------|------------|
| E1 — Identity & Access | Principal (user/agent/service) + RBAC + ABAC + capability attenuation | TASK-035 | ✅ INV-022 |
| E2 — Multi-Tenancy | Tenant + TenantBoundary (deny-by-default) + MemoryNamespace | TASK-036 | ✅ INV-023 |
| E3 — Distributed Runtime | NodeRegistry + RuntimeRouter (tenant/region/capability/capacity/cost/health) | TASK-037 | ✅ INV-029 |
| E4 — Distributed Scheduler | single-active lease + failover/resume snapshot | TASK-038 | ✅ INV-026 |
| E5 — Resource Governance | QuotaManager (fairness) + CostGovernor (budget/cheaper route) | TASK-039 | ✅ INV-025 |
| E6 — Security & Isolation | CredentialBroker (scoped) + NetworkPolicy (default-deny) + SandboxBoundary | TASK-040 | ✅ INV-024/028 |
| E7 — Operations | CentralAuditStore (tamper-evident) + HealthMonitor + RecoveryManager + Dashboard | TASK-041/042 | ✅ INV-027 |

---

## 9. Ecosystem — M8 (TASK-043→049)

> Đưa AIOS thành hệ sinh thái mở rộng được bởi bên thứ ba. M8 KHÔNG thêm invariant mới (tập invariant giữ nguyên từ M7).

| Nhóm | Nội dung | Task | Trạng thái |
|------|----------|------|------------|
| E1 — Public SDK | `from aios import Agent, Tool, Capability, Workflow, Client`; độc lập, không import aios_core | TASK-043 | ✅ SDK Python |
| E2 — Plugin Runtime | lifecycle 10-state (reuse SkillState) + compat aios range + dependency check | TASK-044 | ✅ `plugins/` |
| E3 — Extension Contracts | Internal/Public/Extension/Experimental API + Compatibility Matrix | TASK-045 | ✅ `extension/` |
| E4 — Ecosystem Registry | Registry v2 + discovery (`aiagent ecosystem search`) | TASK-046 | ✅ `ecosystem/` |
| E5 — Developer Kit | scaffold (`aiagent plugin create`) | TASK-047 | ✅ `ecosystem/devkit.py` |
| E6 — Marketplace | Trust model + signature + HMAC (`aiagent marketplace publish`) | TASK-048 | ✅ `ecosystem/marketplace.py` |
| E7 — Certification | COMMUNITY → VERIFIED → CERTIFIED, Harness gate | TASK-049 | ✅ `ecosystem/certification.py` |

---

## 10. Autonomous — M9 (TASK-050→062, INV-030..034)

> `Autonomous = Goal-driven + Bounded + Observable + Reversible + Evaluated`. Autonomy Layer KHÔNG thay Orchestrator — định hướng Orchestrator (`Autonomy → Orchestrator → Runtime`).

| Phase | Task | Nội dung | Trạng thái |
|-------|------|----------|------------|
| P1 — Foundation | TASK-050 | Goal Engine — lifecycle 13 state | ✅ |
| P1 — Foundation | TASK-051 | Autonomous Planner — Goal→World→Capabilities→Plan, dynamic replanning | ✅ |
| P1 — Foundation | TASK-052 | World Model — WorldState + Fact (World ≠ Memory) | ✅ |
| P1 — Foundation | TASK-053 | Autonomy Loop — Observe→Understand→Decide→Plan→Policy→Act→Verify→Learn | ✅ |
| P1 — Foundation | TASK-054 | Autonomy Governor — CONTINUE/PAUSE/ASK/REPLAN/ROLLBACK/STOP + 7 budget | ✅ INV-030/031 |
| P2 — Long-running | TASK-055 | Autonomous Recovery — fingerprint + circuit breaker + cooldown | ✅ |
| P2 — Long-running | TASK-056 | Long-Horizon — ExecutionSession + Checkpoint + resume | ✅ INV-032 |
| P2 — Long-running | TASK-057 | Autonomous Memory — 6 loại + Learning Loop | ✅ INV-034 |
| P2 — Long-running | TASK-061 | Advanced Stuck Detection — 7 signals | ✅ |
| P3 — Adaptive | TASK-058 | Experimentation — Hypothesis→Sandbox→Evaluate→Accept/Reject (qua Harness) | ✅ INV-033 |
| P3 — Adaptive | TASK-060 | Autonomous Evaluation — 5 rules + ProgressEstimator | ✅ |
| P4 — Ecosystem | TASK-059 | Multi-Agent — single/parallel/sequential/hierarchical + delegation | ✅ |
| P4 — Ecosystem | TASK-062 | Autonomous Scheduler — proactive triggers (interval/daily) | ✅ |

---

## 11. Tiến độ milestone — M0..M10

```
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 🔲
✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   (AIOS 1.0 — todo)
```

| Milestone | Mô tả | Trạng thái | Số liệu (theo PROGRESS.md 2026-08-15) |
|-----------|-------|------------|----------------------------------------|
| M0 | Development Foundation — agents + progress system | ✅ done | 4 agents, hard gate |
| M1 | Core Runtime — kernel 9 services, models, memory, knowledge, workflow, capability, catalog | ✅ done | 428 tests · 95.76% |
| M2 | Developer Edition — orchestrator v1, assistants, tools, skills, sandbox, INV-001..010 | ✅ done | 669 tests · 95.51% |
| M3 | Desktop Edition — REST+WS API, Dashboard SPA, VS Code Extension | ✅ done | 689 pytest + 12 + 19 vitest |
| M4 | Platform Edition — upgrade pipeline, observability, orchestrator v2 | ✅ done | 809 tests · 94.92% |
| M5 | Core Intelligence — memory/context/model/planning/graph/scheduler, INV-011..016 | ✅ done | 1086 tests · 95.22% |
| M6 | AIOS Harness — H1..H5, INV-017..021 | ✅ done | 1521 tests · 95.35% |
| M7 | Enterprise — E1..E7, INV-022..029 | ✅ done | 1560 tests · 95.05% |
| M8 | Ecosystem — SDK, plugins, extension contracts, registry, marketplace, certification | ✅ done | 1639 tests |
| M9 | Autonomous — 13 task, INV-030..034 | ✅ done | 1780 tests @M9 · 94.46% (full suite 1793) |
| M10 | AIOS 1.0 — freeze INV-001..034, vi phạm = release blocker | 🔲 todo | — |

### 11.1 Chi tiết tasks M1–M9

| Task | Nội dung | Tests | Milestone |
|------|----------|-------|-----------|
| TASK-002 | Scaffold monorepo + aios_core (config/logging/metadata/healthcheck) | 32 | M1 |
| TASK-003 | Kernel Foundations — semver, contracts, DI, event bus, execution plan | 107 | M1 |
| TASK-004 | Kernel Services I — context, event+audit, artifact, permission, policy | 162 | M1 |
| TASK-005 | Kernel Services II — scheduler, state, resource, execution + RuntimeKernel | 207 | M1 |
| TASK-006 | Model Contract + providers (Mock/OpenAI/Ollama) + Registry | 233 | M1 |
| TASK-007 | Memory 4 loại + Knowledge pipeline | 270 | M1 |
| TASK-008 | Workflow Definition + Compilers + Library + CLI simulate | 300 | M1 |
| TASK-009 | Capability + Prompt Registry + Catalog + Knowledge Graph | 346 | M1 |
| TASK-011 | Remediation 9 P3 findings (M1 v2 review) | 428 | M1 |
| TASK-010 | Decision Pipeline (orchestrator v1) | 402 | M2 |
| TASK-012 | Goal Manager + Task Queue + Permission Broker + Failure Recovery | 490 | M2 |
| TASK-013 | Assistants (Worker Plane — INV-001/002) | 549 | M2 |
| TASK-014 | Tools 6 loại + Tool Registry + capability binding | 622 | M2 |
| TASK-015 | Skills lifecycle 10 states + Sandbox Pool | 669 | M2 |
| TASK-016 | Architecture Hardening — INV-001..010 + AST tests | 669+ | M2 |
| TASK-017 | FastAPI REST + WebSocket (9 routers, serve) | 689 | M3 |
| TASK-018 | Dashboard SPA (React+Vite+TS, 10 tabs, WS) | 12 vitest | M3 |
| TASK-019 | VS Code Extension (9 commands, TS) | 19 vitest | M3 |
| TASK-020 | Upgrade Pipeline (resolve/backup/migrate/pipeline) | 730 | M4 |
| TASK-021 | Observability (metrics/prompt_history/profiler/doctor/arch_health) | 779 | M4 |
| TASK-022 | Orchestrator v2 (advisor/supervisor/collector/goal_reporter) | 809 | M4 |
| TASK-023 | Memory Coordinator (INV-011) | 855 | M5 |
| TASK-024 | Context Optimizer (INV-012) | 896 | M5 |
| TASK-025 | Model Router (INV-013) | 949 | M5 |
| TASK-026 | Planning Engine (INV-014) | 1003 | M5 |
| TASK-027 | Execution Graph (INV-015) | 1055 | M5 |
| TASK-028 | Parallel Scheduler (INV-016) | 1086 | M5 |
| TASK-029 | H1 Harness Kernel (INV-017/018) | 1124 | M6 |
| TASK-030 | H2 Execution Verification (INV-019) | 1210 | M6 |
| TASK-031 | H3 Test & Simulation | 1299 | M6 |
| TASK-032 | H4 Evaluation Harness (INV-020) | 1387 | M6 |
| TASK-033 | H4 Benchmark + Regression Gate (INV-021) | 1450 | M6 |
| TASK-034 | H5 Doctor & Readiness | 1521 | M6 |
| TASK-035..042 | Enterprise E1–E7 (INV-022..029) | 1560 | M7 |
| TASK-043 | Public AIOS SDK | 5 SDK | M8 |
| TASK-044 | Plugin Runtime | 1584 | M8 |
| TASK-045..049 | Extension Contracts / Registry / DevKit / Marketplace / Certification | 1639 | M8 |
| TASK-050..062 | Autonomous (INV-030..034) | 1780 @M9 | M9 |

---

## 12. Architecture Invariants — INV-001..034

> Vi phạm = FAIL architecture review. Enforcement: `backend/tests/test_architecture.py` (AST import-graph scan, nhãn canonical `test_inv0xx_*`) + runtime scanner `observability/arch_health.py` (layer/contract/policy). Quyết định: `docs/adr/0004-architecture-invariants.md`.

| ID | Tên | Nội dung | Milestone |
|----|-----|----------|-----------|
| INV-001 | Runtime Isolation | Worker Agent không truy cập trực tiếp Runtime Service | M2 |
| INV-002 | Capability Isolation | Agent không gọi Tool trực tiếp — chỉ qua Capability | M2 |
| INV-003 | Workflow Independence | Workflow Definition không phụ thuộc engine (LangGraph) | M2 |
| INV-004 | Tool Independence | Capability không phụ thuộc implementation Tool cụ thể | M2 |
| INV-005 | Control Plane Isolation | Orchestrator điều phối, không chứa business implementation | M2 |
| INV-006 | Contract First | Cross-layer giao tiếp qua Contract | M2 |
| INV-007 | Policy First | Execution phải qua policy pre-check trước side effect | M2 |
| INV-008 | Artifact First | Output giữa boundary tham chiếu Artifact | M2 |
| INV-009 | Event Driven | Lifecycle quan trọng phát Event | M2 |
| INV-010 | Deterministic First | Rule/Registry/Workflow ưu tiên trước LLM | M2 |
| INV-011 | Memory Isolation | Agent KHÔNG truy cập Memory trực tiếp — qua Memory Coordinator | M5 |
| INV-012 | Context Budget | Context có token budget + priority (P0–P6), compression 3 cấp | M5 |
| INV-013 | Model Routing | Model chọn theo policy + fallback, availability flag tĩnh | M5 |
| INV-014 | Plan Validation | Planner tạo task graph hợp lệ, tách khỏi execution | M5 |
| INV-015 | Graph Acyclicity | Execution Graph hỗ trợ dependency + parallel + join/failure policy | M5 |
| INV-016 | Scheduler Non-Ownership | Scheduler KHÔNG sở hữu Resource/Execution | M5 |
| INV-017 | Harness Isolation | Harness không sửa Runtime — chỉ gọi qua API | M6 |
| INV-018 | Evidence First | Harness ghi evidence trước khi kết luận | M6 |
| INV-019 | Verification Before Verdict | Verify trước khi đưa verdict | M6 |
| INV-020 | Evaluation Determinism | Evaluation deterministic, reproducible | M6 |
| INV-021 | Release Gate | Benchmark/regression gate trước release | M6 |
| INV-022 | Identity First | Principal + RBAC/ABAC trước mọi quyết định | M7 |
| INV-023 | Tenant Isolation | TenantBoundary deny-by-default | M7 |
| INV-024 | Credential Isolation | CredentialBroker scoped | M7 |
| INV-025 | Resource Fairness | QuotaManager đảm bảo công bằng | M7 |
| INV-026 | Distributed Execution Safety | single-active lease, failover | M7 |
| INV-027 | Audit Completeness | CentralAuditStore tamper-evident | M7 |
| INV-028 | Sandbox Boundary | SandboxBoundary ngăn vượt ranh giới | M7 |
| INV-029 | Control Plane Isolation (M7) | Distributed runtime không phá vỡ control plane | M7 |
| INV-030 | Autonomous Action Boundary | Mọi action của Autonomy Loop qua Governor | M9 |
| INV-031 | Autonomy Bounded | Budget 7 loại (steps/llm/cost/duration/tool/retries/parallel) + risk | M9 |
| INV-032 | Long-running Resumable | Checkpoint/resume cho session dài | M9 |
| INV-033 | Self-Improvement via Harness | Experimentation qua Harness, evidence-first | M9 |
| INV-034 | Autonomous Memory No Unverified Promote | Memory promote phải qua kiểm chứng (double gate) | M9 |

**4 invariant chốt cốt lõi (ADR-0004):**
1. **Orchestrator không phải God Object** — điều phối qua Runtime API, không sở hữu service (INV-005).
2. **Agent không được chạm Tool** — mọi truy cập qua Capability (INV-002).
3. **Workflow không biết Engine** — definition thuần declarative (INV-003).
4. **Execution không bypass Policy** — policy pre-check trước side effect (INV-007).

---

## 13. Nguyên tắc xuyên suốt

- **Source of Truth = Repo**: `docs/PLAN.md` + `aios/progress/` là nguồn chính, không phải bộ nhớ phiên.
- **Control Plane vs Worker Plane**: Orchestrator là agent duy nhất chạm Runtime/Registry; Worker agents chỉ làm nghiệp vụ, truy cập hệ thống bắt buộc qua Capability + Runtime (enforced bởi Permission + Policy Service).
- **Offline-first**: 70–90% yêu cầu dừng ở Rule Engine + Workflow Matcher — nhanh, rẻ, test được.
- **Deterministic trước, LLM sau**: LLM là phương án cuối, không phải mặc định.
- **Contract-First**: 7 contract version hóa (major/minor compatibility), metadata chuẩn cho mọi component.
- **Autonomy có giới hạn**: Autonomous Layer định hướng Orchestrator trong giới hạn Policy/Governor (INV-030/031) — không tự do hành động ngoài kiểm soát.
- **Hard gate mọi task**: spec → critique ×2 → tasks → review → implement → test → evaluate (xem AGENTS.md).

---

## 14. Nguồn & lịch sử

- Tài liệu này: `docs/architecture-v2.md` (2026-08-15, TASK-063) — **bản hiện hành**.
- Bản cũ: `docs/architecture.md` — giữ làm lịch sử (mô tả đến M5 in-progress), không còn cập nhật.
- Nguồn chính: `docs/PLAN.md` · `aios/progress/PROGRESS.md` · `aios/progress/LOG.md` · `docs/adr/` · `backend/tests/test_architecture.py` · `backend/src/aios_core/observability/arch_health.py`.

---

## 15. M10 — AIOS 1.0 (Freeze + Constitution)

> PLAN §M10: `BUILD NOTHING — PROVE EVERYTHING → AIOS 1.0 CERTIFIED`. Kiến trúc bị **freeze** (INV-001..034 — vi phạm = release blocker), contract ổn định, runtime durable, autonomous bounded, có Certification Suite + Golden Scenarios + Conformance + Migration engine.

### 15.1 Tài liệu chuẩn 1.0 (`docs/architecture/`)

| File | Nội dung |
|------|----------|
| `AIOS-1.0.md` | Kiến trúc tổng thể 7 layers + 4 lớp mở rộng + cam kết 1.0 |
| `layer-model.md` | Mô hình 7 tầng L1..L7 + quy tắc tầng |
| `control-plane.md` | Orchestrator + registries + policy/governance + INV liên quan |
| `execution-plane.md` | Runtime kernel + workers + tools + sandbox + distributed (M7) |
| `autonomy.md` | Autonomy Layer — Governor gate + budget/risk + levels |
| `constitution-1.0.md` | **AIOS Architecture Constitution 1.0** — 15 core principle + INV-001..034 frozen |

### 15.2 Trạng thái M10 (theo PROGRESS.md)

| Phase | Task | Nội dung | Trạng thái |
|-------|------|----------|------------|
| P1 Freeze | TASK-063 | Architecture Freeze + Constitution 1.0 (file này + bộ docs/architecture/) | ✅ done (2026-08-15) |
| P1 Freeze | TASK-064 | Contract 1.0 — freeze 10 contracts + `aiagent contract-check` | 🔲 todo |
| P2 Harden | TASK-065 | Runtime Hardening — failure matrix 12 loại | 🔲 todo |
| P2 Harden | TASK-066 | Durable Execution 1.0 — journal + verify-before-resume + idempotency | 🔲 todo |
| P2 Harden | TASK-069 | Reliability — SLO + non-averaged gates | 🔲 todo |
| P3 Secure | TASK-067 | Autonomy Safety — Action Proposal → Governor → Policy → Tool | 🔲 todo |
| P3 Secure | TASK-068 | Kill Switch — `aiagent stop` + `aiagent emergency-stop` | 🔲 todo |
| P3 Secure | TASK-070 | Security Baseline 1.0 — 11 items + `aiagent security-check` | 🔲 todo |
| P4 Productize | TASK-071 | Developer Experience — command tree + `aiagent doctor` first-class | 🔲 todo |
| P4 Productize | TASK-072 | Dashboard 1.0 — 11 tabs + Execution Timeline | 🔲 todo |
| P4 Productize | TASK-075 | Performance & Cost — metrics + Cost/Goal/Workflow/Agent/Tool/Success | 🔲 todo |
| P5 Certify | TASK-073 | Certification Suite — 13 categories + GS-001..020 + conformance + 5 gates | 🔲 todo |
| P5 Certify | TASK-074 | Migration 1.0 — plan/backup/dry-run/validation/rollback | 🔲 todo |

### 15.3 Release Gates (TASK-073)

```
Gate A Architecture: INV violations = 0      Gate B Security: critical = 0, high = 0
Gate C Contract:     breaking = 0            Gate D Reliability: critical failures = 0
Gate E Autonomous:   policy/budget/kill-switch bypass = 0
```
Chỉ 1 gate fail → **AIOS 1.0 = NOT READY**. Conformance: `aiagent conformance` → 9 areas PASS → `AIOS 1.0 READY`.
