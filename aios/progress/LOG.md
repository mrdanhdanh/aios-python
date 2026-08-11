# LOG.md — Nhật ký hành động dự án AIOS

> Format: `YYYY-MM-DD HH:MM | TASK-xxx | bước | việc đã làm | kết quả | artifact`
> Entry `[bypass]` = fix nhỏ làm nhanh, có lý do.
> Entry mới ghi LÊN ĐẦU file (mới nhất trước).

| Thời gian | Task | Bước | Việc đã làm | Kết quả | Artifact |
|-----------|------|------|-------------|---------|----------|
| 2026-08-12 | TASK-004 | E3 | pytest 162 pass, coverage 94.77%; fix 2 lỗi (import path, publish signature) | done — 13/13 AC | `backend/tests/` |
| 2026-08-12 | TASK-004 | E1-E2 | Implement 5 services (context, event+audit, artifact sidecar, permission, policy) + Settings mở rộng | done — commit eb64795 | `kernel/services/` |
| 2026-08-12 | TASK-004 | review | Reviewer: 0 R1, 5 R2 vá nhẹ (pending mâu thuẫn, fake clock trap, sandbox defer, default policy, on_ask flow) — resolve hết | done | `tasks/TASK-004/review.md` |
| 2026-08-12 | TASK-004 | critique-2 | Critic v2: 1 P1 (timebase mâu thuẫn) + 6 P2 + 8 P3 — resolve hết | done | `tasks/TASK-004/critique-2.md` |
| 2026-08-12 | TASK-004 | critique-1 | Critic v1: 2 P1 (path guard startswith bypass, list thiếu cơ chế) + 6 P2 + 3 P3 — resolve hết | done | `tasks/TASK-004/critique-1.md` |
| 2026-08-12 | TASK-003 | D2-D4 | Implement: fix 5 lỗi thật (pydantic validator shadowing, object.__init__, event bus sync wrap, test deepcopy, abstractmethods) | done | `container.py`, `kernel/events.py`, `kernel/execution_plan.py`, `contracts/` |
| 2026-08-12 | TASK-003 | D1 | Implement: semver helper + contracts (ContractVersion, ContractMetadata, ArtifactContract, CompatibilityChecker) | done | `semver.py`, `contracts/` |
| 2026-08-12 | TASK-003 | review | Reviewer: CHANGES REQUESTED — R1 (thiếu bước update aios_core/__init__.py), R2×2 (flush re-raise, pytest root), R3×4 — resolve hết | done | `tasks/TASK-003/review.md` |
| 2026-08-12 | TASK-003 | critique-2 | Critic vòng 2: bắt 2 P1 mới do resolution v1 tạo ra (AC2 case 6 mâu thuẫn rule; check_upgrade đảo tham số) + 8 P2 + P3 — resolve hết | done | `tasks/TASK-003/critique-2.md` |
| 2026-08-12 | TASK-003 | critique-1 | Critic vòng 1: 2 P1 (compatibility sai chiều, async fire-and-forget) + 8 P2 + 8 P3 — resolve hết | done | `tasks/TASK-003/critique-1.md` |
| 2026-08-12 | TASK-003 | plan/spec | Tách TASK-003 (foundations) khỏi TASK-004 (services), viết spec kernel foundations | done | `tasks/TASK-003/spec.md` |
| 2026-08-11 | TASK-002 | C2.8 | venv + `pip install -e ".[dev]"` — aios-core 0.1.0 (fix readme path ngoài project dir; fix pydantic default factory) | done — AC1 pass | `backend/.venv` |
| 2026-08-11 | TASK-002 | C2 | Implement aios_core: config (search order + env validate + whitelist), logging (contextvars + JSON + idempotent), metadata (semver + make_component_metadata), healthcheck (worst-wins + edge cases) | done | `backend/src/aios_core/` |
| 2026-08-11 | TASK-002 | C1 | Scaffold cây monorepo 25 thư mục + .gitkeep + sdk stubs | done | `backend/*`, `dashboard/`, `extension/`, `skills/`, `docker/`, `sdk/` |
| 2026-08-11 | TASK-002 | review | Reviewer (subagent): CHANGES REQUESTED — 1 R1 (thiếu venv step) + 3 R2 (whitelist AIOS_CONFIG_PATH, timestamp default_factory, test.md/evaluation.md steps) + 4 R3 — resolve toàn bộ | done | `tasks/TASK-002/review.md` |
| 2026-08-11 | TASK-002 | critique-2 | Critic (subagent) vòng 2: bắt claim SAI cơ chế (extra=forbid không bắt typo env) + 6 P2 + 3 P3 — resolve toàn bộ | done | `tasks/TASK-002/critique-2.md` |
| 2026-08-11 | TASK-002 | critique-1 | Critic (subagent) vòng 1: 3 P1 + 6 P2 + 5 P3 (gitignore mâu thuẫn, HealthReport thiếu định nghĩa, config path mơ hồ...) — resolve toàn bộ | done | `tasks/TASK-002/critique-1.md` |
| 2026-08-11 | TASK-002 | spec | Viết spec.md TASK-002 (M1-P0: scaffold + aios_core) | done | `tasks/TASK-002/spec.md` |
| 2026-08-11 | TASK-001 | B4 | Người dùng xác nhận: agent picker hiển thị AIOS Orchestrator + 3 subagent; hard gate từ chối đúng | done — M0 ĐÓNG, TASK-001 done | `tasks/TASK-001/test.md` |
| 2026-08-11 | TASK-002 | spec | Viết spec.md TASK-002 (M1-P0: scaffold + aios_core) | done | `tasks/TASK-002/spec.md` |
| 2026-08-11 | TASK-001 | evaluate | Điền evaluation.md: 7/7 AC pass, kết luận ĐẠT spec | done | `tasks/TASK-001/evaluation.md` |
| 2026-08-11 | TASK-001 | stats | Cập nhật STATS.md: M0 done, 5 bài học | done | `aios/progress/STATS.md` |
| 2026-08-11 | TASK-001 | B4 | Verify tự động: B4.1 (git sạch), B4.4 (frontmatter 4 file hợp lệ), B4.5 (progress khớp) | done — 3/3 pass | `tasks/TASK-001/test.md` |
| 2026-08-11 | TASK-001 | B3 | Commit toàn bộ M0 (agent files + progress + fixes critique) | done — 08f1efa, c2d1032 | `git log` |
| 2026-08-11 | TASK-001 | B2 | Tạo progress system: PROGRESS.md, LOG.md, STATS.md (+ mục Bài học) | done | `aios/progress/` |
| 2026-08-11 | TASK-001 | spec | Viết spec.md cho TASK-001 (mục tiêu, phạm vi, AC, rủi ro) | done | `tasks/TASK-001/spec.md` |
| 2026-08-11 | TASK-001 | critique-1 | Critic phản biện vòng 1: tìm 1 P1 (gitignore ignore cả .vscode/), 1 P2 (thiếu rule phân loại task), 1 P3 (template verify) | done — 3/3 đã resolve: sửa .gitignore, thêm rule vào agent orchestrator, thêm ghi chú template | `tasks/TASK-001/critique-1.md` |
| 2026-08-11 | TASK-001 | critique-2 | Critic phản biện vòng 2: kiểm tra resolution vòng 1 (ok), tìm P2 mới (kiểm chứng subagent khi verify), P3 (STATS thiếu Bài học) | done — đã thêm bước B4.2 vào test.md + mục Bài học vào STATS.md | `tasks/TASK-001/critique-2.md` |
| 2026-08-11 | TASK-001 | tasks | Breakdown checklist B0–B4 (13 bước) | done | `tasks/TASK-001/tasks.md` |
| 2026-08-11 | TASK-001 | review | Reviewer: APPROVED có điều kiện (AC3/AC4 cần verify thủ công B4) | done | `tasks/TASK-001/review.md` |
| 2026-08-11 | TASK-001 | implement | Toàn bộ artifact M0 tạo xong (agents + progress + fixes) | done | `tasks/TASK-001/implementation/README.md` |
| 2026-08-11 | TASK-001 | B1 | Tạo 4 VS Code custom agent: aios-orchestrator (Control Plane, hard gate + bypass rules), spec-writer, critic (2 vòng phản biện), reviewer | done — 4 file tạo xong | `.github/agents/*.agent.md` |
| 2026-08-11 | TASK-001 | B0 | git init + git config local (AIAGENT Dev), tạo docs/PLAN.md (plan v6 đầy đủ), AGENTS.md, .gitignore | done — commit e50b715 | `docs/PLAN.md`, `AGENTS.md`, `.gitignore` |
| 2026-08-11 | TASK-001 | plan | Bắt đầu M0: tạo TASK-001, xác định 5 bước B0–B4 | done — checklist tạo trong tasks.md | `aios/progress/tasks/TASK-001/tasks.md` |
