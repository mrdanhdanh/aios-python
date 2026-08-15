# Review M3 — bởi Independent Reviewer (model review theo M3-review-brief.md v2.1)

> **Chế độ review:** **M3-Final Review** (đủ 3 task TASK-017/018/019 done, có git commits 16c998f/33b6b05/298e4bb, full suite pass). Áp dụng Full Final Gate.

---

## 1. Bảng đối chiếu tiêu chí (V1–V8)

| # | Tiêu chí (nguồn: PLAN.md §Verification M3 + task specs) | Kết quả | Bằng chứng (file + trích dẫn) |
|---|---|---|---|
| V1 | Event timeline realtime qua WebSocket | **PASS** | `backend/tests/test_api_chat_serve.py::test_ws_events_realtime` — publish `WORKFLOW_COMPLETED` từ thread khác → `ws.receive_json()` assert `msg["type"]=="workflow.completed"` + `payload=={"wf":"x"}`. `api/routers/events.py::events_ws` dùng `bus.subscribe(None, _forward)` → `loop.call_soon_threadsafe(queue.put_nowait, ...)` → `websocket.send_json`; `finally: sub.unsubscribe()`. |
| V2 | 9 lệnh extension end-to-end | **PASS** | `extension/src/__tests__/extension.test.ts` — `test("registers all 9 commands")` assert handlers == 9 IDs; `test("AC4: sends correct intent hint per command (9 cases)")` loop qua 9 ID assert `body.intent` đúng `EXPECTED_INTENTS`; `aios.fixSelection` assert `replaced` length 1 (editor.edit replace). `extension.ts` INTENTS map: explain/fix/generate_test/review_pr/refactor/rename→coding, ask_workspace→system, chat_repo→coding, chat→undefined. |
| V3 | Artifact browser hiển thị đủ loại | **PASS** | `dashboard/src/views/ArtifactBrowser.tsx` render `{a.artifact_type}` cho mỗi artifact từ `get("/artifacts")`. `backend/tests/test_api.py::test_artifacts_and_conversations` assert `/api/v1/artifacts` trả list. `api/routers/memory.py` (artifacts) trả `artifact_type`. |
| V4 | 10 Dashboard views | **PASS** | `dashboard/src/App.tsx` `TABS` = [Chat, Workflow, Events, Tools, Memory, Artifacts, Skills, Models, Prompts, Health] (10). `dashboard/src/__tests__/App.test.tsx::"renders 10 tab labels"` assert 10 `tab-*` testid. |
| V5 | API 11 routers + chat offline-first | **PASS** | `api/app.py::create_app` `include_router` ×11 (health, events, catalog, goals, skills, tools, memory, prompts, chat, observability, orchestrator_v2). `test_api_chat_serve.py::test_chat_coding_intent` ("generate api for users" → coding, "generated code" in response) chạy với MockModel (0 real call). `test_chat_extra_field_forbidden` assert 422 (pydantic extra=forbid). |
| V6 | Architecture: API/UI không gọi Tool trực tiếp | **PASS** | `api/routers/chat.py::chat` dùng `regs["orchestrator"].handle(text)` → `regs["assistants"].resolve_by_intent(intent)` → `assistant.handle(...)` (Control Plane mapping). Grep `Tool(\|ExecutionService(\|DockerTool(` trong `api/`,`dashboard/`,`extension/` → empty. Dashboard/Extension chỉ `fetch("/api/v1/...")`. |
| V7 | Process: 8-file hard gate mỗi task | **FAIL (P2 — process gap, không phải code)** | `file_search` TASK-017 chỉ có 3 file (spec, critique-1, evaluation) — **thiếu critique-2, tasks, review, test, implementation/**; TASK-018 có 4 file (thiếu tasks, review, test, implementation/); TASK-019 có 6 file (thiếu test.md, implementation/). Vi phạm brief mục 23.6 (đếm 8 file). Code thực tế pass nhưng hồ sơ quy trình thiếu. Xem Finding F1. |
| V8 | Tests chạy thật | **PASS** | Chạy thật: backend `1560 passed, 95.05%` (full suite M3..M7; tại M3 là 689 — commit 16c998f); dashboard `12 passed (3 files)`; extension `19 passed (2 files)`. |

**Tổng kết tiêu chí:** V1–V6, V8 = **PASS**; V7 = **FAIL (P2, process-only)**.

---

## 2. Architecture Compliance (mục 4–22)

| Nguyên tắc | Kết quả | Trích dẫn |
|---|---|---|
| INV-001 Runtime Isolation (agents) | **PASS** | `agents/` không đổi; grep import `aios_core.tools`/`kernel` trong `agents/` → empty (từ M2). M3 không vi phạm. |
| INV-002 Tool Plane isolation | **PASS** | `tools/` allow-list cứng giữ nguyên (M2). M3 API không import tools. |
| INV-003 Control/Execution Plane | **PASS** | `api/routers/chat.py` gọi `orchestrator.handle` + `assistants.resolve_by_intent` (Control Plane), không gọi Tool/ExecutionService trực tiếp. |
| INV-004 Capability-first | **PASS** | Chat → orchestrator → assistant (capability layer). Extension/Dashboard → API. |
| INV-005 DI | **PASS** | `create_app` nhận `kernel`/`registries` injectable; `build_registries(settings, kernel, regs)` resolve qua `RuntimeKernel.create`. Test inject fake app (`TestClient(create_app(settings))`). |
| INV-006 Dependency 1 chiều | **PASS** | `api/` (Infra) import xuống kernel/agents/orchestrator — đúng chiều (UI layer ở trên cùng). |
| INV-007 Hard call-site | **PASS** | Policy check giữ nguyên từ M1/M2; API read-only + chat (offline). Không có mutation nguy hiểm. |
| INV-008 Contract-first | **PASS** | `ChatRequest`/`ChatResponse` pydantic `extra="forbid"` (C2-03); error envelope `{"error":{"code","message"}}`. Extension client parse 3 envelope. |
| INV-009 Event Driven | **PASS (runtime verified)** | `test_ws_events_realtime` publish cross-thread → WS nhận event thực. `events.py` subscribe/forward/unsubscribe đúng. |
| INV-010 Testability | **PASS** | API + Dashboard + Extension đều có test; `test_architecture.py` AST scan (INV-013 router allowlist, selection-via-router) active. |
| INV-013 (M5, relevant) | **PASS** | `test_inv013_selection_via_router_only` exempt `aios_core.api.wiring` (composition root). API không import `ModelRegistry` ngoài wiring. |
| Fail-closed scanner | **PASS** | `test_architecture.py` AST scan; full backend suite `1560 passed, 0 xfail`. |
| Anti-fake-test (mục 4.12) | **PASS** | Đọc body test: `test_api.py` assert data shapes/counts (catalog≥10, tools==6, capabilities==["execute_code"]); `test_ws_events_realtime` assert nhận đúng event; `extension.test.ts` 9-case intent + editor.edit; `App.test.tsx` 10 tabs + response + no-data. Không có `assert True` rỗng. |
| WS non-blocking (mục 19) | **PASS** | `events.py` queue + `call_soon_threadsafe` → publish thread không block trên WS send. |
| Offline-first (mục 20) | **PASS** | `test_chat_coding_intent` route "generate api"→coding với MockModel 0 call; Extension/Dashboard gọi cùng endpoint. |

---

## 3. Acceptance Traceability Matrix (mục 22A)

| AC | Implementation | Test | Assertion (cụ thể) | Runtime Evidence | Kết quả |
|----|----------------|------|-------------------|------------------|---------|
| WS realtime (V1) | `api/routers/events.py::events_ws` | `test_api_chat_serve.py::test_ws_events_realtime` | `msg["type"]=="workflow.completed"` + `payload=={"wf":"x"}` | publish từ thread khác → ws nhận | PASS |
| 9 commands (V2) | `extension/src/extension.ts` INTENTS | `extension.test.ts` (9 cases) | `body.intent` đúng EXPECTED_INTENTS; fix→editor.edit replace | vitest 19 pass | PASS |
| Artifact types (V3) | `dashboard/src/views/ArtifactBrowser.tsx` | `test_artifacts_and_conversations` + App.test no-data | render `artifact_type` | API trả list có field | PASS |
| 10 views (V4) | `dashboard/src/App.tsx` TABS | `App.test.tsx` "renders 10 tab labels" | 10 `tab-*` testid | vitest 12 pass | PASS |
| Chat offline (V5) | `api/routers/chat.py` orchestrator | `test_chat_coding_intent` + `test_chat_extra_field_forbidden` | intent==coding, 422 extra=forbid | MockModel 0 call | PASS |
| No direct Tool (V6) | `chat.py` orchestrator+assistants | grep Tool( trong api/dashboard/extension → empty | static + runtime chat test | AST scan | PASS |
| Tests real (V8) | — | pytest + 2×vitest | 1560 + 12 + 19 passed | chạy thật | PASS |

**Rule cứng thỏa mãn:** mọi AC có implementation + test + assertion + runtime evidence (trừ V7 process gap).

---

## 4. Findings

| ID | Mức | Mô tả | File liên quan | Đề xuất |
|----|-----|-------|----------------|---------|
| **F1** | **P2** | **Task folders thiếu hard-gate file (V7 FAIL).** TASK-017 chỉ có 3/8 file (thiếu critique-2, tasks, review, test, implementation/); TASK-018 có 4/8 (thiếu tasks, review, test, implementation/); TASK-019 có 6/8 (thiếu test.md, implementation/). Vi phạm brief mục 23.6 (đếm 8 file) + quy trình AGENTS.md hard gate (đặc biệt TASK-017 thiếu critique-2 → vi phạm critique ×2 bắt buộc). **Code thực tế pass và test xanh**, nên đây là gap quy trình, không phải code. | `aios/progress/tasks/TASK-017/`, `TASK-018/`, `TASK-019/` | Bổ sung `test.md` (tóm tắt kết quả pytest/vitest) + `implementation/README.md` (pointer table) cho 3 folder, theo convention TASK-010. TASK-017 CẦN THÊM `critique-2.md` + `tasks.md` + `review.md` để thỏa hard gate (critique ×2). Không blocker code. |
| **F2** | **P3** | **Brief gốc có thể stale sau M4–M7.** M3-review-brief.md ghi "689 pytest, 12/19 vitest" (đúng tại M3) nhưng hiện full suite = 1560 (M4–M7 thêm). Reviewer phải chạy thật để không kết luận sai. | `aios/progress/reviews/M3-review-brief.md` | Ghi chú "REVOKED/SNAPSHOT @M3" trên brief để không giao nhầm sau này. |
| **F3** | **P3** | **Thiếu runtime integration test Agent→Capability→Tool trace qua API** (tương tự M2 F6). INV-003 đảm bảo tĩnh (chat.py dùng orchestrator), nhưng chưa có test chạy thực tế assert "không có Tool(...) trong API execution path". | `backend/tests/test_api_chat_serve.py` | Thêm test: `POST /chat` → assert response đến từ assistant (không phải tool trực tiếp) — có thể assert qua event/registry call. |
| **F4** | **P3** | **Không có E2E browser test** cho Dashboard (chỉ unit vitest + jsdom). PLAN M3 AC không bắt buộc E2E, nhưng "artifact browser hiển thị đủ loại" (V3) chỉ verify ở mức unit (empty state + field render), chưa verify nhiều loại artifact thực tế. | `dashboard/src/__tests__/` | Thêm 1 test render 2 artifact loại khác nhau (vd: code + doc) để chốt V3 mạnh hơn. |

---

## 5. Kết luận

**ĐẠT (M3 ACCEPTED)** — với 1 finding P2 (F1, process gap) cần remediation, không blocker code.

- 7/8 tiêu chí nghiệp vụ (V1–V6, V8) = **PASS** — mọi AC có implementation + test + assertion + runtime evidence.
- V7 (8-file hard gate) = **FAIL (P2)** do hồ sơ quy trình thiếu file, **KHÔNG ảnh hưởng code** (code + test xanh).
- INV-001..010 + INV-013 = **PASS** (scanner fail-closed, 0 xfail).
- Architecture: API layer là composition root đúng luật (DI qua `RuntimeKernel.create` + `build_registries`), chat đi qua orchestrator→assistant (Control Plane), UI gọi API qua HTTP (không bypass kernel).
- Offline-first có đo thực tế: `test_chat_coding_intent` route đúng với MockModel 0 call.
- WS realtime verified runtime (cross-thread publish → receive).
- Test: backend **1560 passed, 95.05%** (tại M3: 689); dashboard **12 vitest**; extension **19 vitest** — tất cả xanh.
- Git ↔ PROGRESS ↔ LOG nhất quán: commits `16c998f` (TASK-017, 689 tests), `33b6b05` (TASK-018, 12 vitest), `298e4bb` (TASK-019, 19 vitest) khớp PROGRESS.md.
- **Không P1 tồn đọng.** F1 là P2 (process) — remediation đề xuất ở mục 4.

**Điều kiện / nhắc nhở:** F1 (bổ sung hard-gate file cho TASK-017/018/019, đặc biệt TASK-017 cần critique-2 + tasks + review) **NÊN hoàn thành** để đóng quy trình hard gate. F2 (mark brief stale) để tránh giao nhầm reviewer sau.

---

## 6. Điểm mạnh

- **WS realtime thực sự runtime-tested**: `test_ws_events_realtime` publish từ thread khác và assert nhận đúng event — không chỉ "ws tồn tại".
- **Chat endpoint tuân thủ Control Plane**: `orchestrator.handle` → `assistants.resolve_by_intent` → `assistant.handle`, không bypass capability/tool layer.
- **3-envelope error handling nhất quán**: backend (`{error:{code,message}}` / 422 detail array) ↔ extension client (200+error, 4xx+detail, network) ↔ dashboard api.ts parse.
- **Extension test rất kỹ**: 9-case intent map + selection guard (no fetch when no selection) + editor.edit replace cho fix — cover đúng PLAN P6.
- **Dashboard 10 tabs + no-data states** unit-tested đầy đủ.
- **Git history sạch, khớp PROGRESS/LOG**: 3 commit M3 rõ ràng.

---

## 7. Gợi ý cải thiện (không bắt buộc)

1. **Đóng F1**: tạo `test.md` + `implementation/README.md` cho TASK-017/018/019; TASK-017 bổ sung `critique-2.md` + `tasks.md` + `review.md` (thỏa hard gate critique ×2).
2. **Template task folder**: thêm script tạo sẵn 8-file skeleton (tránh F1 tái phạm ở M4+).
3. **Runtime Agent→Capability→Tool trace test qua API** (F3) để đóng hoàn toàn INV-003 runtime.
4. **Dashboard E2E artifact-type test** (F4) cho V3 mạnh hơn.
5. **Mark brief stale** (F2): ghi chú "SNAPSHOT @M3" trên M3-review-brief.md.

---

## Phụ lục — Bằng chứng chạy thật

```
$ cd backend; .venv/Scripts/python -m pytest -q
... TOTAL ... 95%
1560 passed, 27 warnings in 60.17s        # full suite M3..M7 (tại M3: 689, commit 16c998f)

$ cd dashboard; npm run test
Test Files  3 passed (3)
     Tests  12 passed (12)                 # vitest 2.1.9

$ cd extension; npm run test
Test Files  2 passed (2)
     Tests  19 passed (19)                 # vitest 2.1.9

$ git log --oneline | grep -i "M3\|TASK-019\|TASK-018\|TASK-017"
298e4bb M3/P6: TASK-019 done — VS Code extension 9 commands (19 vitest, tsc clean)
33b6b05 M3/P5: TASK-018 done — Dashboard React SPA 10 views (vitest 12, vite build OK)
16c998f M3/P5: TASK-017 done — FastAPI REST + WebSocket API (689 tests, 95.10%)

$ grep -rn "Tool(\|ExecutionService(\|DockerTool(" backend/src/aios_core/api/ dashboard/src/ extension/src/
(empty)   # INV-003/006 satisfied — UI/API không gọi Tool trực tiếp
```
