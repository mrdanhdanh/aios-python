# TASK-010 — M2/P3a: AIOS Orchestrator v1 — Decision Pipeline 4 tầng (offline-first)

## Mục tiêu
Xây phần lõi của AIOS Orchestrator (Control Plane): **Decision Pipeline 4 tầng offline-first** theo PLAN — Normalizer (không LLM) → Rule Engine (deterministic, 70–90% request dừng ở đây) → Workflow Matcher (tái sử dụng Workflow Library) → Planner LLM (chỉ khi cần). Kèm Agent Selector (chọn agent theo intent) + System Knowledge (trả lời metadata hệ thống qua Catalog/Graph). Đây là "bộ não" mà mọi UI (CLI/dashboard/extension) sẽ đi qua.

## Phạm vi
- **In** (thuộc `backend/src/aios_core/orchestrator/`):
  1. `normalizer.py` — `Normalizer.__init__(alias: dict | None = None, library: WorkflowLibrary | None = None)` (**library optional — None → bỏ qua @ macro, confidence 0.5; Orchestrator truyền CÙNG library instance cho normalizer + matcher**); `normalize(text: str, source: str = "cli")` hoặc dict `{"text", "source", "params"}`; chuẩn hóa tham số (regex `(\w+)=([^\s]+)` — ghi chú giới hạn URL chứa `=`) → alias (dict cấu hình merge) → macro (**`@workflow` anchor `^@` — tra library; `#` đầu câu (`^#`) → intent="chat" — Normalizer ĐƯỢC gán intent cho 2 case đặc biệt `#`/`!skill`, còn lại None; `!skill` → intent="skill", params={"skill": name} — dừng pipeline**); lowercase + strip; `NormalizedRequest`: `intent: str | None = None` (None trừ #/!skill), `params`, `raw`, `source`, `confidence: float = 0.5` (1.0 nếu alias/macro khớp); KHÔNG dùng LLM
  2. `rule_engine.py` — `RuleEngine`: **deterministic, word-boundary match `re.search(rf"\b{re.escape(pattern)}\b", text.lower())`**; `add_rule(patterns, intent, agent=None, priority=0)`; **tổng thứ tự: priority desc → longest pattern (độ dài pattern string) → insertion asc**; `match(text) -> RuleMatch | None`; `RuleMatch(intent, agent, matched_pattern, priority)`; **bảng `default_rules()` đầy đủ** (xem mục "Rules mặc định")

### Rules mặc định (default_rules — bảng đầy đủ)
| patterns | intent | agent | priority |
|---|---|---|---|
| generate api, create api | coding | coder | 10 |
| medical, doctor, khám bệnh, triệu chứng | medical | doctor | 10 |
| system status, system health | system | system_doctor | 8 |
| install skill | skill | None | 8 |
| upgrade, update system | upgrade | None | 8 |
| diagnose, phân tích lỗi | diagnose | None | 8 |
| chat, hello, hi, xin chào | chat | None | 5 |
| crud, api generator | workflow | None | 4 |
  3. `workflow_matcher.py` — `WorkflowMatcher(library)`: `match(text) -> WorkflowMatch | None` (**library từ constructor — không qua tham số**): ưu tiên (1) template macro (**nơi DUY NHẤT validate macro → workflow_name — `library.get` WorkflowError → bỏ qua**) → confidence 0.9; (2) search cả câu; (3) **token search (filter: bỏ token < 3 ký tự + stopwords; gọi library.search từng token theo thứ tự — dừng ở token ĐẦU có match)**; **sau candidate → `library.get(name)` re-check: `token in name` → 0.8, chỉ description → 0.6**; `WorkflowMatch(workflow_name, matched_by, confidence)`; first match (insertion order)
  4. `planner.py` — `Planner` (LLM fallback): `plan(request, model: ModelContract, library: WorkflowLibrary) -> PlanResult` — prompt hệ thống liệt kê workflow names từ library; **catch `ModelError` (gồm ModelTimeoutError) + check `is_available()` trước** → PlanResult intent="chat" + error=True; **`PlanResult(intent, workflow_names, reasoning, confidence, llm_used: bool, error: bool = False)`**; **Planner giữ `self._calls` (tăng quanh mỗi model.chat kể cả raise) + `reset_calls()`; Orchestrator.stats() đọc planner.calls; PlannerStub calls==0**; **parse fail (không có "intent:") → intent="chat" + error=True**; `PlannerStub` (intent_map **exact text match**; llm_used=False) — test offline
  5. `orchestrator.py` — `Orchestrator` (public API): `handle(request: str | dict | NormalizedRequest) -> OrchestratorResponse` — pipeline: Normalizer → RuleEngine → WorkflowMatcher → Planner; **`if req.intent` (từ normalizer #/!skill) → dừng pipeline, resolved_by="normalizer"`**; **rule có agent → VẪN chạy matcher (không gọi planner); rule không agent → chạy matcher; matcher khớp → gắn workflow_name; hết → planner**; **rule+matcher cùng khớp → resolved_by="rule" (nguồn chính) + workflow_name phụ (UI hiển thị cả 2)**; `agent = rule.agent or selector.select(intent)`; `OrchestratorResponse(intent, agent: str | None, workflow_name: str | None, source, resolved_by: Literal["normalizer","rule","workflow","planner","fallback"], raw, plan, request_stats: dict)`; **`Orchestrator.stats()` cumulative: `total_requests`, `llm_calls` (đọc planner.calls — số lần model.chat thực), trả bản copy, `reset()`; lock chỉ bao counter KHÔNG bao LLM call**; `Orchestrator.__init__(rule_engine, workflow_matcher, planner, normalizer, agent_selector)` — DI-friendly
  6. `agent_selector.py` — `AgentSelector`: map intent → agent (`{"coding": "coder", "medical": "doctor", "system": "system_doctor", "chat": "general"}`); `select(intent) -> str | None`; unknown → None; **nối luồng: `agent = rule.agent or selector.select(intent)`** (skill/upgrade/diagnose → None → fallback general)
  7. `system_knowledge.py` — `SystemKnowledge(catalog: SystemCatalog, graph: KnowledgeGraph, library: WorkflowLibrary)`: `answer(question: str) -> str` (rule-based keywords v1 — KHÔNG LLM; test tiếng Anh); queries: "how many (skills|workflows|agents|tools)" — **mapping plural→singular (workflows→workflow, skills→skill, agents→agent, tools→tool) + `catalog.search("", kind=X)` đếm**; "who uses <capability>" (qua `graph.neighbors(kind="capability", id=...)` — **catch GraphError → None**); "workflow <keyword>" — **nguồn = library.search(keyword)** trả "Workflows: <names>"; **catch CatalogError/GraphError/WorkflowError → None**; unknown → None
  8. `errors.py` — `OrchestratorError`
  9. `__init__.py` exports + re-export `orchestrator` ở `aios_core/__init__.py`
  10. Tests: test_normalizer, test_rule_engine, test_workflow_matcher, test_planner, test_orchestrator, test_system_knowledge (6 file)
- **Out (không làm)**: Goal Manager + Task Queue → TASK-011; Permission Broker → TASK-011; Failure Recovery (retry/fallback agent) → TASK-011; Capability Router đầy đủ → TASK-011 (Orchestrator v1 chỉ chọn agent + workflow); Skill Manager Proxy → M2 sau; Improvement Advisor → M4; CLI/API wrapper → TASK-011 (dùng trực tiếp Orchestrator.handle qua test); LLM agent thật (General/Coder/Doctor) → TASK-012+ (P3b)

## Yêu cầu chi tiết
1. **Normalizer**: alias dict injectable (defaults + custom merge); macro: text bắt đầu `@` → tra WorkflowLibrary; `#` prefix → chat direct; lowercase + strip; params: extract `key=value` pairs (v1 đơn giản)
2. **RuleEngine**: `match` trả rule khớp nhất (priority desc, insertion asc); rules mặc định (8 intents) khai báo trong `default_rules()`; case-insensitive; pattern là keyword substring (không regex v1 — ghi chú)
3. **WorkflowMatcher**: `match` ưu tiên (1) template macro (2) library.search; confidence: template=0.9, search name=0.8, description=0.6
4. **Planner**: `PlanResult` có `llm_used: bool`; PlannerStub cấu hình `intent_map: dict[str, str]` (text → intent) — test deterministic; Planner thật gọi `model.chat` (tối đa 1 lần/request)
5. **Orchestrator** (xem Phạm vi #5 — Yêu cầu này): **rule có agent → VẪN chạy matcher (chỉ bỏ qua planner); rule+matcher cùng khớp → resolved_by="rule" + workflow_name phụ**; rule không agent → chạy matcher → planner nếu không khớp; `if req.intent` từ normalizer → dừng, resolved_by="normalizer"; `agent = rule.agent or selector.select(intent)`; stats: `total_requests`, `llm_calls` (đọc planner.calls), **reset(): gọi planner.reset_calls() + zero counters**
6. **AgentSelector**: mapping default; `select` unknown → None
7. **SystemKnowledge**: queries mẫu: "bao nhiêu (skills|workflows|agents|tools)", "ai dùng (capability)", "workflow nào (keyword)"; trả string tiếng Anh (code) — trả lời user qua UI sẽ dịch (M3)
8. Mọi test offline (PlannerStub — không gọi model thật); coverage ≥ 80%; test_import cập nhật
9. Stats cho verification M2: `Orchestrator.stats()` tích lũy (tổng requests, llm_calls) — test "100 requests mẫu → llm_calls ≤ 30%" (offline-first verification)

## Input / Output
- Input: TASK-008 (WorkflowLibrary, WorkflowDefinition), TASK-009 (SystemCatalog, KnowledgeGraph, CapabilityRegistry), TASK-006 (ModelContract, MockModel)
- Output: orchestrator/ package (8 module) + tests + exports + commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: Normalizer 6 case cụ thể: (1) CLI text + params `lang=python` → params đúng; (2) alias merge custom; (3) `@workflow` macro; (4) `#` đầu câu → chat; (5) lowercase/strip; (6) dict input `{"text", "source"}` (có test)
- [ ] AC2: RuleEngine: match đúng intent 7 mẫu (coding/medical/system/skill/upgrade/diagnose/chat); **word-boundary chống false positive ("file system" → KHÔNG system)**; **"generate api generator" → coding (priority 10 thắng longest 13)**; priority thắng; cùng priority → insertion (**tie "update system status" — system status đăng ký trước**); không khớp → None (có test)
- [ ] AC3: WorkflowMatcher: template macro khớp; search theo token (tách keyword trước search); không khớp → None; confidence đúng (có test)
- [ ] AC4: PlannerStub deterministic (intent_map, llm_used=False); Planner thật: gọi model 1 lần, parse, **ModelError/Timeout → fallback intent="chat" + error flag** (có test — fake model)
- [ ] AC5: Orchestrator pipeline: "generate api" → coding/coder resolved_by="rule" + **matcher token search "api" tìm workflow `crud_generator` (fixture description chứa "api") → response có cả agent='coder' lẫn workflow_name='crud_generator'**; "medical question" → medical/doctor (rule); "tạo crud api" → workflow (matcher); "#hello" → chat resolved_by="normalizer"; intent lạ → planner; fallback chat (có test 6 case)
- [ ] AC6: Offline-first: 100 requests mẫu (70 rule + 20 workflow + 10 lạ) với **Planner thật + MockModel đếm calls** → `llm_calls == 10` (≤ 30%); stats.total_requests == 100; reset() → 0 (có test)
- [ ] AC7: AgentSelector mapping + unknown → None; `agent = rule.agent or selector.select(intent)` (có test)
- [ ] AC8: SystemKnowledge: "how many workflows", "who uses execute_code" (graph.neighbors), "workflow crud" → câu đúng; unknown → None (có test)
- [ ] AC9: pytest pass + coverage ≥ 80% (addopts sẵn có); test_import: `from aios_core.orchestrator import Orchestrator, Normalizer, RuleEngine, WorkflowMatcher, Planner, AgentSelector, SystemKnowledge` pass
- [ ] AC10: Mọi test offline — git sạch (yêu cầu quy trình)

## Phụ thuộc
- TASK-006 (ModelContract, MockModel), TASK-008 (WorkflowLibrary), TASK-009 (SystemCatalog, KnowledgeGraph)
- Không dep mới

## Rủi ro
- R1: Planner parse model output không JSON → regex/fallback v1 (pattern "intent: X" + "workflow: Y"); ghi chú M2 nâng cấp structured output
- R2: Rule keywords trùng nhau (VD "api" trong coding + workflow) → priority + thứ tự đăng ký quyết định; test pin thứ tự
- R3: SystemKnowledge phạm vi hẹp (rule-based) — đủ v1, LLM → M4 Improvement Advisor
- R4: Orchestrator giữ state (stats) → thread-safe lock; reset() cho test
