# AIOS — AI Operating System

Nền tảng AI Agent 5 tầng chạy local desktop: Runtime Kernel 9 services, Workflow Engine
pluggable, Capability Layer, Plugin/Skill system, Dashboard, VS Code Extension.

> Chi tiết kiến trúc + milestones: [`docs/PLAN.md`](PLAN.md)
> Tiến độ dự án: [`aios/progress/PROGRESS.md`](../aios/progress/PROGRESS.md)

## Cấu trúc

```
backend/     Python core (aios_core: config, logging, metadata, healthcheck — M1)
sdk/         SDK python + typescript (stub)
dashboard/   React + Vite SPA (M3)
extension/   VS Code extension (M3)
skills/      skill packs mặc định
docker/      sandbox images
docs/        tài liệu + master plan
aios/        progress tracking (PROGRESS/LOG/STATS)
```

## Chạy test backend

```bash
# Cách 1 — từ backend/ (venv đã cài .[dev])
cd backend
.venv/Scripts/python -m pytest

# Cách 2 — từ repo root
backend/.venv/Scripts/python -m pytest backend/tests
```

Coverage gate ≥ 80% trên `aios_core` (tự động qua `addopts`).

> Ghi chú:
> - `logging.file_path` mặc định là CWD-relative (`aios/logs/aios.jsonl`) — chạy tay từ `backend/` sẽ tạo `backend/aios/logs/` (đã thêm vào .gitignore).
> - Chưa có log rotation ở M1 — sẽ xử lý trong P8 observability.
