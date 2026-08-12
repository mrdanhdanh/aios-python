# TASK-009 — M1/P2b: Capability + Prompt Registry + System Catalog + Knowledge Graph

## Mục tiêu
4 thành phần cuối của M1 — nền cho AIOS Orchestrator (M2):
1. **Capability Registry**: agent chỉ biết capability (execute_code, read_file...) — tool khai báo capabilities, registry map capability ↔ tool; nền Capability Router M2
2. **Prompt Registry**: template (jinja2-style v1: string .format) → variables → version → evaluation; prompt first-class (PLAN)
3. **System Catalog**: index + search metadata toàn hệ thống (không quét registry mỗi lần) — "mục lục" AIOS
4. **Knowledge Graph**: đồ thị Agent–Skill–Workflow–Capability–Tool–Artifact–Model–Prompt (nodes + edges, versioned), trả lời quan hệ nhanh ("capability execute_code được dùng bởi agent nào")

## Phạm vi
- **In** (thuộc `backend/src/aios_core/`):
  1. `capabilities/registry.py` — `Capability` dataclass (name, description, tools: list[str]); `CapabilityRegistry`: `register_capability(name, description)`, `bind_tool(capability, tool_id)` (**unknown capability → CapabilityError; tool_id string tự do — chưa có Tool Registry; trùng → idempotent**), `unbind_tool` (unknown → CapabilityError; idempotent), `get(capability)` (unknown → CapabilityError), `tools_for(capability)` (unknown → CapabilityError), `list()`, `register_agent_use(agent_id, capability)` (**agent_id rỗng → ValueError; unknown → CapabilityError; trùng (agent, capability) → idempotent set**), `agents_using(capability)` (unknown → CapabilityError); thread-safe lock; duplicate register → overwrite + warning; **ghi chú: M2 graph populate đọc từ registry (registry = nguồn chính); get() trả object — caller không mutate**
  2. `prompts/registry.py` — `PromptTemplate` pydantic: `id, name, version (semver), template: str, variables: list[str] (TỰ extract + validate CÙNG LÚC CONSTRUCT qua pydantic model_validator — object hỏng không tồn tại; regex `(?<!\{)\{([A-Za-z_]\w*)\}(?!\})`, dedup giữ thứ tự; **scan trái→phải: (1) `{{`/`}}` → escape nhảy 2; (2) field regex tại vị trí → nhảy qua; (3) còn lại → PromptError — bắt `{score:.2f}`, `{}`, `{0}`, `{name}}`, `{{{name}}}`**), description`; `PromptRegistry`: `register(prompt)` (**overwrite + warning CHỈ khi trùng (id, version); version khác → thêm entry**), `get(id, version=None)` (**None → mới nhất = max theo semver.compare() TASK-003; unknown id HOẶC version → PromptError**), `list()` (insertion order), `render(id, variables, version=None)` (**bọc KeyError/ValueError → PromptError kèm tên biến; escape render literal; thiếu variable → PromptError; extra variable bỏ qua; variable value=None chấp nhận (str.format "None")**), `evaluate(id, score, note="")` (**id unknown → PromptError; bind version mới nhất + append CÙNG critical section**), `evaluations(id, version=None)` (**id unknown → PromptError; None = TOÀN BỘ history thứ tự append; có version → lọc; PromptEvaluation(version, score, note, timestamp UTC ISO)**); thread-safe
  3. `catalog/catalog.py` — `SystemCatalog`: `index_entry(kind, id, metadata)` (upsert), `remove_entry(kind, id)` (**unknown → idempotent im lặng**), `search(query, kind=None)` (**query rỗng → trả toàn bộ; đệ quy dict/list so `str(value).lower()` cho scalar — **bỏ qua value None**; KEY KHÔNG search; kind filter = exact; kết quả sorted (kind, id)**), `get(kind, id)` (unknown → CatalogError), `count()`; in-memory + lock
  4. `knowledge_graph/graph.py` — `KnowledgeGraph`: `add_node(kind, id, properties)` (trùng → overwrite + warning; **quy ước properties có thể chứa key "version" — không bắt buộc**), `add_edge(source_kind, source_id, relation, target_kind, target_id)` (**node không tồn tại → GraphError — không auto-create; relation rỗng → ValueError; self-loop cho phép v1 (ghi chú); trùng (source, relation, target) → idempotent skip**), `get_node(kind, id)` (unknown → GraphError), `neighbors(kind, id, relation=None)` (**trả (relation GỐC, đầu kia); dedup set giữ thứ tự ổn định; reverse lookup cùng label**) -> list[tuple[str, str]], `find(kind=None, property_key=None, property_value=None)` (**property tầng 1; property_value=None → bỏ qua value, trả node có key; so sánh == đúng kiểu; value thật sự None — chấp nhận v1**), `delete_node(kind, id)` (cascade edges 2 chiều); in-memory dict + lock; **ghi chú: knowledge_graph/ (mối quan hệ component) KHÁC knowledge/ (RAG chunks TASK-007)**
  5. errors: `capabilities/errors.py` (CapabilityError), `prompts/errors.py` (PromptError), `catalog/errors.py` (CatalogError), `knowledge_graph/errors.py` (GraphError)
  6. `__init__.py` exports + re-export ở `aios_core/__init__.py`
  7. Tests: test_capabilities, test_prompts, test_catalog, test_knowledge_graph (4 file)
- **Out (không làm)**: **SQLite persist cho catalog/graph → M4 (đã amend PLAN.md — quyết định in-memory v1)**; jinja2 dep (v1 str.format subset); prompt A/B testing thật (M4); **catalog auto-sync từ registry + graph auto-build từ events → M2 (populate thủ công v1)**; fuzzy search; nested property match trong find (M2); **auto-discovery capability từ ToolContract scan → M2**

## Yêu cầu chi tiết
1. **CapabilityRegistry**: `register_capability` name non-empty; `bind_tool` tool_id non-empty; unbind idempotent; agents_using qua `register_agent_use` (nền M2 Agent Contract)
2. **PromptTemplate**: variables extract regex `\{(\w+)\}`; render dùng `str.format`; template chứa `{{` → v1 chấp nhận (không escape — ghi chú); version semver; duplicate register → overwrite + warning
3. **SystemCatalog**: search metadata string values case-insensitive; kind filter; entry upsert (cùng kind+id → replace metadata)
4. **KnowledgeGraph**: add_node trùng kind+id → overwrite properties + warning; add_edge trùng (source, relation, target) → idempotent skip; delete_node cascade edges cả 2 chiều; find theo property match (exact v1); neighbors trả (relation, node_id) hoặc (node_id) — pin: `list[tuple[str, str]]` (relation, node_id)
5. Mọi test offline + tmp_path (nếu cần); coverage ≥ 80%; test_import cập nhật

## Input / Output
- Input: TASK-003 (semver), TASK-006 (metadata), TASK-008 (workflow)
- Output: 4 module + tests + exports + commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: CapabilityRegistry: register/get/list; bind (trùng → idempotent)/unbind; unknown get/tools_for/register_agent_use → CapabilityError; agents_using (trùng → set); duplicate → overwrite; thread-safe (có test)
- [ ] AC2: PromptTemplate: variables tự extract (dedup, thứ tự); **edge case: `{{name}}` → KHÔNG extract; `{score:.2f}` → PromptError lúc construct; `{}` → PromptError**; version semver invalid → ValidationError (có test)
- [ ] AC3: PromptRegistry: register (overwrite chỉ cùng (id,version); version khác → thêm); get (None → mới nhất theo semver; unknown id HOẶC version → PromptError); render (escape literal, thiếu biến → PromptError, thừa biến bỏ qua); **evaluate ×2 → evaluations() trả 2 entry (history append)** (có test)
- [ ] AC4: SystemCatalog: index (upsert)/remove/get/search (**rỗng → toàn bộ; nested scalar match; key không search; kind exact filter; sorted**)/count; unknown get → CatalogError (có test)
- [ ] AC5: KnowledgeGraph: add_node (trùng → overwrite); add_edge (**missing node → GraphError; trùng → skip**); get_node; **neighbors 2 chiều (relation gốc, dedup)**; find (**property tầng 1, value=None → có key, == đúng kiểu**); delete_node cascade; unknown → GraphError (có test)
- [ ] AC6: pytest pass + coverage ≥ 80%; test_import: `from aios_core.capabilities import CapabilityRegistry, Capability` + `from aios_core.prompts import PromptRegistry, PromptTemplate` + `from aios_core.catalog import SystemCatalog` + `from aios_core.knowledge_graph import KnowledgeGraph` pass
- [ ] AC7: Mọi test offline — git sạch
- [ ] AC8: Scenario tích hợp: dùng WorkflowLibrary thật (TASK-008) lấy workflow → index catalog + graph nodes/edges thủ công (**relation cụ thể: `tool -provides-> capability`, `agent -uses-> capability`, `workflow -requires-> capability`**) → 3 query kỳ vọng (search "crud" → workflow; graph: tool nào provides execute_code; agents_using) (có test)
- [ ] AC9: Amend PLAN.md ghi quyết định in-memory v1 + populate thủ công (đã làm trong task) — PLAN + PROGRESS nhất quán

## Phụ thuộc
- TASK-003 (semver), TASK-008 (workflow names)
- Không dep mới

## Rủi ro
- R1: str.format với template chứa JSON braces ({...}) → v1 ghi chú escape `{{ }}`; M4 chuyển jinja2
- R2: In-memory catalog/graph mất khi restart → ghi chú rõ Out (M4 persist)
- R3: 4 module riêng → nhiều errors.py nhỏ — chấp nhận (mỗi module tự chứa)
