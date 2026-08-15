# AIOS — AI Operating System

Nền tảng AI Agent chạy local desktop: **Runtime Kernel 9 services**, Workflow Engine pluggable,
AIOS Orchestrator (Control Plane) + Worker Agents, Core Intelligence (Memory/Context/Model/Planning/
Graph/Scheduler), Capability Layer, Plugin/Skill system, Dashboard, VS Code Extension, Autonomous Layer —
**AIOS 1.0 CERTIFIED**.

> Kiến trúc hệ thống: [`architecture-v3.md`](architecture-v3.md) · Chi tiết + milestones: [`PLAN.md`](PLAN.md)
> Tiến độ dự án: [`aios/progress/PROGRESS.md`](../aios/progress/PROGRESS.md)

## Trạng thái

| Milestone | Trạng thái | Số liệu |
|-----------|-----------|---------|
| M0–M9 | ✅ done | 1780 tests @M9 · coverage 94.46% |
| M10 — AIOS 1.0 | ✅ done | **1939 tests** + vitest 13/13 · `aiagent conformance` → **AIOS 1.0 READY** · doctor 100/100 · review ACCEPTED |

## Cấu trúc

```
backend/     Python core — aios_core: kernel 9 services, orchestrator, agents, intelligence,
             harness, enterprise, plugins, autonomous, observability... (M1–M10)
sdk/         AIOS SDK python + typescript (public API — M8)
dashboard/   React + Vite SPA — 11 tabs + Execution Timeline (M3 + M10)
extension/   VS Code extension (M3)
skills/      skill packs mặc định
docker/      sandbox images
docs/        tài liệu + master plan + architecture (architecture-v2.md, docs/architecture/*)
aios/        progress tracking (PROGRESS/LOG/STATS) + data
```

## Chạy test

```bash
# Backend — từ backend/ (venv đã cài .[dev])
cd backend
.venv/Scripts/python -m pytest

# Dashboard + Extension
npm run test        # dashboard (vitest)
cd extension && npm run test
```

Coverage gate ≥ 80% trên `aios_core` (tự động qua `addopts`).

## Kiểm tra sức khỏe hệ thống

```bash
# Sau khi kích hoạt venv backend
aiagent doctor          # Health 100/100 (18 hạng mục)
aiagent conformance     # 9 areas + 20 Golden Scenarios → AIOS 1.0 READY
aiagent arch-health     # Architecture Health — 0 violations (INV-001..034)
```

> Ghi chú:
> - `logging.file_path` mặc định là CWD-relative (`aios/logs/aios.jsonl`) — chạy tay từ `backend/` sẽ tạo `backend/aios/logs/` (đã thêm vào .gitignore).
> - Kiến trúc đã **freeze** tại M10: INV-001..034, vi phạm = release blocker — xem [`docs/architecture/constitution-1.0.md`](architecture/constitution-1.0.md).
