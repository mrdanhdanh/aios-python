# Review M1 — Core Runtime (template nâng cấp v2)

> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem bản review nội bộ nào trước đó.
>
> **Lưu ý cho reviewer:** Template v2 chuyển trọng tâm từ *existence review* (file có tồn tại không) sang **runtime correctness & architecture review** (kiến trúc có đúng không, runtime có hoạt động đúng không). Bắt buộc áp dụng các mục 4–22 trước khi kết luận.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M4). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M1 – Core Runtime" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu)
- `AGENTS.md` — quy tắc vận hành dự án
- `docs/adr/` (nếu có) — các quyết định kiến trúc đã ghi nhận (xem mục 21)

## 2. Nhiệm vụ

Review milestone **M1** — Core Runtime (P0–P2): infrastructure (`aios_core`), Runtime Kernel 9 services, contracts version hóa, model providers (Mock/OpenAI/Ollama), memory 4 loại + knowledge pipeline, workflow definition + compilers, capability discovery, prompt registry, System Catalog, Knowledge Graph.

Đánh giá độc lập 4 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M1 không (9 task: TASK-002 → TASK-009)
2. **Đúng quy trình**: hard gate có được tuân thủ cho từng task không (spec/critique ×2/tasks/review/test/evaluate)
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế ↔ kết quả test có khớp nhau không
4. **Đúng kiến trúc & runtime correctness**: kiến trúc có tuân thủ nguyên tắc AIOS không, runtime có hoạt động đúng không (xem mục 4–22)

## 3. Deliverable cần kiểm tra

### 3.1 Code (backend, src layout — package `aios_core` tại `backend/src/aios_core/`)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 1 | `backend/src/aios_core/config.py`, `logging.py`, `metadata.py`, `healthcheck.py`, `container.py`, `semver.py` | Tồn tại, có nội dung thật (không phải stub), khớp mô tả task |
| 2 | `backend/src/aios_core/contracts/` | Contract version hóa + compatibility checker (major/minor) |
| 3 | `backend/src/aios_core/kernel/` | 9 services: execution, context, event, artifact, permission, policy, scheduler, state, resource + RuntimeKernel wiring + events + execution plan |
| 4 | `backend/src/aios_core/models/` | ModelContract (template-method) + Mock/OpenAI/Ollama + ModelRegistry |
| 5 | `backend/src/aios_core/memory/` | Memory: conversation (SQLite), session (cache), vector store |
| 6 | `backend/src/aios_core/knowledge/` + `knowledge_graph/` | Knowledge pipeline (chunks → embedder → store → retriever) + Knowledge Graph |
| 7 | `backend/src/aios_core/workflow/` | Workflow definition declarative + DAG + MockCompiler + LangGraph (stub/optional) + Library |
| 8 | `backend/src/aios_core/capabilities/`, `prompts/`, `catalog/` | CapabilityRegistry (discovery), PromptRegistry, SystemCatalog (index/search) |
| 9 | CLI simulate | `aiagent run workflow.yaml --simulate` — tìm CLI entrypoint (xem `backend/pyproject.toml` + `backend/src/aios_core/workflow/cli.py` hoặc tương đương) |

### 3.2 Tests (chạy thật)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 10 | `backend/tests/` | ~34 file test; chạy `pytest` trong `backend/` (venv: `backend/.venv/Scripts/python -m pytest`) — mong đợi **346 tests pass, coverage ~95%** |
| 11 | `test_policy.py`, `test_runtime_kernel.py`, `test_integration.py`, `test_semver.py`, `test_contracts.py`, `test_catalog.py`, `test_knowledge_graph.py`, `test_compiler.py`, `test_cli.py`, `test_state.py`, `test_resource.py`, `test_context.py`, `test_events.py`, `test_vector.py`, `test_capabilities.py`, `test_prompts.py`, `test_permissions.py` | Có test cho từng tiêu chí mục 23 (đọc + chạy). **Quan trọng:** đọc body test (mục 22) |

### 3.3 Hồ sơ quy trình (hard gate)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 12 | `aios/progress/tasks/TASK-002/` … `TASK-009/` | **8 task M1, mỗi task đủ 8 file**: spec.md, critique-1.md, critique-2.md, tasks.md, review.md, test.md, evaluation.md, implementation/ |
| 13 | `aios/progress/PROGRESS.md` | Mục M1: P0/P0.5/P1/P2, trạng thái từng task, khớp git history |
| 14 | `aios/progress/LOG.md` | Entry cho từng bước implement + test của TẤT CẢ 8 task, đúng format |
| 15 | `aios/progress/STATS.md` | Mục M1: 9 task done, 346 tests, critique resolve, bypass |
| 16 | Git history | `git log --oneline` — có commit "M1 HOÀN TẤT (9/9 tasks, 346 tests, 95.3%)" + commit code từng task |

---

## 4. Architecture Compliance (TRỌNG TÂM M1)

Reviewer phải xác minh kiến trúc AIOS tuân thủ các nguyên tắc cốt lõi — **KHÔNG chỉ xem file tồn tại**. Phải xác minh dependency graph (dùng `grep` import hoặc đọc `from/import`).

Nguyên tắc bắt buộc:
- **Runtime-first**: logic nghiệp vụ chạy trong Runtime Kernel, không rải rác ở CLI/agent.
- **Contract-first**: giao tiếp qua contract, không qua kiểu dữ liệu nội bộ.
- **Plugin-first**: capability/tool/model có thể cắm thêm mà không sửa core.
- **Engine-independent**: workflow definition độc lập engine (xem mục 8).
- **Capability-first**: agent gọi capability, không gọi tool trực tiếp (xem mục 9).
- **Policy-first**: mọi request bị policy pre-check (xem mục 10).
- **Dependency Injection**: service được resolve qua container (xem mục 6).
- **Event-driven**: runtime phát event qua Event Bus (xem mục 11).

Ví dụ đúng:
```
Workflow → Capability → Tool
```
Sai (FAIL):
```
Workflow → Docker
```

## 5. Dependency Rules

Reviewer kiểm tra import graph:
- **import graph**: layer trên không import ngược layer dưới một cách sai nguyên tắc.
- **circular dependency**: không có vòng lặp import (đọc `from/import` các module).
- **layer violation**: Tool / layer thấp không được import Runtime Kernel (layer cao).

Ví dụ đúng:
```
Kernel → Capability → Tool
```
Sai (FAIL): Tool import `RuntimeKernel` hoặc `ExecutionService` trực tiếp.

## 6. Runtime Wiring Review

Không chỉ ghi "Runtime Kernel wiring". Phải xác minh:
- **Service registration**: service được đăng ký vào container.
- **Lifecycle**: init / start / stop rõ ràng.
- **Singleton / Scoped**: đúng scope (service chia sẻ vs per-request).
- **DI resolve**: service được resolve qua container.

Đúng:
```
Runtime → Container → ExecutionService (resolve)
```
Sai:
```
ExecutionService()   # tạo trực tiếp rải rác khắp code
```

## 7. Contract Evolution (mở rộng V1)

Old Contract → Compatibility Checker → New Contract. Các case phải có test/code xử lý:

| Case | Kết quả |
|------|---------|
| add field | PASS (backward-compatible) |
| remove required field | FAIL (breaking) |
| rename field | FAIL (breaking) |
| optional → required | FAIL (breaking) |

Reviewer phải chạy/đọc test cho 4 case này (đọc `test_contracts.py`, `test_semver.py`).

## 8. Workflow Contract Review (mở rộng V2/V3)

Workflow Definition **KHÔNG** được import:
- LangGraph
- Docker
- Model

Nếu có → **FAIL**. Workflow definition là declarative contract độc lập engine; compiler là lớp riêng.

## 9. Capability Isolation (MỚI)

Acceptance: `Agent → Capability → Tool`.
Reviewer phải **TÌM** `DockerTool(...)` (hoặc tool cụ thể) bên trong Agent.
Nếu Agent khởi tạo Tool trực tiếp → **FAIL**. Capability là lớp trung gian, Agent không trực tiếp khởi tạo Tool cụ thể.

## 10. Policy Engine Review (mở rộng V5)

Không chỉ internet. Policy pre-check phải cover TẤT CẢ:
- filesystem
- shell
- docker
- network
- clipboard

Tất cả đều reject **TRƯỚC execution** (xem `test_policy.py` có cover từng scope).

## 11. Event Review (MỚI)

Event Bus phải **emit** các event (đọc event bus + emit sites, không chỉ định nghĩa):
- Execution Started / Finished
- Tool Started / Finished
- Policy Denied
- Snapshot Saved

Reviewer xác minh các emit thực sự được gọi trong code path.

## 12. Resource Review (MỚI)

Resource Service phải có test cho:
- allocate
- queue
- reject
- release

## 13. Context Review (MỚI)

6 context. Reviewer kiểm tra:
- **isolation**: context A không đọc context B
- **TTL**
- **cleanup**
- **inheritance**

## 14. Knowledge Graph (mở rộng V7)

Không chỉ O(1). Phải có:
- add node
- remove node
- update edge
- **consistency**: index `_out/_in` đồng bộ sau mọi CRUD

## 15. Catalog (mở rộng V6)

Ngoài search. Reviewer review:
- rebuild index
- incremental update
- stale index (index cũ không dùng được sau update)

## 16. Prompt Registry (MỚI)

Acceptance:
- version
- schema
- variable validation
- template compile

## 17. CLI (mở rộng V3)

Ngoài `--simulate`, phải có:
- `doctor`
- `catalog`
- `workflow validate`
- `contract validate`

## 18. Runtime Crash (mở rộng V4)

Không chỉ snapshot. Phải cover:
```
Execution → Crash → Restart → Resume
```
Reviewer kiểm tra resume sau crash thực sự khôi phục state (đọc `test_state.py` / execution service).

## 19. Performance (MỚI)

M1 là Runtime — phải có benchmark tối thiểu:
- catalog search < 5 ms
- workflow compile < 50 ms
- capability lookup O(1)

## 20. Security Review (MỚI)

Reviewer kiểm tra:
- permission bypass
- direct tool access (vượt capability)
- unsafe import
- shell injection

## 21. Architecture Decision Record (MỚI)

Reviewer đọc `docs/adr/` (nếu có) để xem implementation có đúng quyết định kiến trúc không.

## 22. Anti Fake Test (RẤT QUAN TRỌNG)

Không chỉ "346 tests pass". Reviewer phải kiểm tra coverage thật sự cover Acceptance Criteria.
Ví dụ: `test_policy.py` chỉ `assert True` vẫn pass nhưng không test đúng → phải bị bắt.
Phải **đọc body test**, không chỉ đếm số pass. Kiểm tra mỗi test có assert đúng behavior hay chỉ pass bề mặt.

---

## 23. Tiêu chí chấp nhận (nguồn: PLAN.md → Verification M1 + mở rộng)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|------------------|---------------------|
| V1 | Contract tests: semver + compatibility đúng (major = breaking, minor = backward-compatible) + Contract Evolution (mục 7) | Đọc + chạy `test_semver.py`, `test_contracts.py` | Tests pass; 4 case (add / remove required / rename / optional→required) đúng chiều |
| V2 | Đổi engine langgraph→mock **không đổi** workflow definition + Workflow Contract (mục 8) | Đọc `workflow/`: definition không import LangGraph/Docker/Model; 2 compiler cùng nhận 1 definition | Workflow definition độc lập engine |
| V3 | Simulation chạy **không cần** Docker/LLM + CLI subcommands (mục 17) | Chạy `aiagent run workflow.yaml --simulate` + `doctor` / `catalog` / `workflow validate` / `contract validate` | Chạy không cần Docker/LLM; MockCompiler không gọi model; subcommands tồn tại |
| V4 | Snapshot → kill → resume + Runtime Crash (mục 18) | Đọc test_state.py + execution service | Test snapshot/resume + crash→restart→resume pass |
| V5 | **Policy pre-check** tất cả scope (mục 10): internet/filesystem/shell/docker/network/clipboard → reject **trước execution** | Đọc test_policy.py + policy service | Có test từng scope; reject xảy ra trước execution |
| V6 | **Catalog search** không quét registry + index lifecycle (mục 15) | Đọc catalog service + test_catalog.py | Dùng index/search; rebuild / incremental / stale index được xử lý |
| V7 | **Knowledge Graph** O(1) + CRUD consistency (mục 14) | Đọc knowledge_graph + test_knowledge_graph.py | Test query O(1) + add/remove/update/consistency |

**Deliverable M1 (PLAN.md)**: `aiagent run workflow.yaml --simulate` chạy được — kiểm chứng bằng CLI thật hoặc test_cli.py.

**Các tiêu chí architecture (mục 4–22)** phải được reviewer xác minh riêng và báo cáo trong subsection "Architecture Compliance" (xem mục 25).

## 24. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 23: tìm bằng chứng → kết luận **PASS/FAIL/INCONCLUSIVE** kèm trích dẫn `file:đường dẫn`
3. Áp dụng Architecture Compliance (mục 4), Dependency Rules (mục 5), Runtime Wiring (mục 6), và các mục 7–22 — mỗi mục phải có kết luận rõ
4. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật nếu có quyền)
5. Tìm lỗ hổng chủ động: file thiếu, stub không có logic, mâu thuẫn, checkbox chưa tick, claim không có bằng chứng, **test pass nhưng không test đúng thứ cần test** (mục 22)
6. Với mỗi task TASK-002→009: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
7. Phân mức findings: **P1** (sai mục tiêu/tiêu chí — phải sửa trước khi chấp nhận), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 25. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review M1 — bởi <tên model / reviewer>

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

## 26. Final Gate (nâng cấp)

Kết quả mỗi tiêu chí thuộc một trong 3 trạng thái:
- **PASS**: Có bằng chứng trực tiếp và kiểm chứng được (đọc code + chạy test/CLI).
- **FAIL**: Có bằng chứng cho thấy không đạt.
- **INCONCLUSIVE**: Không đủ bằng chứng để kết luận (reviewer không có quyền chạy, thiếu file, hoặc mâu thuẫn không giải được).

**Milestone M1 chỉ được ACCEPTED khi:**
- V1–V7 = **PASS** (không FAIL, không INCONCLUSIVE)
- Không có **P1** finding
- Không có **INCONCLUSIVE** nào trong bảng tiêu chí
- Các test bắt buộc (mục 3.2) chạy thành công trên môi trường review (hoặc có bằng chứng thực thi đáng tin cậy nếu reviewer không có quyền chạy)

> Nếu có bất kỳ **INCONCLUSIVE** nào, milestone không được ACCEPTED cho đến khi reviewer có đủ bằng chứng nâng lên PASS hoặc FAIL.
