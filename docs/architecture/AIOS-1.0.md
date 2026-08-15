# AIOS 1.0 — Architecture (Frozen)

> **Trạng thái: FROZEN (2026-08-15)** — tài liệu kiến trúc chuẩn của AIOS 1.0. Mọi thay đổi fundamental → **AIOS 2.0**. Sau 1.0 chỉ cho phép: bug/security/performance fixes, backward-compatible features, ecosystem extensions.
> Xem thêm: [`layer-model.md`](layer-model.md) · [`control-plane.md`](control-plane.md) · [`execution-plane.md`](execution-plane.md) · [`autonomy.md`](autonomy.md) · [`constitution-1.0.md`](constitution-1.0.md)

## Kiến trúc tổng thể (7 layers)

```
USER / SYSTEM
    │
    ▼
UI / SDK / API                 (L1: dashboard · extension · sdk · api)
    │
    ▼
AUTONOMY CONTROL               (L2: autonomous/ — Goal · Planner · Governor · World)
    │
    ▼
ORCHESTRATOR (Control Plane)   (L3: orchestrator/ — Decision Pipeline 4 tầng)
    │
    ▼
WORKFLOW / AGENT / CAPABILITY  (L4: workflow/ · agents/ · capabilities/)
    │
    ▼
RUNTIME KERNEL                 (L5: kernel/ — 9 services + DI + event bus)
    │
    ▼
TOOLS / STATE / EVENTS         (L6: tools/ · context/ · sandbox/)
    │
    ▼
INFRA                          (L7: models · memory · knowledge · catalog · observability
                                     · upgrade · enterprise · harness · plugins · ecosystem)
```

## Bốn lớp hệ sinh thái (M6–M9)

| Lớp | Nội dung | Package |
|-----|----------|---------|
| Harness (M6) | Tự kiểm thử/xác minh/đánh giá chính mình — H1..H5 | `harness/` (kernel, execution, testing, evaluation, benchmark, doctor) |
| Enterprise (M7) | Identity/Tenancy/Distributed/Governance/Security/Operations | `enterprise/` |
| Ecosystem (M8) | SDK công khai + Plugin + Extension Contracts + Registry + DevKit + Marketplace + Certification | `sdk/python` + `plugins/` + `extension/` + `ecosystem/` |
| Autonomous (M9) | Goal-driven + Bounded + Observable + Reversible + Evaluated | `autonomous/` |

## Khối xây dựng

- **Runtime Kernel 9 services**: Execution · Context · Event · Artifact · Permission · Policy · Scheduler · State · Resource (`kernel/services/`)
- **Core Intelligence (M5)**: Memory Coordinator · Context Optimizer · Model Router · Planning Engine · Execution Graph · Parallel Scheduler
- **Decision Pipeline**: Normalizer → Rule Engine (deterministic, 70–90%) → Workflow Matcher → Planner LLM (chỉ khi cần)
- **Contract 1.0**: 10 public contracts frozen (xem `aiagent contract-check` — TASK-064)

## Cam kết 1.0 (M10)

| Năng lực | Trạng thái |
|----------|-----------|
| Execute (workflow/agent/capability/tool) | ✅ Có (M1–M2) |
| Orchestrate (decision pipeline + policy) | ✅ Có (M2) |
| Reason/Plan (planning engine + graph) | ✅ Có (M5) |
| Recover (failure recovery + resilience) | ✅ Có (M2/M4) — hardening M10 (TASK-065) |
| Resume (snapshot/checkpoint durable) | ✅ Có (M1/M9) — durable 1.0 (TASK-066) |
| Autonomous bounded (governor/budget) | ✅ Có (M9) — safety 1.0 (TASK-067) + kill switch (TASK-068) |
| Prove result (harness/evidence) | ✅ Có (M6) |
| Extensible (sdk/plugin/ecosystem) | ✅ Có (M8) |
| Enterprise (identity/tenant/distributed) | ✅ Có (M7) |
| Stable under change (freeze + certification) | 🔲 **M10** — Certification Suite + Golden Scenarios (TASK-073, planned) |

## Release Gates (planned — TASK-073)

```
Gate A Architecture: INV violations = 0
Gate B Security:     critical = 0, high = 0
Gate C Contract:     breaking compatibility = 0
Gate D Reliability:  critical scenario failures = 0
Gate E Autonomous:   policy bypass = 0, budget bypass = 0, kill-switch bypass = 0
```
Chỉ 1 gate fail → **AIOS 1.0 = NOT READY**. Conformance: `aiagent conformance` → 9 areas PASS → `AIOS 1.0 READY` (TASK-073).

## Golden Demo (mục tiêu — PLAN §M10-40)

"Phân tích module X, tìm vấn đề, lập kế hoạch sửa, thực hiện, chạy test, tự recover nếu fail, đánh giá và báo cáo" → toàn bộ pipeline `Request→Normalizer→Rule→Workflow→Goal→Planner→Policy→Governor→Coder→Capability→Tools→Tests→Failure→Recovery→Replan→Verify→Evaluation→Evidence→Goal Complete` — Dashboard hiển thị execution trace.
