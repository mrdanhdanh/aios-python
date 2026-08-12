# Review M1 — Core Runtime

> **Bản điền sẵn từ** `REVIEW-BRIEF-TEMPLATE.md` — đem cho model khác review độc lập.
> Copy TOÀN BỘ file này sang model review. Model tự đọc repo, tự kết luận — không xem bản review nội bộ nào trước đó.

---

## 1. Bối cảnh dự án (đọc TRƯỚC khi review)

Dự án **AIOS** (AI Operating System) — hệ điều hành agent chạy local desktop, phát triển theo milestone (M0–M4). Quy trình bắt buộc cho mọi task: plan → spec → critique ×2 → tasks → review → implement → test → evaluate (hard gate).

Đọc bắt buộc:
- `docs/PLAN.md` — master plan. **Đặc biệt mục "M1 – Core Runtime" + mục "Verification (theo milestone)"** (tiêu chuẩn nghiệm thu)
- `AGENTS.md` — quy tắc vận hành dự án

## 2. Nhiệm vụ

Review milestone **M1** — Core Runtime (P0–P2): infrastructure (`aios_core`), Runtime Kernel 9 services, contracts version hóa, model providers (Mock/OpenAI/Ollama), memory 4 loại + knowledge pipeline, workflow definition + compilers, capability discovery, prompt registry, System Catalog, Knowledge Graph.

Đánh giá độc lập 3 khía cạnh:
1. **Đúng phạm vi**: deliverable có đúng như PLAN hứa cho M1 không (9 task: TASK-002 → TASK-009)
2. **Đúng quy trình**: hard gate có được tuân thủ cho từng task không (spec/critique ×2/tasks/review/test/evaluate)
3. **Hồ sơ nhất quán**: PROGRESS.md ↔ LOG.md ↔ git history ↔ file thực tế ↔ kết quả test có khớp nhau không

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
| 11 | `test_policy.py`, `test_runtime_kernel.py`, `test_integration.py`, `test_semver.py`, `test_contracts.py`, `test_catalog.py`, `test_knowledge_graph.py`, `test_compiler.py`, `test_cli.py`, `test_state.py` | Có test cho từng tiêu chí mục 4 (đọc + chạy) |

### 3.3 Hồ sơ quy trình (hard gate)

| # | Đường dẫn | Kiểm tra gì |
|---|-----------|-------------|
| 12 | `aios/progress/tasks/TASK-002/` … `TASK-009/` | **8 task M1, mỗi task đủ 8 file**: spec.md, critique-1.md, critique-2.md, tasks.md, review.md, test.md, evaluation.md, implementation/ |
| 13 | `aios/progress/PROGRESS.md` | Mục M1: P0/P0.5/P1/P2, trạng thái từng task, khớp git history |
| 14 | `aios/progress/LOG.md` | Entry cho từng bước implement + test của TẤT CẢ 8 task, đúng format |
| 15 | `aios/progress/STATS.md` | Mục M1: 9 task done, 346 tests, critique resolve, bypass |
| 16 | Git history | `git log --oneline` — có commit "M1 HOÀN TẤT (9/9 tasks, 346 tests, 95.3%)" + commit code từng task |

## 4. Tiêu chí chấp nhận (nguồn: PLAN.md → Verification M1)

| # | Tiêu chí | Cách kiểm chứng | Bằng chứng mong đợi |
|---|----------|------------------|---------------------|
| V1 | Contract tests: semver + compatibility đúng (major = breaking, minor = backward-compatible) | Đọc + chạy `backend/tests/test_semver.py`, `test_contracts.py` | Tests pass; đọc code `semver.py` + `contracts/` thấy logic đúng chiều |
| V2 | Đổi engine langgraph→mock **không đổi** workflow definition | Đọc `workflow/`: definition là declarative contract độc lập engine; 2 compiler cùng nhận 1 definition | Workflow definition không import engine; compiler là lớp riêng, đổi compiler không đụng definition |
| V3 | Simulation chạy **không cần** Docker/LLM | Chạy thử `aiagent run workflow.yaml --simulate` (hoặc test tương đương) | Chạy được không cần Docker/LLM; MockCompiler không gọi model |
| V4 | Snapshot → kill → resume hoạt động | Đọc test_state.py + code state service/execution service | Test snapshot/resume pass; checkpoint lưu state + có cơ chế khôi phục sau crash |
| V5 | **Policy pre-check**: request cần internet nhưng policy deny → reject **trước khi execution** | Đọc test_policy.py + policy service | Có test chứng minh reject xảy ra trước khi workflow chạy (trước execution) |
| V6 | **Catalog search** không quét registry | Đọc catalog service + test_catalog.py | SystemCatalog dùng index/search, không duyệt từng registry mỗi lần search |
| V7 | **Knowledge Graph**: "agent nào dùng execute_code" trả lời O(1) | Đọc knowledge_graph + test_knowledge_graph.py | Có test query quan hệ; truy vấn qua index/edges, không quét toàn bộ |

**Deliverable M1 (PLAN.md)**: `aiagent run workflow.yaml --simulate` chạy được — kiểm chứng bằng CLI thật hoặc test_cli.py.

## 5. Phương pháp review (BẮT BUỘC làm đủ)

1. Đọc thực tế từng file trong mục 3 — **không tin mô tả**, phải thấy bằng chứng trong file
2. Với mỗi tiêu chí mục 4: tìm bằng chứng → kết luận **PASS/FAIL** kèm trích dẫn `file:đường dẫn`
3. Kiểm tra chéo 3 nguồn: PROGRESS.md ↔ LOG.md ↔ `git log --oneline` (chạy lệnh thật nếu có quyền)
4. Tìm lỗ hổng chủ động: file thiếu, stub không có logic, mâu thuẫn giữa các file, checkbox chưa tick, claim không có bằng chứng, test pass nhưng không test đúng thứ cần test
5. Với mỗi task TASK-002→009: đếm đủ 8 file (spec, critique-1, critique-2, tasks, review, test, evaluation, implementation/)
6. Phân mức findings: **P1** (sai mục tiêu/tiêu chí — phải sửa trước khi chấp nhận), **P2** (thiếu sót đáng sửa), **P3** (góp ý nhỏ)

## 6. Format báo cáo trả về (bắt buộc đúng cấu trúc)

```markdown
# Review M1 — bởi <tên model / reviewer>

## 1. Bảng đối chiếu tiêu chí
| # | Tiêu chí | Kết quả | Bằng chứng (file + trích dẫn) |

## 2. Findings
| ID | Mức (P1/P2/P3) | Mô tả | File liên quan | Đề xuất |

## 3. Kết luận
- ĐẠT / CHƯA ĐẠT (kèm điều kiện nếu có)
- Lý do ngắn gọn

## 4. Điểm mạnh (nếu có)
## 5. Gợi ý cải thiện (không bắt buộc)
```
