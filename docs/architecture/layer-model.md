# Layer Model — AIOS 1.0 (7 tầng)

> Tài liệu chuẩn theo PLAN.md §M10-4. Tầng thấp hơn là hạ tầng cho tầng trên; dependency 1 chiều (enforced bởi INV-001..010 + arch tests `backend/tests/test_architecture.py` + scanner runtime `observability/arch_health.py`).

```
USER / SYSTEM
    │
    ▼
L1  UI / SDK / API          dashboard/ · extension/ · sdk/ · backend/src/aios_core/api/
    │
    ▼
L2  AUTONOMY CONTROL        autonomous/ (Goal · Planner · World · Governor · Loop)
    │
    ▼
L3  ORCHESTRATOR            orchestrator/ (Normalizer · Rule Engine · Workflow Matcher · Planner
    │                       · Agent Selector · Capability Router · Policy · Permission Broker ...)
    ▼
L4  WORKFLOW / AGENT / CAPABILITY   workflow/ · agents/ · capabilities/
    │
    ▼
L5  RUNTIME KERNEL          kernel/ (9 services: Execution, Context, Event, Artifact,
    │                       Permission, Policy, Scheduler, State, Resource)
    ▼
L6  TOOLS / STATE / EVENTS  tools/ · context/ · kernel/events.py · sandbox/
    │
    ▼
L7  INFRA                   models/ · memory/ · knowledge/ · knowledge_graph/ · catalog/
                            · observability/ · upgrade/ · enterprise/ · harness/
                            · plugins/ · extension/ · ecosystem/
```

## Bảng 7 tầng

| Tầng | Tên | Package chính (`backend/src/aios_core/`) | Vai trò |
|------|-----|------------------------------------------|---------|
| L1 | UI / SDK / API | `api/` (FastAPI + WS), `dashboard/`, `extension/`, `sdk/python`, `sdk/typescript` | Giao diện người dùng & lập trình viên |
| L2 | Autonomy Control | `autonomous/` | Goal-driven, bounded, observable (INV-030..034) |
| L3 | Orchestrator Control Plane | `orchestrator/` (+ `goals/`, `planning/`) | Decision Pipeline 4 tầng offline-first, điều phối |
| L4 | Workflow / Agent / Capability | `workflow/`, `agents/`, `capabilities/` | Nghiệp vụ: agent chỉ qua Capability (INV-002) |
| L5 | Runtime Kernel | `kernel/` | 9 services, DI container, event bus |
| L6 | Tools / State / Events | `tools/`, `context/`, `sandbox/` | Execution plane: tool 6 loại, state, events |
| L7 | Infra | `models/`, `memory/`, `knowledge/`, `catalog/`, `observability/`, `upgrade/`, `enterprise/`, `harness/`, `plugins/`, `extension/`, `ecosystem/` | Hạ tầng dùng chung, mở rộng |

## Luồng request 1.0 (rút gọn)

```
Request → L1 (API/CLI) → L3 Orchestrator (Normalizer → Rule → Matcher → Planner)
       → L2 (nếu autonomous: Governor gate) → L4 (Agent → Capability)
       → L5 Runtime (Execution) → L6 (Tool/State/Events) → L7 (Model/Memory/Knowledge)
```

## Quy tắc tầng

- **L3 là Control Plane duy nhất** — mọi điều phối qua Orchestrator; worker chỉ truy cập qua Capability + Runtime (INV-005, INV-029).
- **L2 định hướng L3, không thay thế** — Autonomy Layer đưa ra mục tiêu, Orchestrator vẫn là Control Plane.
- **L5 không biết L4** — Runtime thi hành Execution Plan, không nhúng agent.
- **L7 là dùng chung** — Harness (M6) chỉ gọi API, không chui vào implementation (INV-017).
