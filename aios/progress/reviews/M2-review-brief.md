# Review M2 — Developer Edition (template nâng cấp v2)

> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem bản review nội bộ nào trước đó.
>
> **Lưu ý cho reviewer:** Template v2 chuyển trọng tâm từ *existence review* (file có tồn tại không) sang **runtime correctness & architecture review** (kiến trúc có đúng không, runtime có hoạt động đúng không, offline-first có thật không). Bắt buộc áp dụng các mục 4–22 trước khi kết luận.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M4). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M2 – Developer Edition" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu)
- `AGENTS.md` — quy tắc vận hành dự án
- `docs/architecture.md` — tài liệu kiến trúc 7 tầng + 10 Architecture Invariants (INV-001..010)
- `docs/adr/` — Architecture Decision Records (ADR-0001..0004+)

## 2. Nhiệm vụ

Review milestone **M2** — Developer Edition (P3–P4): AIOS Orchestrator v1 (Decision Pipeline 4 tầng offline-first), Assistants (General + Coder + Doctor + System Doctor), Tools 6 loại (Python/Docker/REST/MCP/Shell/Git) + ToolRegistry + capability binding, Skills lifecycle 10 trạng thái + Skill Manager, Sandbox Pool (reuse + warm-start), Goal Manager + Task Queue, Permission Broker, Failure Recovery, System Knowledge, Capability Router.

Đánh giá độc lập 4 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M2 không (TASK-010 → TASK-016, trong đó TASK-015 skills/sandbox đang pending)
2. **Đúng quy trình**: hard gate có được tuân thủ cho từng task không (spec/critique ×2/tasks/review/test/evaluate)
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế ↔ kết quả test có khớp nhau không
4. **Đúng kiến trúc & runtime correctness**: kiến trúc tuân thủ INV-001..010, **offline-first có thật** (70–90% request không gọi LLM), isolation Worker Plane đúng nguyên tắc

## 3. Deliverable cần kiểm tra

### 3.1 Code (backend, src layout — package `aios_core` tại `backend/src/aios_core/`)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 1 | `backend/src/aios_core/orchestrator/` | Decision Pipeline 4 tầng: `normalizer.py`, `rule_engine.py`, `workflow_matcher.py`, `planner.py`, `orchestrator.py` (chỉ chọn capability), `agent_selector.py`, `system_knowledge.py` |
| 2 | `backend/src/aios_core/agents/` | Worker Plane: `base.py`, `general.py`, `coder.py`, `doctor.py`, `system_doctor.py`, `registry.py` — **chỉ import models.base/errors + pydantic + stdlib** (INV-001/002) |
| 3 | `backend/src/aios_core/tools/` | 6 tool types: `base.py` + `python_tool.py` + `docker_tool.py` + `rest_tool.py` + `mcp_tool.py` + `shell_tool.py` + `git_tool.py` + `registry.py` — **allow-list cứng** (metadata + pydantic + stdlib + urllib.parse) |
| 4 | `backend/src/aios_core/orchestrator/goals/` | Goal Manager (`goal.py`), Task Queue (`task_queue.py` — dequeue atomic RETURNING, reorder 2 pha, recover stale), Permission Broker (`permission_broker.py` — ask_scopes, default-deny), Failure Recovery (`failure_recovery.py` — retry→fallback→report), factory `__init__.py` |
| 5 | `backend/src/aios_core/skills/` | **PENDING (TASK-015)** — Skill Manager + lifecycle 10 trạng thái (resolve/validate/install/enable/disable/unload/reload/upgrade/rollback/remove) |
| 6 | `backend/src/aios_core/sandbox/` | **PENDING (TASK-015)** — Sandbox Pool (reuse pool, warm-start, health check, reset state, eviction idle) |
| 7 | `backend/src/aios_core/capabilities/` (từ M1) | Capability Registry (dynamic discovery) — verify TASK-014 bind_capabilities |
| 8 | CLI entrypoint | `aiagent` CLI — verify có subcommands chạy agent (general/coder/doctor/system-doctor) offline |

### 3.2 Tests (chạy thật)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 9 | `backend/tests/` | ~47 file test; chạy `pytest` trong `backend/` (venv: `backend/.venv/Scripts/python -m pytest`) — mong đợi **≥622 tests pass, 0 skip, coverage ~96%** |
| 10 | `test_orchestrator.py`, `test_normalizer.py`, `test_rule_engine.py`, `test_workflow_matcher.py`, `test_planner.py`, `test_agent_selector.py`, `test_system_knowledge.py` | Decision Pipeline + Orchestrator |
| 11 | `test_agents_base.py`, `test_coder_assistant.py`, `test_doctor_assistant.py`, `test_system_doctor.py`, `test_assistant_registry.py` | Worker Plane assistants |
| 12 | `test_tools_base.py`, `test_tool_stubs.py`, `test_tool_registry.py` | 6 tool types + registry + capability binding |
| 13 | `test_goal_manager.py`, `test_task_queue.py`, `test_permission_broker.py`, `test_failure_recovery.py` | Goal/Queue/Broker/Recovery |
| 14 | `test_architecture.py`, `_arch_scan.py` | 10 Architecture Invariants (AST pure scan — không import runtime) |
| 15 | `test_benchmark.py` | Benchmark harness (skippable) — catalog search < 5ms, workflow compile < 50ms, capability lookup O(1) |

### 3.3 Hồ sơ quy trình (hard gate)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 16 | `aios/progress/tasks/TASK-010/` … `TASK-016/` | **7 task M2 done** (010, 011, 012, 013, 014, 016 + 011 M1-followup), mỗi task đủ 8 file: spec.md, critique-1.md, critique-2.md, tasks.md, review.md, test.md, evaluation.md, implementation/ |
| 17 | `aios/progress/tasks/TASK-015/` | **PENDING** — chỉ có `spec.md` (skills + sandbox chưa implement) |
| 18 | `aios/progress/PROGRESS.md` | Mục M2: TASK-010/012/013/014/016 done, TASK-015 pending; khớp git history |
| 19 | `aios/progress/LOG.md` | Entry cho từng bước implement + test của TẤT CẢ task M2, đúng format |
| 20 | `aios/progress/STATS.md` | Mục M2: tests count, coverage, critique resolve, bypass |
| 21 | Git history | `git log --oneline` — commit code từng task M2 + "M2 HOÀN TẤT" (sau khi TASK-015 xong) |

---

## 4. Architecture Compliance (TRỌNG TÂM M2)

Reviewer phải xác minh kiến trúc AIOS tuân thủ **10 Architecture Invariants** (`docs/architecture.md` §7 + ADR-0004). Đọc `docs/architecture.md` trước khi review mục này.

Nguyên tắc bắt buộc:
- **INV-001 (Agent Plane separation)**: `agents/` chỉ import `models.base`, `models.errors`, pydantic, stdlib — KHÔNG import kernel/capabilities/tools/orchestrator. Mọi service qua callable injectable.
- **INV-002 (Tool Plane isolation)**: `tools/` allow-list cứng — chỉ metadata + pydantic + stdlib + urllib.parse. KHÔNG import kernel/capabilities/agents/orchestrator.
- **INV-003 (Control/Execution Plane)**: Orchestrator (Control) điều phối, Agent/Tool (Execution) thực thi — tách biệt rõ.
- **INV-004 (Capability-first)**: Agent gọi Capability, KHÔNG gọi Tool trực tiếp (`Agent → Capability → Tool`).
- **INV-005 (DI)**: service resolve qua container, không `new` rải rác.
- **INV-006 (Dependency 1 chiều)**: `kernel → capability → tool → infra`; không có vòng lặp; layer thấp không import layer cao.
- **INV-007 (Hard call-site)**: các hàm nhạy cảm (policy check, capability lookup) có call-site cố định, không qua monkey-patch.
- **INV-008 (Contract-first)**: giao tiếp qua contract, version hóa.
- **INV-009 (Event-driven)**: runtime phát event qua Event Bus; business events đúng schema.
- **INV-010 (Testability)**: mọi module có test; architecture invariants có AST scan test (test_architecture.py).

Sai (FAIL): `agents/coder.py` import `ExecutionService`; `tools/shell_tool.py` import `RuntimeKernel`; Orchestrator gọi Tool trực tiếp thay vì Capability.

## 5. Dependency Rules

Reviewer kiểm tra import graph (dùng `grep`/`ast`):
- `agents/` import allow-list (INV-001): chỉ `models.base`, `models.errors`, pydantic, stdlib
- `tools/` import allow-list (INV-002): chỉ metadata, pydantic, stdlib, `urllib.parse`
- **circular dependency**: không có vòng lặp import giữa orchestrator/agents/tools/capabilities/kernel
- **layer violation**: Tool không import Runtime Kernel; Agent không import Capability Registry trực tiếp

## 6. Runtime Wiring Review

Không chỉ ghi "wiring". Phải xác minh:
- **Service registration**: Goal Manager / Task Queue / Permission Broker / Failure Recovery đăng ký vào container
- **Lifecycle**: init / start / stop rõ ràng
- **Singleton / Scoped**: đúng scope
- **DI resolve**: service resolve qua container (xem TASK-011 F-007 — CLI dùng `RuntimeKernel.create()` / `SystemCatalog()`, không `ExecutionService(...)` trực tiếp)

## 7. Contract Evolution (mở rộng V1)

Đã verify ở M1 (TASK-011 F-002). Reviewer xác nhận regression tests còn tồn tại: `test_contracts.py` có 4 case (add / remove required / rename / optional→required) đúng chiều.

## 8. Workflow Contract Review (mở rộng V2/V3)

Workflow Definition độc lập engine — đã verify M1. Reviewer xác nhận không hồi quy (definition không import LangGraph/Docker/Model).

## 9. Capability Isolation (MỚI — TRỌNG TÂM M2)

Acceptance: `Agent → Capability → Tool`.
Reviewer phải **TÌM** `DockerTool(...)` / `ShellTool(...)` (tool cụ thể) bên trong `agents/`.
Nếu Agent khởi tạo Tool trực tiếp → **FAIL**. Capability là lớp trung gian, Agent gọi `capability.execute()` không gọi `tool.run()`.

## 10. Policy Engine Review (mở rộng V5)

Đã verify M1 (internet/filesystem/shell/docker/network/clipboard reject trước execution). M2 thêm: **Permission Broker** gom permission từ workflow → user approve → mới chạy. Đọc `test_permission_broker.py`: `ask_scopes`, default-deny khi không có approver.

## 11. Event Review (MỚI)

Event Bus phải **emit** các event (đọc emit sites):
- Execution Started / Finished (M1)
- Tool Started / Finished (`TOOL_STARTED` / `TOOL_FINISHED` — TASK-011 F-005)
- Policy Denied
- Snapshot Saved (`SNAPSHOT_SAVED` — TASK-011 F-005)
- **M2 mới**: `goal.*` (created/updated/completed/cancelled), `queue.updated`, `recovery.*` (retry/fallback/report) — xem `kernel/events.py` EventType +6

## 12. Resource Review (MỚI)

Đã verify M1 (allocate/queue/reject/release + FIFO queue TASK-011 F-003). Reviewer xác nhận không hồi quy.

## 13. Context Review (MỚI)

Đã verify M1 (6 context, isolation/TTL/cleanup/inheritance TASK-011 F-004). Reviewer xác nhận không hồi quy.

## 14. Knowledge Graph (mở rộng V7)

Đã verify M1 (O(1) + CRUD consistency). Không hồi quy.

## 15. Catalog (mở rộng V6)

Đã verify M1 (search không quét + rebuild/index/stale TASK-011 F-006). Không hồi quy.

## 16. Prompt Registry (MỚI)

Đã verify M1 (version/schema/variable/template). Không hồi quy.

## 17. CLI (mở rộng V3)

Đã verify M1 (`--simulate`, `doctor`, `catalog`, `workflow validate`, `contract validate` TASK-011 F-001). M2 thêm: subcommands chạy agent (general/coder/doctor/system-doctor) **offline**.

## 18. Runtime Crash (mở rộng V4)

Đã verify M1 (snapshot→kill→resume + crash→restart→resume). Không hồi quy.

## 19. Performance (MỚI)

Đã verify M1 (catalog < 5ms, compile < 50ms, capability O(1)). M2 thêm: Decision Pipeline routing latency (rule engine < 5ms cho 70–90% request).

## 20. Offline-First Verification (TRỌNG TÂM M2 — MỚI)

**ĐÂY LÀ TIÊU CHÍ QUAN TRỌNG NHẤT CỦA M2.** Reviewer phải chứng minh:
- Tắt LLM (Mock model, 0 lần gọi thực tế) → 70–90% request vẫn routing đúng qua **Rule Engine**:
  - "Generate API" → Coder
  - "medical question" → Doctor
  - "system status" → System Doctor
- **Planner LLM chỉ gọi khi thật sự cần** (nhiệm vụ mở) — đọc `rule_engine.py` + `planner.py` + test tương ứng (`test_rule_engine.py` với kết quả xác định trước, `test_orchestrator.py` mock model 0 call)
- **Orchestrator chỉ chọn capability không chọn tool trực tiếp** (INV-004)

Cách kiểm chứng: chạy test với model bị mock/dis bên dưới; đếm số lần `planner.plan()` được gọi. Phải = 0 cho các intent rõ ràng.

## 21. Security Review (MỚI)

Reviewer kiểm tra:
- permission bypass (Permission Broker default-deny)
- direct tool access (vượt capability — INV-004)
- unsafe import (allow-list agents/tools — INV-001/002)
- shell injection (ShellTool không exec scope bắt buộc — TASK-014)
- Python tool: `ast.parse` no-exec (TASK-014)

## 22. Anti Fake Test (RẤT QUAN TRỌNG)

Không chỉ "≥622 tests pass". Reviewer phải kiểm tra coverage thật sự cover Acceptance Criteria.
Ví dụ: `test_rule_engine.py` chỉ `assert True` vẫn pass nhưng không test routing → phải bị bắt.
Phải **đọc body test**, không chỉ đếm số pass. Kiểm tra mỗi test có assert đúng behavior hay chỉ pass bề mặt.
Đặc biệt với M2: test offline-first phải **thực sự mock model và đếm call count**, không chỉ assert output.

---

## 23. Tiêu chí chấp nhận (nguồn: PLAN.md → Verification M2 + mở rộng)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|------------------|---------------------|
| V1 | Capability swap (execute_code: docker→mock) **không đổi** agent code | Đọc `agents/` + `capabilities/`; đổi tool impl → agent không sửa | Agent gọi capability, không import tool cụ thể (INV-004) |
| V2 | Skill lifecycle test đủ 10 trạng thái (resolve/validate/install/enable/disable/unload/reload/upgrade/rollback/remove) | Đọc `skills/` + `test_skills.py` (TASK-015 pending) | 10 trạng thái có test; state machine đúng chuyển tiếp |
| V3 | Sandbox pool reuse + warm-start | Đọc `sandbox/` + `test_sandbox.py` (TASK-015 pending) | Pool tái sử dụng container, warm-start, reset state, eviction idle |
| V4 | **Offline-first**: tắt LLM → 70–90% request routing đúng qua Rule Engine (Generate API→Coder, medical→Doctor, system→System Doctor) | Chạy test với model mock/dis bên dưới; đếm `planner.plan()` calls | `test_rule_engine.py` + `test_orchestrator.py`: 0 planner call cho intent rõ ràng; routing đúng |
| V5 | **Planner LLM chỉ gọi khi thật sự cần** (nhiệm vụ mở) | Đọc `planner.py` + test nhiệm vụ mở | Planner chỉ gọi khi Rule Engine/Matcher thất bại; test assertion call count |
| V6 | **Orchestrator chỉ chọn capability không chọn tool trực tiếp** | Đọc `orchestrator.py` + `agents/` (INV-004) | Không có `Tool(...)` trong orchestrator/agents; capability router chọn |
| V7 | **Permission Broker**: workflow cần network/shell → gom permission → user approve → mới chạy | Đọc `permission_broker.py` + `test_permission_broker.py` | ask_scopes gom scope; default-deny khi không approve; test cover |
| V8 | **Failure Recovery**: agent lỗi → retry → fallback agent → report | Đọc `failure_recovery.py` + `test_failure_recovery.py` | Retry → Fallback → Report chain có test; event `recovery.*` emit |
| V9 | **Isolation**: Worker agent không truy cập registry trực tiếp (bị Permission + Policy chặn) | Đọc `agents/` imports (INV-001) + test | agents/ không import kernel/capabilities/tools; AST scan pass |
| V10 | **Goal Manager**: goal "Xây AIOS" → tasks → progress persist qua phiên | Đọc `goals/goal.py` + `test_goal_manager.py` | Goal state machine + cascade cancel + persist (DB/JSON) có test |
| V11 | **Task Queue**: pause/resume/reorder/priority hoạt động | Đọc `goals/task_queue.py` + `test_task_queue.py` | dequeue atomic RETURNING, reorder 2 pha, recover stale, priority có test |
| V12 | Xuyên suốt: pytest + contract tests CI; permission enforcement (ask→deny); rule engine unit test kết quả xác định | Chạy `pytest`; đọc `test_policy.py`, `test_rule_engine.py` | Tất cả pass; rule engine deterministic |

**Deliverable M2 (PLAN.md)**: dev dùng CLI (mặc định qua Orchestrator, **hoạt động offline khi không có LLM**) để agent sinh code + test trong sandbox, cài skill plugin đầy đủ.

**Các tiêu chí architecture (mục 4–22)** phải được reviewer xác minh riêng và báo cáo trong subsection "Architecture Compliance" (xem mục 25).

**Trạng thái hiện tại (2026-08-13)**: TASK-010/011/012/013/014/016 done (622 tests, 0 skip, 96.15% cov). **TASK-015 (Skills + Sandbox) đang PENDING** — V2/V3 sẽ INCONCLUSIVE cho đến khi TASK-015 hoàn tất.

## 24. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 23: tìm bằng chứng → kết luận **PASS/FAIL/INCONCLUSIVE** kèm trích dẫn `file:đường dẫn`
3. Áp dụng Architecture Compliance (mục 4), Dependency Rules (mục 5), Runtime Wiring (mục 6), và các mục 7–22 — mỗi mục phải có kết luận rõ
4. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật nếu có quyền)
5. Tìm lỗ hổng chủ động: file thiếu (đặc biệt TASK-015), stub không có logic, mâu thuẫn, checkbox chưa tick, claim không có bằng chứng, **test pass nhưng không test đúng thứ cần test** (mục 22)
6. Với mỗi task M2 done: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
7. Phân mức findings: **P1** (sai mục tiêu/tiêu chí — phải sửa trước khi chấp nhận), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 25. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review M2 — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả (PASS/FAIL/INCONCLUSIVE) | Bằng chứng (file + trích dẫn) |

## 2. Architecture Compliance
(đối chiếu mục 4–22: INV-001..010 / Runtime-first / Contract-first / Plugin-first /
Capability-first / Policy-first / DI / Event-driven / Dependency / Wiring / Security /
Performance / Offline-First / Anti-fake-test — mỗi nguyên tắc ghi PASS/FAIL/INCONCLUSIVE + trích dẫn)

## 3. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 4. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 5. Điểm mạnh (nếu có)
## 6. Gợi ý cải thiện (không bắt buộc)
```

## 26. Final Gate (nâng cấp)

Kết quả mỗi tiêu chí thuộc một trong 3 trạng thái:
- **PASS**: Có bằng chứng trực tiếp và kiểm chứng được (đọc code + chạy test/CLI).
- **FAIL**: Có bằng chứng cho thấy không đạt.
- **INCONCLUSIVE**: Không đủ bằng chứng để kết luận (reviewer không có quyền chạy, thiếu file, hoặc mâu thuẫn không giải được).

**Milestone M2 chỉ được ACCEPTED khi:**
- V1, V4–V11 = **PASS** (không FAIL, không INCONCLUSIVE)
- V2, V3 = **PASS** (yêu cầu TASK-015 done — hiện INCONCLUSIVE do pending)
- Không có **P1** finding
- Không có **INCONCLUSIVE** nào trong bảng tiêu chí
- Các test bắt buộc (mục 3.2) chạy thành công trên môi trường review (hoặc có bằng chứng thực thi đáng tin cậy nếu reviewer không có quyền chạy)

> Nếu có bất kỳ **INCONCLUSIVE** nào (VD: TASK-015 chưa xong), milestone không được ACCEPTED cho đến khi reviewer có đủ bằng chứng nâng lên PASS hoặc FAIL.
