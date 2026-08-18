# AIOS — AI Operating System

Nền tảng AI Agent chạy local desktop: **Runtime Kernel 9 services**, Workflow Engine pluggable,
AIOS Orchestrator (Control Plane) + Worker Agents, Core Intelligence (Memory/Context/Model/Planning/
Graph/Scheduler), Capability Layer, Plugin/Skill system, Dashboard, VS Code Extension, Autonomous Layer,
AIOS Harness (16 harness: behavioral / coverage / meta / release / diagnose / heal / simulate / certify / autonomous / dsh_bridge) —
**AIOS 1.1 READY · HARNESS TRACK COMPLETE (M13–M16) · 2360 tests**.

> Kiến trúc hệ thống: [`architecture-v3.md`](architecture-v3.md) · Chi tiết + milestones: [`PLAN.md`](PLAN.md)
> Tiến độ dự án: [`aios/progress/PROGRESS.md`](../aios/progress/PROGRESS.md)

## Trạng thái

| Milestone | Trạng thái | Số liệu |
|-----------|-----------|---------|
| M0–M9 | ✅ done | 1780 tests @M9 · coverage 94.46% |
| M10 — AIOS 1.0 | ✅ done | **1939 tests** + vitest 13/13 · `aiagent conformance` → **AIOS 1.0 READY** · doctor 100/100 · review ACCEPTED |
| M11 — Deterministic Artifact & Interaction Runtime | ✅ done (master) | **2052 tests** · `aiagent conformance` 10 areas/6 gates · **INV-035** (Verification Fail-Closed) |
| M12 — AIOS 1.1 Compatibility | ✅ done | **2118 tests** · `aiagent conformance` 11 areas/7 gates → **AIOS 1.1 READY** (TASK-084..088) |
| M13–M16 — Harness Track (Trust→Heal→Autonomy→Integrate) | ✅ done | **2360 tests / 0 FAIL** · **16 harness** · INV-036/037/038 · 4 invariant track (FAIL-CLOSED + INDEPENDENT VERIFICATION + PERMISSION BOUNDARY + CERTIFIED BASELINE/ROLLBACK) |

## Cấu trúc

```
backend/     Python core — aios_core: kernel 9 services, orchestrator, agents, intelligence,
             harness (16 harness), enterprise, plugins, autonomous, observability... (M1–M16)
sdk/         AIOS SDK python + typescript (public API — M8)
dashboard/   React + Vite SPA — 11 tabs + Execution Timeline (M3 + M10)
extension/   VS Code extension (M3)
skills/      skill packs mặc định
docker/      sandbox images
docs/        tài liệu + master plan + architecture (architecture-v3.md hiện hành, docs/architecture/*)
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
aiagent conformance     # 11 areas + 20 Golden Scenarios + 7 gates → AIOS 1.1 READY
aiagent arch-health     # Architecture Health — 0 violations (INV-001..038)
aiagent compat verify   # Backward compatibility cũ→mới trên AIOS 1.1 (9/9)
```

> Ghi chú:
> - `logging.file_path` mặc định là CWD-relative (`aios/logs/aios.jsonl`) — chạy tay từ `backend/` sẽ tạo `backend/aios/logs/` (đã thêm vào .gitignore).
> - Kiến trúc đã **freeze** tại M10 (INV-001..034); M11–M15 bổ sung **INV-035** (Verification Fail-Closed) · **INV-036** (Harness Trust) · **INV-037** (Remediation Integrity) · **INV-038** (Autonomy Boundary) — vi phạm = release blocker — xem [`docs/architecture/constitution-1.0.md`](architecture/constitution-1.0.md).
> - Harness Track M13–M16 HOÀN TẤT: Trust (ADR-0008) → Controlled Self-Healing → Autonomous Harness → DSH Bridge (independent oracle). Xem [`architecture-v3.md §9d`](architecture-v3.md).
> - Nâng cấp AIOS 1.0 → 1.1: [`docs/guides/migration-1.0-to-1.1.md`](guides/migration-1.0-to-1.1.md) · Chính sách: [`docs/adr/0007-compatibility-migration-policy.md`](adr/0007-compatibility-migration-policy.md).
