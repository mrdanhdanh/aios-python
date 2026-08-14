# TASK-023 — Memory Coordinator (M5-P9, Phase 1)

**Metadata**: TASK-023 | M5/P9 | 2026-08-14 | v4 (critique ×2 + review approved có điều kiện) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/memory/` (coordinator + contracts + sources) + `config.py` (MemorySettings.budget) + `kernel/runtime_kernel.py` (wiring) + `tests/`

## 1. Mục tiêu

Xây **Memory Coordinator** — tầng quyết định giữa 4 loại Memory (Conversation/Session/Knowledge/Artifact) và ContextService, trả lời câu hỏi của PLAN.md §M5-3: *"Trong tất cả những gì AIOS biết, cái gì thực sự cần đưa vào execution hiện tại?"*

Pipeline: `Memory Stores → Memory Coordinator (Retrieve → Filter → Rank → Compress → Deduplicate → Prioritize) → Memory Context → ContextService`. Agent KHÔNG truy cập Memory trực tiếp (INV-011: `Memory → Coordinator → Context → Agent`). Toàn bộ pipeline **deterministic, không bắt buộc LLM** — mọi bước đều test được bằng unit test; đây là nền tảng cho TASK-024 Context Optimizer.

> **Thứ tự pipeline (C2-03)**: Compress trước Deduplicate — dedup phải đánh giá trên content sau truncate (2 content dài cùng prefix sau compress thành y hệt → dedup 1 bản). Rank trước Compress (score dùng content đầy đủ).

## 2. Phạm vi

**In**:
- `memory/contracts.py` — 5 pydantic models: `MemoryQuery · MemoryCandidate · MemoryScore · MemorySelection · MemoryContext` (`extra="forbid"`)
- `memory/coordinator.py` — `MemoryCoordinator` (điều phối pipeline) + `MemorySource` Protocol + `MemoryCoordinatorConfig`
- `memory/sources.py` — 4 adapter store: `ConversationSource · SessionSource · KnowledgeSource · ArtifactSource` (duck-typed qua Protocol, **không import runtime store implementation của knowledge**)
- `config.py` — mở rộng `MemorySettings` (+ `budget`) — additive only
- `kernel/runtime_kernel.py` — wiring `MemoryCoordinator` qua `container.register_instance` (additive)
- `tests/test_memory_coordinator.py` + `tests/test_architecture.py` (allow-list `memory/` + INV-011)
- `memory/__init__.py` — re-export public API (additive)
- `knowledge/knowledge.py` — thêm **1 method additive read-only** `list_chunks(source_id=None) -> list[ChunkRecord]` (resolution C1-01)

**Out (không làm — tránh scope creep)**:
- **KHÔNG đổi hành vi** API có sẵn của `ConversationMemory` / `SessionMemory` / `VectorStore` / `SQLiteVectorStore` / `KnowledgeMemory` / `ContextService` / `ArtifactService` (git diff verify — additive only; **ngoại lệ duy nhất**: method mới `KnowledgeMemory.list_chunks`, read-only, không đổi hành vi method cũ — C1-01)
- **KHÔNG làm Context Optimizer** (TASK-024): priority P0..P6, 3-level compression (Extractive/LLM), final context cho model. Ranh giới: TASK-023 compress = **deterministic truncate** + budget theo category; TASK-024 = "đưa bao nhiêu và dưới dạng nào vào model"
- **KHÔNG dùng LLM** ở bất kỳ bước nào (rank/compress/dedup đều deterministic)
- **KHÔNG sửa Agent / Orchestrator / Capability** để dùng coordinator (việc của task sau / harness M6) — task này chỉ xây coordinator + inject vào ContextService
- **KHÔNG emit event mới** (EventType giữ nguyên; observability "memory retrieval latency" của M5 DoD gắn ở task sau)
- **KHÔNG làm embedding production** (Ollama/OpenAI embedder cho semantic) — embedder injectable, default `None`
- **KHÔNG sửa `contracts/`** (INV-006 purity — contracts của coordinator đặt trong `memory/`, domain-local, theo pattern TASK-022 dataclass local)

## 3. Input / Output

- **Input**: `MemoryQuery` (text, session_id, strategies, sources, top_k, since, min_importance, max_chars) + dữ liệu từ 4 store + `MemorySettings.budget`
- **Output**:
  - `MemorySelection` — candidates đã rank + tokens theo category + trạng thái budget
  - `MemoryContext` — sections theo category đã cắt theo budget, **được inject vào `ContextService`** scope `EXECUTION`, key `memory.context` (đọc lại được bằng `get(EXECUTION, "memory.context")`)
  - Không trả về trực tiếp cho Agent — Agent đọc qua ContextService (INV-011)

## 4. Yêu cầu chức năng

### YC-1 — Contract models (pydantic, `extra="forbid"`)
5 models trong `memory/contracts.py`:
```python
class MemoryKind(str, Enum):          # conversation | session | knowledge | artifact
class MemoryStrategy(str, Enum):      # exact | keyword | semantic | metadata | recency | importance | hybrid

class MemoryQuery(BaseModel):         # extra="forbid"
    text: str
    session_id: str
    strategies: list[MemoryStrategy] = [HYBRID]      # default hybrid
    sources: list[MemoryKind] | None = None          # None = tất cả 4 loại
    top_k_per_source: int = Field(gt=0, default=20)   # C2-11
    since: datetime | None = None
    min_importance: float = Field(ge=0, le=1, default=0.0)  # C2-11
    max_chars: int = Field(gt=0, default=2000)        # C2-11: per-candidate compress cap

class MemoryCandidate(BaseModel):     # extra="forbid"
    id: str                           # dedup key: "{kind}:{source_id}:{item_id}"
    kind: MemoryKind
    source_id: str
    content: str
    created_at: datetime
    importance: float = 0.5
    metadata: dict[str, Any] = {}
    strategy_hits: list[MemoryStrategy] = []

class MemoryScore(BaseModel):         # extra="forbid"
    semantic: float = 0.0             # 0..1
    relevance: float = 0.0            # 0..1
    recency: float = 0.0              # 0..1
    importance: float = 0.0           # 0..1
    source_priority: float = 0.0      # 0..1
    total: float = 0.0                # weighted sum

class MemorySelection(BaseModel):     # extra="forbid"
    query: MemoryQuery
    items: list[tuple[MemoryCandidate, MemoryScore]]   # đã sort, giữ thứ tự
    tokens_by_kind: dict[MemoryKind, int]    # C2-01: 4 kind khớp 4 category dùng (task/knowledge/history/artifacts)
    total_tokens: int
    budget: dict[MemoryKind, int]            # C2-01: chỉ 4 kind; system/reserve chỉ ở MemoryBudgetSettings
    truncated: bool

class MemoryContext(BaseModel):       # extra="forbid"
    session_id: str
    sections: dict[MemoryKind, list[str]]   # content đã render per category
    tokens_by_kind: dict[MemoryKind, int]    # C2-01
    total_tokens: int
    selection: MemorySelection
    created_at: datetime
```
- **Test**: `extra="forbid"` — field thừa → `ValidationError`; `top_k_per_source <= 0` → `ValidationError`; `min_importance` ngoài [0,1] → `ValidationError`; default đúng (strategies=[hybrid], top_k=20, max_chars=2000).

### YC-2 — Retrieval: 7 chiến lược (PLAN §3.1)

**Ma trận source × strategy (C2-05 — chỉ liệt kê chiến lược có dữ liệu thật cho source đó)**:

| Strategy | conversation | session | knowledge | artifact |
|----------|--------------|---------|-----------|----------|
| exact | ✓ (content) | ✓ (content) | ✗ (chunk text không match substring — chỉ keyword) | ✓ (name/metadata) |
| keyword | ✓ | ✗ | ✓ (chunk text qua `list_chunks`) | ✓ (name) |
| semantic | ✗ | ✗ | ✓ (nếu embedder ≠ None; None → rỗng) | ✗ |
| metadata | ✗ | ✗ | ✗ (chunks không có metadata) | ✓ (`type`, `metadata` dict) |
| recency | ✓ | ✓ | ✗ (chunks không có created_at) | ✓ (`created_at`) |
| importance | ✗ (fallback 0.5 — no-op) | ✗ (fallback 0.5 — no-op) | ✗ (fallback 0.5 — no-op) | ✓ (nếu `metadata` có `importance`) |

- **exact**: substring match (case-insensitive) trên `content` — conversation, session, artifact (name)
- **keyword**: term overlap — tokenize text → tỉ lệ term trùng trong content — conversation, knowledge chunk (qua `list_chunks`), artifact (name)
- **semantic**: embed query → `VectorStore.search` — knowledge (có vector); **nếu embedder = None → chiến lược trả rỗng (deterministic, score 0), không crash**
- **metadata**: filter theo field metadata (vd `type`, `tags`) — **chỉ artifact** (có metadata thật)
- **recency**: lấy N mới nhất theo `created_at` — conversation, session, artifact
- **importance**: lấy top theo `metadata["importance"]` — chỉ artifact (nếu có); các source khác importance fallback 0.5 → no-op (thiết kế — ghi Giả định)
- **hybrid** (default): kết hợp ≥2 chiến lược (mặc định `semantic + keyword + recency`) → gộp candidate, dedup sau
- Strategy không được source hỗ trợ → source đó bỏ qua chiến lược đó (không crash)
- **Test**: 7 test riêng, mỗi test seed store + query → assert đúng loại/đúng candidate; hybrid gộp ≥2 nguồn; embedder None → semantic rỗng; strategy không hợp lệ → **`ValidationError` (pydantic, C3-01)**.

### YC-3 — Filter
Loại candidate: (a) không đúng `sources` whitelist; (b) `created_at < since` — **ngoại lệ: knowledge bỏ qua `since`** (created_at = epoch cố định — C2-12); (c) `importance < min_importance`; (d) content rỗng/whitespace.
Sau filter, nếu số candidate > `top_k_per_source` → **giữ N mới nhất theo `created_at desc → id asc` (deterministic — C2-03/C2-07)**.
- **Test**: seed candidate vi phạm từng điều kiện → bị loại; không điều kiện vi phạm → giữ nguyên; > top_k → chỉ giữ N mới nhất; tie created_at → id asc.

### YC-4 — Ranking (PLAN §3.2, deterministic)
`MemoryScore.total = w_sem·semantic + w_rel·relevance + w_rec·recency + w_imp·importance + w_sp·source_priority` — **weights mặc định `{semantic: 0.35, relevance: 0.25, recency: 0.15, importance: 0.10, source_priority: 0.15}` (sum = 1.0, validate khi khởi tạo config)**.
- `semantic`: từ vector score (cosine, chuẩn hoá `(cos + 1) / 2` về [0,1] — C2-09) khi strategy semantic; ngược lại 0.0
- `relevance`: tỉ lệ term trùng (keyword) hoặc 1.0 khi exact hit; ngược lại 0.0
- `recency`: time decay `clamp(0.0, 1 - age_days / half_life_days, 1.0)` — `age = clock() - created_at`, `half_life_days` mặc định 7.0; **clock injectable** (mặc định `time.time`); clamp chặn created_at tương lai → recency > 1 (C2-10)
- `importance`: `metadata["importance"]` nếu có (clamp 0..1), ngược lại 0.5
- `source_priority`: hằng số theo kind — mặc định `{conversation: 1.0, session: 0.9, knowledge: 0.8, artifact: 0.7}` (trong `MemoryCoordinatorConfig`)
- **`MemoryCoordinatorConfig.budget: MemoryBudgetSettings`** (R2-2) — coordinator tự ánh xạ kind→category (conversation→history, session→task, knowledge→knowledge, artifact→artifacts), ignore system/reserve
- **Sort**: `total desc → source_priority desc → created_at desc → id asc` (tie-break hoàn toàn deterministic)
- **tz-aware (C2-06)**: `created_at` từ store được normalize về tz-aware UTC; input naive → `.replace(tzinfo=timezone.utc)` (không raise, không phụ thuộc timezone máy)
- **Test**: (a) 2 candidate cùng weights → thứ tự đúng theo công thức; (b) đổi weights trong config → thứ tự đổi đúng; (c) cùng total → tie-break đúng thứ tự; (d) fake clock → recency thay đổi theo thời gian; (e) cùng input chạy 2 lần → kết quả y hệt; (f) naive datetime → normalize về UTC, recency tính đúng.

### YC-5 — Deduplicate
Key = `_normalize(content)` (strip + lowercase + collapse whitespace) — SHA-256 của chuỗi chuẩn hoá; candidate trùng key → giữ bản **total cao nhất** (hoà → giữ bản đọc trước — thứ tự sources ổn định). **Chạy SAU Compress** (C2-03) — dedup trên content đã truncate.
- **Test**: cùng nội dung từ conversation + knowledge → 1 candidate, score cao nhất được giữ; 2 candidate khác nội dung → giữ cả 2; **regression**: 2 content dài 5000 ký tự cùng 2000 ký tự đầu → sau pipeline chỉ 1 section trong MemoryContext (C2-03).

### YC-6 — Compress (deterministic, cấp 1 — KHÔNG LLM)
Mỗi candidate cắt về `query.max_chars` ký tự: `content[:max_chars-1] + "…"` khi bị cắt (tổng = max_chars — C2-08); content ≤ max_chars giữ nguyên. Không merge, không extractive — đó là TASK-024.
- **Test**: content 5000 ký tự + max_chars 2000 → content đầu ra = 2000 ký tự (1999 + "…"); content ngắn → giữ nguyên.

### YC-7 — Budget (PLAN §3.3, INV-012 phần coordinator)
- `MemorySettings.budget` (mới, additive): `system: 3000, task: 2000, knowledge: 6000, history: 5000, artifacts: 3000, reserve: 1000` (tổng 20K)
- Ánh xạ kind → category: `conversation→history, session→task, knowledge→knowledge, artifact→artifacts` (**system/reserve dành cho TASK-024** — coordinator chỉ dùng 4 category)
- Token estimate deterministic: `estimate_tokens(text) = max(1, ceil(len(text)/4))` — **tính trên content SAU compress** (R3-2)
- **Prioritize**: xếp candidate theo total desc, đưa vào từng category cho tới khi vượt cap → candidate vượt cap bị loại (không truncate ngẫu nhiên); `truncated = True` nếu có loại; `total_tokens = sum(tokens_by_kind)` ≤ tổng cap
- **Query rỗng → short-circuit (C2-02)**: `text.strip() == ""` → trả `MemorySelection` rỗng ngay đầu pipeline (không chạy retrieval, không crash)
- **Test**: seed đủ vượt cap → assert `tokens_by_kind[kind] ≤ budget[kind]` cho cả 4 kind; candidate bị loại đúng là candidate có **total thấp nhất trong category tương ứng** (C1-02); overflow 1 category riêng; truncated flag đúng; query rỗng → selection rỗng.

### YC-8 — Inject vào ContextService (INV-011)
- `MemoryCoordinator.inject(query) -> MemoryContext`: chạy pipeline → `context.set(ContextScope.EXECUTION, "memory.context", memory_context)` (TTL None mặc định; giá trị là instance MemoryContext)
- Inject lần 2 → ghi đè (đúng semantics `ContextService.set`)
- Coordinator **không trả memory trực tiếp cho Agent** — chỉ qua ContextService
- **Test (C3-05)**: sau inject, `context.get(EXECUTION, "memory.context", inherit=False)` trả `MemoryContext` đúng session_id/tokens; inject lại → value mới; `context.get(AGENT, "memory.context", inherit=True) is None` (inheritance đi hướng xuống SYSTEM←…←AGENT←EXECUTION → key ở EXECUTION không thấy ở AGENT).

### YC-9 — Deterministic tổng thể
Cùng input (store + query + weights) → `MemorySelection` y hệt (giá trị lẫn thứ tự items). Không dùng LLM, không dùng random, không dùng thời gian thực ngoài clock injectable.
- **Test (C2-06)**: chạy pipeline 2 lần trên cùng fixture với **fixed fake clock (hằng số epoch)** + fixture `created_at` cố định → `model_dump()` bằng nhau. Điều kiện đủ "cùng input" = store + query + clock + weights đều cố định.

### YC-10 — Settings (additive)
`MemorySettings` thêm field:
```python
class MemoryBudgetSettings(BaseModel):
    system: int = 3000
    task: int = 2000
    knowledge: int = 6000
    history: int = 5000
    artifacts: int = 3000
    reserve: int = 1000

class MemorySettings(BaseModel):
    conversation_db_path: str = "aios/data/conversations.db"
    knowledge_db_path: str = "aios/data/knowledge.db"
    budget: MemoryBudgetSettings = MemoryBudgetSettings()
```
- `config.yaml` **không cần sửa** (default khớp); override env: `AIOS_MEMORY__BUDGET__KNOWLEDGE=8000`
- **Test** (`test_config.py`): default 6 field; env override; `_yaml_extra_keys_guard` vẫn pass với config.yaml hiện có (không sửa file).

### YC-11 — Wiring (RuntimeKernel.create, additive)
- Trong `RuntimeKernel.create` (sau khi có `context_service` + `artifact_service`):
  - `conversation = ConversationMemory(settings.memory.conversation_db_path)` (lazy — import bên trong create, theo pattern sẵn có)
  - `knowledge = KnowledgeMemory(settings.memory.knowledge_db_path)` + embedder = None (mặc định)
  - `coordinator = MemoryCoordinator(sources=[ConversationSource(conversation), SessionSource(context_service), KnowledgeSource(knowledge, embedder=None), ArtifactSource(artifact_service)], context=context_service, config=MemoryCoordinatorConfig(budget=settings.memory.budget))`
  - `container.register_instance(MemoryCoordinator, coordinator)` (instance dựng tay — theo pattern `EventService`/`ContextService`)
- `RuntimeKernel.create()` chạy được với Settings default; KHÔNG sửa service đã đăng ký
- **Test** (integration): `RuntimeKernel.create().container.resolve(MemoryCoordinator)` trả instance; inject chạy end-to-end với store thật (tmp db qua Settings).

## 5. Yêu cầu kiến trúc

### 5.1 INV-011 — Memory Isolation
- `MemoryCoordinator` là **cổng duy nhất** truy xuất 4 store cho execution; Agent không import `aios_core.memory.*` / `aios_core.knowledge.*` trực tiếp
- Arch test mới trong `test_architecture.py`: `dir_imports(AGENTS_DIR, ["aios_core.memory", "aios_core.knowledge"])` → `[]` (bổ sung vào allow-list agents hiện có — agents/ đã bị cấm import những thứ khác, chỉ cần thêm 2 pattern vào forbidden set của INV-001/002)
- **Ghi chú (C3-02)**: allow-list agents hiện có (`_AGENTS_ALLOWED_AIOS` = {models.base, models.errors}) ĐÃ chặn mọi import memory/knowledge từ agents/ — test INV-011 mới chỉ là **tường minh hóa** invariant đã được bao phủ, không phải rào chắn mới.

### 5.2 Allow-list import `memory/` (test mới `test_inv_memory_import_allowlist`)
- **aios_core allowed**: chỉ `aios_core.kernel.services` (session.py đã import sẵn — giữ nguyên; coordinator cần `ContextService`/`ContextScope`; ArtifactSource nhận `ArtifactService`)
- **CẤM import `aios_core.knowledge` TUYỆT ĐỐI trong `memory/*.py` — kể cả dưới `TYPE_CHECKING`** (C2-01): `collect_imports`/AST scan đếm MỌI Import node (top-level, trong hàm, try/except, TYPE_CHECKING). `KnowledgeSource` dùng **local structural Protocol** khai báo ngay trong `memory/sources.py` (duck-typed; store + embedder nhận kiểu `Any`); `KnowledgeMemory` thỏa structural typing mà không cần import. `runtime_kernel.py` (ngoài `memory/`) là nơi DUY NHẤT import `KnowledgeMemory` để dựng instance.
- **external allowed**: `pydantic`, `typing`, `datetime`, `time`, `enum`, `collections`, `math`, `hashlib`, `logging`, `dataclasses`, `functools`, `re`, `pathlib`, `abc`, `contextlib`, `sqlite3`, `json`, `uuid`, `itertools`
- Test scan toàn dir `memory/*.py` qua `collect_imports` (pattern y hệt `test_inv_skills_import_allowlist`), loại trừ intra-package

### 5.3 Deterministic first
- Mọi stage thuần hàm: không LLM, không random, clock injectable; ranking = công thức cố định; tie-break đầy đủ; test `model_dump()` bằng nhau qua 2 lần chạy (YC-9)

### 5.4 No God Object
- `MemoryCoordinator` **chỉ điều phối** (gọi pipeline stages), **không ôm logic store**: logic truy xuất từng store nằm trong 4 adapter `memory/sources.py`; logic rank/budget trong coordinator tách stage (retrieve/filter/rank/dedup/compress/prioritize — có thể là private methods hoặc functions module-level; coordinator giữ thứ tự pipeline)
- Coordinator chỉ phụ thuộc `MemorySource` Protocol + contracts — không biết `ConversationMemory`/`KnowledgeMemory` cụ thể

### 5.5 Additive only
- `git diff` sau implement: `conversation.py / session.py / vector.py / context.py / artifacts.py / events.py` **không đổi**; `knowledge/knowledge.py` chỉ **thêm** method `list_chunks` (read-only, C1-01); còn lại chỉ thêm file mới + `config.py`/`runtime_kernel.py`/`__init__.py`/tests (mở rộng)
- **Hành vi mới chủ ý (C2-05)**: `RuntimeKernel.create()` sau wiring sẽ eager tạo `conversations.db` + `knowledge.db` (pattern đã có: EventService tạo `audit.db` eager) — persistence là mục đích; test dùng tmp settings.

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — 5 models pydantic `extra="forbid"`; thừa field / `top_k<=0` / `min_importance` ngoài [0,1] → `ValidationError`; defaults đúng (test_memory_coordinator.py — YC-1)
- [ ] **AC2**: 7 retrieval strategies — mỗi strategy có test riêng trên store seeded → trả đúng candidate; hybrid gộp ≥2 chiến lược; embedder None → semantic rỗng không crash; strategy không hợp lệ → **`ValidationError` (pydantic tại boundary `MemoryQuery`)** (YC-2, C2-04)
- [ ] **AC3**: Ranking deterministic — công thức weights; đổi weights → thứ tự đổi đúng; tie-break `total→source_priority→created_at→id`; fake clock; 2 lần chạy y hệt (YC-4, YC-9)
- [ ] **AC4**: Dedup — cùng nội dung 2 source → 1 candidate giữ total cao nhất; khác nội dung → giữ cả 2 (YC-5)
- [ ] **AC5**: Budget — test dùng `MemoryBudgetSettings` tùy chỉnh tổng **4K** (history 1500, task 1000, knowledge 1000, artifacts 500); seed cụ thể (C2-13): conversation 40 messages (mỗi ~200 ký tự → 50 tokens → 40×50 = 2000 > 1500 cap), knowledge 30 chunks (mỗi ~500 ký tự → 125 tokens → 3750 > 1000), session 20 values (mỗi ~200 ký tự → 50 tokens → 1000 = cap), artifact 10 items (name > 200 ký tự → 51 tokens → 510 > 500); total các candidate cách biệt rõ (tránh trôi recency — C2-06 dùng fake clock); assert `total_tokens ≤ 4000`, `tokens_by_kind[kind] ≤ budget[kind]` cả 4 kind, **candidate bị loại = candidate có total thấp nhất trong category tương ứng** (C1-02), `truncated` đúng; + test overflow 1 category riêng (PLAN §23 test strategy; YC-7)
- [ ] **AC6**: Compress — content dài bị cắt về đúng `max_chars` (1999 + "…"), content ngắn giữ nguyên, deterministic (YC-6)
- [ ] **AC7**: Inject — `context.get(EXECUTION, "memory.context", inherit=False)` trả `MemoryContext` đúng; inject lại ghi đè; `get(AGENT, key, inherit=True) is None`; Agent (agents/) không thể import memory trực tiếp (INV-011 arch test pass) (YC-8, §5.1)
- [ ] **AC8**: Settings — `memory.budget` 6 field default đúng; env override `AIOS_MEMORY__BUDGET__KNOWLEDGE` hoạt động; config.yaml hiện có load không lỗi (YC-10)
- [ ] **AC9**: Wiring — `RuntimeKernel.create()` trả instance dùng được; test **bắt buộc dùng tmp settings** (pattern `make_settings(tmp_path)` — C3-03); full suite pytest pass; coverage toàn suite ≥ 80% cứng (95% mục tiêu) (YC-11)
- [ ] **AC10**: Architecture — `test_inv_memory_import_allowlist` pass (memory/ chỉ import allow-list; **không import aios_core.knowledge kể cả TYPE_CHECKING**); git diff verify additive only (§5.2, §5.5)

## 7. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Cycle package `memory` ↔ `knowledge` (knowledge đã import `memory.vector`) | `KnowledgeSource` dùng **local structural Protocol + Any — không import runtime `aios_core.knowledge` kể cả TYPE_CHECKING** (C2-01); arch test chặn (AC10) |
| Semantic retrieval vô dụng khi embedder None (production chưa có embedder) | Giả định rõ: semantic = 0 khi không có embedder, deterministic; keyword/exact/recency vẫn hoạt động; embedder injectable để gắn sau (M5 sau / harness) |
| Chồng lấn TASK-024 (compress/prioritize đều nằm trong cả 2) | Ranh giới cứng ghi trong Phạm vi Out: TASK-023 = chọn memory + deterministic truncate + budget theo category; TASK-024 = priority P0..P6 + 3-level compression + final context cho model |
| Budget tổng (20K) vượt context window model thật | Budget là cấu hình (Settings), coordinator chỉ enforce theo config; Context Optimizer (TASK-024) xử lý tổng thể — ghi nhận là giả định |
| Performance khi store lớn (retrieve toàn bộ rồi rank) | `top_k_per_source` default 20 — **giới hạn sau filter** (giữ N mới nhất theo created_at desc, C2-03); SQLite index có sẵn (messages theo conversation_id+created_at); 100 memories trong test < vài trăm ms |
| `RuntimeKernel.create()` eager tạo memory db — đổi hành vi CLI/API (C2-05) | Chốt eager creation là hành vi mới chủ ý (persistence; pattern EventService/audit.db); test dùng tmp settings; ghi nhận trong Phạm vi §5.5 |
| Critic phản biện vị trí `memory/coordinator.py` (có thể đề xuất package riêng) | Lý do giữ `memory/`: coordinator là nội bộ domain memory, gần stores; tránh package mới `intelligence/` khi chỉ có 1 module; nếu critique yêu cầu, tách `aios_core/intelligence/` là quyết định mở — ghi vào critique resolution |

**Giả định**:
- Token estimate dùng heuristic `ceil(len/4)` — không phải tokenizer chính xác (đủ cho budget + test deterministic; chính xác hoá ở TASK-024)
- `SessionMemory` được tạo per `session_id` qua `SessionSource` (wrapper mỏng, rẻ); SessionSource enumerate qua `get_all(SHARED)` + prefix, `content = str(value)`, `created_at` từ `Context.created` (qua `get_context`), `metadata = {}`, `importance = 0.5` (C2-04)
- **Importance fallback 0.5 cho mọi source không có metadata là thiết kế** (C2-05) — importance strategy chỉ có hiệu lực thật trên artifact có `metadata["importance"]`
- Artifact `content = artifact.name` (không đọc bytes file ở retrieval — C3-04); metadata strategy dùng `artifact.type` + `artifact.metadata` dict thật; timestamp field là **`created`** (kế thừa `AiOSMetadata`) → map `contract.created → created_at` (C2-15)
- **Knowledge chunks không có timestamp thật → `created_at = datetime(1970,1,1, tzinfo=utc)` cố định** (C2-02) → recency = 0 deterministic, đúng matrix "recency ✗"; knowledge bỏ qua filter `since` (C2-12)
- Clock mặc định `time.time()` (epoch, cho recency) — không dùng monotonic vì cần so sánh với `created_at` ISO lưu store
- `created_at` normalize về tz-aware UTC trước khi tính recency; naive → giả định UTC (C2-06)
- `RuntimeKernel.create()` **eager tạo memory db** (C2-05) — hành vi mới chủ ý, pattern giống EventService/audit.db

## 8. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/memory/contracts.py` | NEW | 5 pydantic models + `MemoryKind`/`MemoryStrategy` enums |
| `backend/src/aios_core/memory/coordinator.py` | NEW | `MemoryCoordinator` + `MemorySource` Protocol + `MemoryCoordinatorConfig` + `estimate_tokens` |
| `backend/src/aios_core/memory/sources.py` | NEW | 4 adapter (Conversation/Session/Knowledge/Artifact) |
| `backend/src/aios_core/knowledge/knowledge.py` | MOD (additive) | Thêm `list_chunks(source_id=None) -> list[ChunkRecord]` — query sqlite trực tiếp như `search()`, **không sửa `ChunksStore`**, `ORDER BY source_id, chunk_index` (C1-01/C2-14) |
| `backend/src/aios_core/memory/__init__.py` | MOD | Re-export public API (additive) |
| `backend/src/aios_core/config.py` | MOD | `MemoryBudgetSettings` + `MemorySettings.budget` (additive) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring `register_instance(MemoryCoordinator, ...)` (additive) |
| `backend/tests/test_memory_coordinator.py` | NEW | Unit + integration: contracts/7 strategies/filter/rank/dedup/compress/budget/inject/deterministic/wiring |
| `backend/tests/test_config.py` | MOD | Budget settings tests (additive) |
| `backend/tests/test_runtime_kernel.py` | MOD | `make_settings` override cả conversation + knowledge db (R2-1/R3-1); test resolve `MemoryCoordinator` |
| `backend/tests/test_api.py` | MOD | Fixture override cả `conversation_db_path` + `knowledge_db_path` (R2-1) |
| `backend/tests/test_architecture.py` | MOD | `test_inv_memory_import_allowlist` + INV-011 (agents không import memory/knowledge) |
| `aios/progress/tasks/TASK-023/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 9. Ghi chú thiết kế (cho critic phản biện)

- **Vị trí**: `memory/coordinator.py` thay vì package mới — coordinator thuộc domain memory; nếu critique cho rằng nên tách `intelligence/` thì phải cân nhắc chi phí chuyển + allow-list riêng (quyết định mở)
- **Sources tách file**: `sources.py` riêng để coordinator không ôm logic store (no God Object); adapter duck-typed qua Protocol → coordinator không biết implementation cụ thể (PLAN §3.4)
- **Budget mapping**: conversation→history, session→task, knowledge→knowledge, artifact→artifacts; system/reserve để cho TASK-024 — giữ PLAN số liệu 3K/2K/6K/5K/3K/1K nguyên vẹn trong Settings
- **Inject scope**: `EXECUTION` — "execution hiện tại" đúng nghĩa PLAN; key `memory.context` ổn định để TASK-024 và agent đọc
- **Không event mới**: tránh scope creep; observability M5 DoD gắn task sau
