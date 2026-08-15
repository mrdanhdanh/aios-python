# Execution Plane — AIOS 1.0

> Execution Plane = nơi công việc được THỰC HIỆN: runtime nodes (M7), worker agents, capability, tools, sandbox. Worker KHÔNG truy cập registry/control plane trực tiếp — chỉ qua Capability + Runtime (INV-002, INV-005, INV-028).

## Thành phần (module thật — `backend/src/aios_core/`)

| Nhóm | Module | Vai trò |
|------|--------|---------|
| Runtime Kernel | `kernel/runtime_kernel.py` + `kernel/services/` (execution, context, event, artifact, permission, policy, scheduler, state, resource) | 9 services, DI container, event bus |
| Execution | `kernel/services/execution.py` — checkpoint/snapshot/resume, retry/cancel/timeout | Chạy Execution Plan |
| Graph & Scheduler (M5) | `kernel/graph/` (execution_graph) · `kernel/scheduler.py` (graph scheduler) | DAG + parallel execution (INV-015, INV-016) |
| Workers | `agents/` (general, coder, doctor, system_doctor) | Worker Plane — chỉ làm nghiệp vụ |
| Capability | `capabilities/registry.py` | Dynamic discovery: tool khai báo capabilities, router chọn theo health/availability/priority |
| Tools | `tools/` (python, docker, rest, mcp, shell, git) | 6 loại tool, gate fail-closed |
| Sandbox | `sandbox/pool.py` | Pool tái sử dụng container, warm-start (M2; sandbox thật M7 INV-028) |
| Enterprise (M7) | `enterprise/runtime.py` · `scheduler.py` · `operations.py` | Runtime Node + Router, Distributed Scheduler + Lease/Failover (INV-026), HA |

## Luồng thực thi

```
Planning → Execution Graph → Graph Scheduler → Resource Service → Execution Service → State Service
   → Agent → Capability → Tool → (Sandbox) → Artifact/Events
```

## Ranh giới (bất biến)

- INV-001 Runtime Isolation — agent/worker không chạm runtime service trực tiếp.
- INV-002 Capability Isolation — agent không chọn tool trực tiếp, chỉ chọn capability.
- INV-004 Tool Independence — workflow/agent không import tool implementation.
- INV-016 Scheduler Separation — scheduler không sở hữu Resource/Execution.
- INV-026 Distributed Execution Safety — một execution chỉ một active lease.
- INV-028 Sandbox Boundary — untrusted tool execution phải qua sandbox policy.

## M7: Distributed

```
Orchestrator → Runtime Router → Runtime-01 / Runtime-02 / Runtime-03
                                    │        │        │
                                Worker  Worker  Worker → Capability → Tool → Sandbox
```
Failover: Runtime chết → lease expired → scheduler → runtime khác → resume snapshot (INV-026, INV-032).
