# Review M3 — Desktop Edition (template nâng cấp v2)

> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem bản review nội bộ nào trước đó.
>
> **Lưu ý cho reviewer:** Template v2.1 (hard-gate review framework) chuyển trọng tâm từ *existence review* sang **runtime correctness & architecture review**. Bắt buộc áp dụng các mục 4–22 + Acceptance Traceability (22A) + Final Gate (26) trước khi kết luận.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M10). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M3 – Desktop Edition (P5–P6)" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu M3)
- `AGENTS.md` — quy tắc vận hành dự án
- `docs/architecture.md` — tài liệu kiến trúc 7 tầng + Architecture Invariants (INV-001..010+)
- `docs/adr/` — Architecture Decision Records

## 2. Nhiệm vụ

Review milestone **M3** — Desktop Edition (P5–P6):
- **P5 Dashboard**: 10 views (Chat, Workflow Viewer, Event Timeline WebSocket, Tool Usage, Memory Viewer, Artifact Browser, Skill Marketplace, Model Usage, Prompt Inspector, Health Dashboard)
- **P6 VS Code Extension**: 9 lệnh (Chat, Explain, Fix selection, Generate test, Review PR, Refactor, Rename, Ask Workspace, Chat với repo)
- Kết quả: sản phẩm desktop hoàn chỉnh cho người dùng cuối, backend REST + WebSocket API phục vụ cả Dashboard và Extension.

Đánh giá độc lập 4 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M3 (TASK-017 API, TASK-018 Dashboard, TASK-019 Extension)
2. **Đúng quy trình**: hard gate có được tuân thủ cho từng task không (spec/critique ×2/tasks/review/test/evaluate)
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế ↔ kết quả test có khớp nhau không
4. **Đúng kiến trúc & runtime correctness**: kiến trúc tuân thủ INV-001..010, API layer là composition root đúng luật, Dashboard/Extension qua API (không bypass kernel)

## 3. Deliverable cần kiểm tra

### 3.1 Code (backend — package `aios_core` tại `backend/src/aios_core/`)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 1 | `backend/src/aios_core/api/` | `app.py` (create_app factory, 11 routers, CORS, error handlers), `wiring.py` (build_registries — RuntimeKernel.create + registries), `serve.py` (uvicorn runner), `routers/` (health, events, catalog, goals, skills, tools, memory, prompts, chat, observability, orchestrator_v2) |
| 2 | `backend/src/aios_core/api/routers/events.py` | **AC quan trọng**: `GET /events` (audit history) + `WS /events/ws` (realtime: subscribe EventBus → forward JSON, `call_soon_threadsafe` + queue backpressure, cleanup unsubscribe) |
| 3 | `backend/src/aios_core/api/routers/chat.py` | Chat endpoint đi qua orchestrator decision pipeline + assistant registry (Control Plane), **KHÔNG** gọi Tool trực tiếp |
| 4 | `backend/workflow/cli.py` | subcommand `aiagent serve --host --port` (lazy import) |

### 3.2 Code (frontend — `dashboard/` và `extension/`)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 5 | `dashboard/` | Vite + React 18 + TS: `src/App.tsx` (10 tabs), `src/api.ts` (3-envelope fetch wrapper), `src/ws.ts` (WebSocket reconnect 3s + MockWebSocket stub), `src/views/` (10 views: Chat/Workflow/EventTimeline/ToolUsage/Memory/ArtifactBrowser/SkillMarketplace/ModelUsage/PromptInspector/Health), `vite.config.ts` (proxy /api → 127.0.0.1:8000) |
| 6 | `dashboard/src/views/ArtifactBrowser.tsx` | **AC quan trọng**: render `artifact_type` cho mỗi artifact → "hiển thị đủ loại" |
| 7 | `extension/` | package.json (9 commands + activationEvents + config `aios.serverUrl`), `src/extension.ts` (activate + 9 commands + INTENTS map), `src/client.ts` (AiosClient.callChat — 3 envelope + trim slash), `src/context.ts` (editorText qua document.getText, gitDiff, buildPrompt 8 template) |

### 3.3 Tests (chạy thật)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 8 | `backend/tests/test_api.py` | API router tests (AC1–AC10, AC12): health, events, catalog, goals, skills, tools, artifacts, prompts, models, sandbox — assert data shapes + counts |
| 9 | `backend/tests/test_api_chat_serve.py` | Chat (intent routing + 422 extra=forbid) + **WS realtime**: `test_ws_events_realtime` publish từ thread khác → ws nhận đúng type/payload; CLI serve parser |
| 10 | `dashboard/src/__tests__/` | `api.test.ts`, `ws.test.ts`, `App.test.tsx` — vitest + jsdom + testing-library: 10 tabs, chat response, health score, no-data states, ws reconnect |
| 11 | `extension/src/__tests__/` | `client.test.ts` (8 tests), `extension.test.ts` (11 tests) — vitest: 9 commands registered, intent map 9 cases, selection guard, editor.edit replace cho fix/generate_test, 3 envelope errors |
| 12 | Toàn bộ backend | `cd backend; .venv/Scripts/python -m pytest` — mong đợi **≥689 tests pass** (tại thời điểm M3; hiện full suite 1560 do M4–M7 thêm) |

### 3.4 Hồ sơ quy trình (hard gate)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 13 | `aios/progress/tasks/TASK-017/` | M3-P5 API — đủ 8 file: spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/ |
| 14 | `aios/progress/tasks/TASK-018/` | M3-P5 Dashboard — đủ 8 file |
| 15 | `aios/progress/tasks/TASK-019/` | M3-P6 Extension — đủ 8 file |
| 16 | `aios/progress/PROGRESS.md` | Mục M3: TASK-017/018/019 done; khớp git history |
| 17 | `aios/progress/LOG.md` | Entry cho từng bước implement + test của TẤT CẢ task M3, đúng format |
| 18 | `aios/progress/STATS.md` | Mục M3: tests count, coverage, critique resolve |
| 19 | Git history | `git log --oneline` — commit code từng task M3 (16c998f, 33b6b05, 298e4bb) + "M3 DONE" |

---

## 4. Architecture Compliance (TRỌNG TÂM M3)

Reviewer phải xác minh kiến trúc AIOS tuân thủ **Architecture Invariants** (`docs/architecture.md` §7). Đọc `docs/architecture.md` trước khi review mục này.

Nguyên tắc bắt buộc cho M3 (UI/API layer là Infra/Composition-root — ĐƯỢC phép import mọi thứ, nhưng phải đi qua orchestrator/capability, KHÔNG bypass):
- **INV-001 (Agent Plane separation)**: agents chỉ import models.base/errors + pydantic + stdlib. M3 thêm API layer — API là composition root, KHÔNG vi phạm vì nó không phải Execution Plane.
- **INV-002 (Tool Plane isolation)**: tools allow-list cứng. API không gọi Tool trực tiếp — phải qua orchestrator/assistant/capability.
- **INV-003 (Control/Execution Plane)**: Orchestrator (Control) điều phối; API là transport. Chat endpoint phải gọi `regs["orchestrator"].handle()` + `regs["assistants"].resolve_by_intent()` (đã thấy trong `chat.py`), KHÔNG gọi `Tool(...)` trực tiếp.
- **INV-004 (Capability-first)**: Agent/API gọi Capability, KHÔNG gọi Tool trực tiếp.
- **INV-005 (DI)**: service resolve qua container/kernel; API dùng `RuntimeKernel.create()` + `build_registries`.
- **INV-006 (Dependency 1 chiều)**: `kernel → capability → tool → infra`; API/UI ở tầng trên cùng (Infra), import xuống được.
- **INV-007 (Hard call-site)**: policy check có call-site cố định.
- **INV-008 (Contract-first)**: giao tiếp qua contract (ChatRequest/ChatResponse pydantic, extra=forbid).
- **INV-009 (Event-driven)**: EventBus emit; WS forward event thực sự (verify `test_ws_events_realtime`).
- **INV-010 (Testability)**: mọi module có test; architecture invariants có AST scan test.
- **INV-013 (selection via router only)**: model selection qua ModelRouter; API `wiring.py` là composition root → được exempt.

**Fail-closed scanner (bắt buộc):** `tests/test_architecture.py` + AST scan. Xác nhận scanner báo cáo mọi file quét được, không silent-skip (0 xfail/skip hiệu dụng cho M3-relevant tests).

## 5. Dependency Rules
- import graph: `api/routers/*` import từ `aios_core.kernel`, `aios_core.agents`, `aios_core.orchestrator` — OK vì API là Infra layer.
- **circular dependency**: không có vòng lặp.
- **layer violation**: Dashboard/Extension GỌI API qua HTTP fetch (không import kernel). Verify `dashboard/src/api.ts`, `extension/src/client.ts` chỉ fetch `/api/v1/...`.

## 6. Runtime Wiring Review
- `create_app(settings, kernel, registries)`: kernel None → `RuntimeKernel.create(settings)`; registries None → `build_registries`. DI qua kernel/container.
- Negative test (bắt buộc): không có construction trực tiếp trái phép tại boundary. Verify chat router dùng `regs[...]` (injectable), không `ExecutionService()` / `Tool()` trực tiếp.

## 7. Contract Evolution
Đã verify M1. Reviewer xác nhận regression tests còn (`test_contracts.py` 4 case).

## 8. Workflow Contract Review
Đã verify M1. Definition không import engine cụ thể.

## 9. Capability Isolation (TRỌNG TÂM M3)
API/Dashboard/Extension **KHÔNG** gọi Tool trực tiếp. Tìm `DockerTool(...)` / `ShellTool(...)` bên trong `api/` / `dashboard/` / `extension/` → FAIL nếu có. Acceptance: `UI → API → Orchestrator → Capability → Tool`.

## 10. Policy Engine Review
Đã verify M1/M2. M3 API read-only + 1 action chat (offline-first). Verify không có mutation nguy hiểm qua API.

## 11. Event Review (MỚI — TRỌNG TÂM M3)
Event Bus emit events; **WS `/events/ws` forward thực sự**. Verify `events.py`: `bus.subscribe` → `call_soon_threadsafe(queue.put)` → `websocket.send_json`. Test `test_ws_events_realtime` publish cross-thread → ws nhận. Không chỉ assert "ws tồn tại" — phải assert nhận đúng event.

## 12. Resource Review
Đã verify M1/M2 (SandboxPool reuse). API `/sandbox` GET stats — read-only.

## 13. Context Review
Đã verify M1/M2. Dashboard không quản lý context.

## 14. Knowledge Graph
Đã verify M1.

## 15. Catalog
Đã verify M1. API `/catalog`, `/catalog/search`.

## 16. Prompt Registry
Đã verify M1. API `/prompts`.

## 17. CLI
Đã verify M1 (`--simulate`, `doctor`, ...). M3 thêm `aiagent serve`.

## 18. Runtime Crash
Đã verify M1.

## 19. Performance
M3 thêm API latency. Verify WS fan-out không block publish thread (queue + `call_soon_threadsafe`). Không yêu cầu benchmark cứng nhưng WS phải non-blocking.

## 20. Offline-first (MỚI — TRỌNG TÂM M3)
Chat endpoint offline-first: intent None → orchestrator.handle (mock model 0 call) → route. Verify `test_chat_coding_intent` (generate api → coding, "generated code" trong response) chạy với MockModel (0 real call). Extension/Dashboard gọi cùng endpoint.

## 21. UI/UX Review (MỚI — M3)
- Dashboard: 10 tabs render (test `App.test.tsx`); mỗi view mount đúng; api.ts parse `{data}`/`{error}`; ws.ts reconnect.
- Extension: 9 commands registered (test `extension.test.ts`); INTENTS map đúng bảng §4; selection guard (warning, không gọi API); fix/generate_test dùng `editor.edit` replace.

## 22. Acceptance Criteria (nguồn: PLAN.md §Verification M3 + task specs)

| # | Tiêu chí (nguồn) | Cách kiểm chứng | Bằng chứng mong đợi | Map mục 4 |
|---|---|---|---|---|
| V1 | Event timeline realtime qua WebSocket | `test_ws_events_realtime`: publish cross-thread → ws nhận đúng type/payload | msg["type"]=="workflow.completed", payload khớp | 4/11 + mục 11 |
| V2 | 9 lệnh extension end-to-end | `extension.test.ts`: 9 commands registered + intent map 9 cases + editor.edit cho fix + selection guard | handlers == 9 IDs; body.intent đúng; fetch không gọi khi no selection | 4/9 + mục 21 |
| V3 | Artifact browser hiển thị đủ loại | `ArtifactBrowser.tsx` render `artifact_type`; API `/artifacts` trả list có `artifact_type` | component map artifact_type → display; test_api `test_artifacts_and_conversations` | 4/9 + mục 21 |
| V4 | 10 Dashboard views | `App.tsx` TABS có 10 entries; `App.test.tsx` assert 10 tab labels | 10 tab-testid present | 4 + mục 21 |
| V5 | API 11 routers + chat offline-first | `test_api.py` (10 routers) + `test_api_chat_serve.py` (chat intent + 422) | routing + mock model 0 call | 4/3/20 |
| V6 | Architecture: API không gọi Tool trực tiếp | grep `Tool(`/`ExecutionService(` trong `api/`/`dashboard/`/`extension/` → empty; chat.py dùng orchestrator+assistants | static + runtime (chat test) | 4/9/INV-003 |
| V7 | Process: 8-file hard gate mỗi task | đếm file trong TASK-017/018/019 folders | mỗi folder đủ 8 file | 4 (mục 6 brief) |
| V8 | Tests chạy thật | pytest backend + vitest dashboard + vitest extension | 689+ pytest, 12 vitest dashboard, 19 vitest extension (tại M3) | 4/10 |

## 23. Phương pháp review (BẮT BUỘC làm đủ)
1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 22: tìm bằng chứng → kết luận **PASS/FAIL/INCONCLUSIVE** kèm trích dẫn `file:đường dẫn`
3. Áp dụng Architecture & Runtime Deep Review (mục 4.1–4.12 tương đương 4–22) — mỗi mục phải có kết luận rõ
4. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật)
5. Tìm lỗ hổng chủ động: file thiếu, stub không logic, mâu thuẫn, checkbox chưa tick, claim không có bằng chứng, **test pass nhưng không test đúng thứ cần test** (mục 12 template / mục 4.12)
6. Với mỗi task: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
7. Phân mức findings: **P1** (sai mục tiêu/tiêu chí), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 24. Format báo cáo trả về (bắt buộc đúng cấu trúc)
```markdown
# Review M3 — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả (PASS/FAIL/INCONCLUSIVE) | Bằng chứng (file + trích dẫn) |

## 2. Architecture Compliance
(đối chiếu mục 4–22: Runtime-first / Contract-first / Plugin-first / Engine-independent /
Capability-first / Policy-first / DI / Event-driven / Dependency / Wiring / Security /
Performance / Event Bus / Anti-fake-test — mỗi nguyên tắc ghi PASS/FAIL/INCONCLUSIVE + trích dẫn)

## 3. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 4. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 5. Điểm mạnh (nếu có)
## 6. Gợi ý cải thiện (không bắt buộc)
```

## 25. Final Gate (nâng cấp)
Kết quả mỗi tiêu chí thuộc một trong 3 trạng thái:
- **PASS**: Có bằng chứng trực tiếp và kiểm chứng được (đọc code + chạy test/CLI).
- **FAIL**: Có bằng chứng cho thấy không đạt.
- **INCONCLUSIVE**: Không đủ bằng chứng để kết luận.

**Milestone chỉ được ACCEPTED khi:**
- Tất cả tiêu chí mục 22 = **PASS** (không FAIL, không INCONCLUSIVE)
- Không có **P1** finding
- Không có **INCONCLUSIVE** nào trong bảng tiêu chí
- Các test bắt buộc chạy thành công trên môi trường review (hoặc có bằng chứng thực thi đáng tin cậy)

> Nếu có bất kỳ **INCONCLUSIVE** nào, milestone không được ACCEPTED cho đến khi reviewer có đủ bằng chứng nâng lên PASS hoặc FAIL.

---

## 26. Cách tạo bản điền sẵn cho milestone mới
Copy template này → đổi tên `{{MILESTONE}}-review-brief.md` → điền 4 placeholder: `{{MILESTONE}}`, `{{MILESTONE_DESCRIPTION}}`, `{{DELIVERABLE_LIST}}`, `{{AC_TABLE}}` (lấy AC từ PLAN.md mục Verification). Khi điền `{{AC_TABLE}}`, nhớ map mỗi tiêu chí với mục 4.1–4.12 tương ứng.
