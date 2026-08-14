# TASK-024 — Context Optimizer (M5-P9, Phase 1)

**Metadata**: TASK-024 | M5/P9 | 2026-08-14 | v4 (critique ×2 + review resolved) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/context/` (package mới: optimizer + contracts) + `kernel/runtime_kernel.py` (wiring) + `tests/`

## 1. Mục tiêu

Xây **Context Optimizer** — tầng quyết định *"Trong những thông tin đó (memory + system + user + execution state), nên đưa bao nhiêu và dưới dạng nào vào model?"* (PLAN §M5-4) — trách nhiệm KHÁC Memory Coordinator (TASK-023 trả lời *"nên lấy memory nào?"*).

Pipeline (PLAN §4): `Memory (TASK-023 output / MemoryContext) → Context Optimizer → Deduplicate → Compress → Prioritize → Token Budget → Final Context`.

- **Context Priority** (PLAN §5): `P0 System/Safety · P1 User Request · P2 Current Execution State · P3 Relevant Knowledge · P4 Relevant Memory · P5 Historical · P6 Optional` — **loại bỏ từ dưới lên nếu thiếu token, không truncate ngẫu nhiên**.
- **Context Compression 3 cấp** (PLAN §6, triết lý **Deterministic First → LLM Last**): L1 Deterministic (dedup/metadata thừa/merge fragments) · L2 Extractive (deterministic heuristic) · **L3 LLM compression = defer (stub interface, không implement)** — lý do ở §YC-5.
- **Token Budget** (INV-012): tổng context ≤ budget cấu hình; priority quyết định thứ tự giữ; per-tier cap; reserve.
- **Final Context**: đầu ra chuẩn có thứ tự cho model — sections xếp theo tier P0→P6, token count, budget/compression report.

Toàn bộ pipeline **deterministic, không bắt buộc LLM** — mọi bước test được bằng unit test (PLAN §23). Optimizer **chỉ đọc** qua `ContextService` public API, không ôm logic context service, không sửa `ContextService`/`MemoryCoordinator`/`ExecutionService`.

## 2. Phạm vi

**In**:
- `context/contracts.py` — NEW: `PriorityTier · ContextSection · TierBudgetReport · CompressionReport · FinalContext` (pydantic, `extra="forbid"`)
- `context/optimizer.py` — NEW: `ContextOptimizer` + `ContextOptimizerConfig` + `ContentCompressor` Protocol (stub L3) + `Level1Compressor`/`Level2Compressor` (deterministic, module-level functions)
- `context/__init__.py` — NEW: re-export public API (pattern `memory/__init__.py`)
- `kernel/runtime_kernel.py` — MOD (additive): wiring `register_instance(ContextOptimizer, ...)` — **tái dùng `settings.memory.budget` (MemoryBudget), KHÔNG thêm settings mới**
- `tests/test_context_optimizer.py` — NEW: unit + integration (deterministic, INV-012)
- `tests/test_architecture.py` — MOD: allow-list `context/` + INV-012 (tường minh hóa)
- `tests/test_runtime_kernel.py` — MOD (additive): resolve `ContextOptimizer`

**Out (không làm — tránh scope creep)**:
- **KHÔNG sửa** `MemoryCoordinator` / `memory/*` (TASK-023) — optimizer CHỈ đọc output đã inject (`memory.context` ở EXECUTION scope), không gọi pipeline memory lại
- **KHÔNG sửa** `ContextService` (context.py) — không thêm scope/key/setting; chỉ đọc `get`/`get_all`
- **KHÔNG sửa** `ExecutionService` / `orchestrator/` (planner, orchestrator, rule_engine...) — việc nối optimizer vào pipeline orchestration (PLAN §20) là task sau / harness M6; task này chỉ xây service + wiring vào RuntimeKernel
- **KHÔNG làm Model Router** (TASK-025): optimizer KHÔNG đọc context window / model metadata — budget nhận từ config; không chọn model
- **KHÔNG implement Level 3 LLM compression** — chỉ giữ interface (Protocol) + config field; lý do §YC-5
- **KHÔNG emit event mới** (EventType giữ nguyên); observability "context size / context compression" của M5 DoD — số liệu nằm trong `FinalContext` (compression/budget report), gắn metrics ở task sau
- **KHÔNG sửa `contracts/`** (INV-006 purity — contracts domain-local đặt trong `context/`, pattern `memory/`)
- **KHÔNG dùng LLM / random / thời gian thực ngoài clock injectable** ở bất kỳ bước nào

## 3. Input / Output

- **Input** (đọc qua `ContextService` public API — constructor dependency):
  - `user_request: str` — tham số bắt buộc của `optimize()` (P1)
  - `context.get_all(ContextScope.SYSTEM)` — system/safety content (P0)
  - `context.get_all(ContextScope.EXECUTION, inherit=False)` — execution state (P2), **trừ key `memory.context`** (xử lý riêng)
  - `context.get(ContextScope.EXECUTION, "memory.context", inherit=False)` — `MemoryContext | None` từ TASK-023 (P2 session / P3 knowledge / P4-P5 conversation / P6 artifacts); chưa inject → các tier này rỗng, không crash
  - `ContextOptimizerConfig` (budget = `MemoryBudget` tái dùng từ `memory.contracts` — cùng schema `MemoryBudgetSettings` của config.py; `relevant_threshold`; `max_compression_level`; `force_extractive`; clock injectable)
- **Output**:
  - `FinalContext` — sections đã sort theo tier (P0→P6, trong tier giữ thứ tự rank từ `MemorySelection` / thứ tự state), `total_tokens` ≤ usable budget, `tier_reports` (cap/used/dropped per tier), `compression` report, `truncated`, `created_at`
  - `FinalContext.render() -> str` — text thuần deterministic, format chuẩn cho model input
  - KHÔNG inject kết quả vào ContextService (không ghi đè `memory.context`) — người dùng (orchestrator/task sau) nhận return value trực tiếp

## 4. Yêu cầu chức năng

### YC-1 — Contract models (pydantic, `extra="forbid"`)
Trong `context/contracts.py`:
```python
class PriorityTier(str, Enum):
    P0_SYSTEM = "p0_system"          # System/Safety — không bao giờ cắt
    P1_USER = "p1_user"              # User Request — không bao giờ cắt
    P2_EXECUTION = "p2_execution"    # Current Execution State (session memory + state)
    P3_KNOWLEDGE = "p3_knowledge"    # Relevant Knowledge
    P4_MEMORY = "p4_memory"          # Relevant Memory (conversation score >= threshold)
    P5_HISTORICAL = "p5_historical"  # Historical (conversation score < threshold)
    P6_OPTIONAL = "p6_optional"      # Optional (artifacts)

class ContextSection(BaseModel):     # extra="forbid"
    tier: PriorityTier
    source: str                      # "system.<key>" | "user.request" | "execution.<key>" |
                                     # "memory.session" | "memory.knowledge" | "memory.history" | "memory.artifact"
    content: str
    tokens: int = 0                  # set tại build; content rỗng → 0 (không estimate_tokens — C2-12)

class TierBudgetReport(BaseModel):   # extra="forbid"
    tier: PriorityTier
    cap: int | None                  # None = uncapped (P1)
    used: int
    dropped_tokens: int
    dropped_items: int

class CompressionReport(BaseModel):  # extra="forbid"
    original_tokens: int             # tổng tokens ngay SAU build, TRƯỚC L1
    final_tokens: int
    ratio: float                     # round(final/original, 4); original=0 → 1.0
    levels_used: list[int]           # [1], [1,2], [1,2,3], [1,3] (terms rỗng → L2 no-op — C2-11)
    dropped_by_budget: int           # tokens loại do budget (không phải compress)

class FinalContext(BaseModel):       # extra="forbid"
    session_id: str
    sections: list[ContextSection]   # đã sort tier asc (P0→P6), trong tier giữ thứ tự
    total_tokens: int
    usable_budget: int               # total - reserve
    tier_reports: list[TierBudgetReport]
    compression: CompressionReport
    truncated: bool
    created_at: datetime

    def render(self) -> str: ...     # deterministic; format §YC-7
```
- `estimate_tokens` **import từ `aios_core.memory.coordinator`** (public API, đã re-export qua `memory/__init__.py`) — 1 nguồn token heuristic duy nhất, không duplicate
- **Test**: `extra="forbid"` (field thừa → `ValidationError`); tier enum đủ 7 giá trị đúng tên; `FinalContext.render()` trả str; `ratio` tính đúng (0 chia → 1.0); `ContextSection.tokens` tự set đúng `estimate_tokens`.

### YC-2 — Nguồn vào & tier mapping (P0..P6)
`ContextOptimizer.__init__(context: ContextService, config: ContextOptimizerConfig | None = None, now: Callable[[], datetime] = datetime.now(timezone.utc))` — `optimize(user_request: str) -> FinalContext`:

| Tier | Nguồn | Mapping |
|------|-------|---------|
| P0 | `context.get_all(SYSTEM)` | mỗi key → 1 section `source="system.<key>"`, content = `_serialize_value(value)` (bỏ value None/"" — C2-02: `_serialize_value`: scalar → str(); dict/list → `json.dumps(sort_keys=True, default=str)` **wrap try/except (TypeError, ValueError) → fallback `<TypeName>`**; set/frozenset → `str(sorted(v))`; object lạ → `f"<{type(v).__name__}>"` — C2-03) |
| P1 | tham số `user_request` | 1 section `source="user.request"`; `user_request.strip()==""` → section rỗng hợp lệ (vẫn render; **exempt L1 empty-drop** — C2-04; **tokens = 0 cho content rỗng** — C2-12) |
| P2 | `context.get_all(EXECUTION, inherit=False)` trừ `memory.context` + `memory_context.selection` items kind=SESSION | state key → `source="execution.<key>"`, content `f"{key}: {_serialize_value(value)}"` (bỏ value None/""/rỗng; **bỏ key bắt đầu `_`** — metadata thừa L1); session memory → `source="memory.session"`; **thứ tự: state keys (insertion order) TRƯỚC, session items (rank desc) SAU (C2-04)** — cắt từ cuối = session score thấp trước, rồi state keys cuối |
| P3 | items kind=KNOWLEDGE (từ `memory_context.selection.items` — **dùng items có score, không dùng `sections` đã mất metadata**) | mỗi candidate → 1 section `source="memory.knowledge"`, content = `candidate.content` (đã compress bởi TASK-023) |
| P4 | items kind=CONVERSATION có `score.total >= config.relevant_threshold` | `source="memory.history"` |
| P5 | items kind=CONVERSATION có `score.total < config.relevant_threshold` | `source="memory.history"` |
| P6 | items kind=ARTIFACT | `source="memory.artifact"` |

- **`memory_context` = `context.get(EXECUTION, "memory.context", inherit=False)`** — nếu `None` HOẶC **không phải instance `MemoryContext` (isinstance check — R3-2, ContextService public không namespace)** → P2(session)/P3/P4/P5/P6 rỗng, pipeline chạy bình thường
- Thứ tự nội bộ trong tier P3/P4/P5/P6 = thứ tự `selection.items` (đã sort `total desc` bởi TASK-023 — giữ nguyên); P2 = thứ tự `get_all` (insertion order — deterministic cho cùng chuỗi set)
- **Test**: seed ContextService (SYSTEM 2 keys, EXECUTION 2 keys + `memory.context` với selection đủ 4 kind + scores 0.9/0.2) → `optimize("fix bug")` → assert mỗi tier đúng nguồn/đúng content/đúng thứ tự; conversation 0.9 → P4, 0.2 → P5; chưa inject memory → P3..P6 rỗng không crash; state key `_private` bị bỏ.

### YC-3 — Compression Level 1 (Deterministic — luôn chạy)
Module-level functions trong `optimizer.py` (thuần hàm, test trực tiếp):
1. **Dedup toàn cục**: key = SHA-256 của `_normalize(content)` (strip + lowercase + collapse whitespace — triển khai local, không import private của memory); 2 section trùng key → giữ section **tier cao hơn** (P0 > P1 > ... > P6), hoà tier → giữ section đọc trước (thứ tự build ổn định); **P0/P1 KHÔNG bao giờ là victim của dedup** (C3-07) — chỉ tier thấp hơn bị loại khi trùng P0/P1
2. **Metadata thừa**: bỏ section value None/""/rỗng (đã làm ở build YC-2; **P1 rỗng exempt** — C2-04); state key bắt đầu `_` bỏ (YC-2)
3. **Merge fragments**: section cùng `(tier, source)` → gộp 1 section, content join `"\n"` (loại header lặp); **LOẠI TRỪ source `memory.*`** (C1-01) — memory tiers giữ 1 section/candidate (thứ tự items = rank desc sẵn có); **ghi chú (C2-02)**: với mapping source per-key hiện tại (`system.<key>`/`execution.<key>` unique), merge không fire trên input thật — giữ hàm thuần + unit test như **defensive** (PLAN §6 yêu cầu merge), không phải stage tích cực
4. **"message cũ"** (PLAN §6 L1): đã được phủ qua P4/P5 threshold — `score.total` gồm recency decay (TASK-023) → L1 không lặp lại (C3-05)
5. **Re-token**: `tokens = estimate_tokens(content)` tính lại cho MỌI section sau mỗi transform (C2-03)
- **Test**: 2 section trùng content (system + memory) → 1 section giữ tier cao hơn (P0/P1 không bị dedup loại); 3 section cùng (tier, source) execution → 1 section nối đúng thứ tự; **2 candidate cùng tier memory (source memory.knowledge) KHÔNG bị merge** (giữ 2 section, thứ tự rank); dedup chạy được trên content khác whitespace/case; L1 không đổi content section không trùng; re-token đúng sau merge.

### YC-4 — Compression Level 2 (Extractive — deterministic heuristic)
- **Kích hoạt**: chỉ khi tổng tokens sau L1 **vượt usable budget** HOẶC `config.force_extractive=True` — không chạy khi dư budget (đảm bảo không mất thông tin vô cớ); **khi KÍCH HOẠT → `levels_used` có 2 kể cả no-match theo content (R2-2)**
- **Chỉ áp dụng cho tier P3/P4/P5/P6** (P0/P1/P2 giữ nguyên vẹn — system/safety/user/state không được extract)
- Thuật toán (thuần hàm `extractive_compress(section, query_terms, max_chars) -> str`):
  1. `terms = set(user_request.lower().split())`; **terms rỗng → L2 no-op toàn pipeline** (`levels_used` không có 2) — C2-01
  2. Tách câu bằng regex boundary `(?<=[.!?])\s+` (giữ delimiter)
  3. Giữ các câu có `any(term in sentence.lower() for term in terms)` — **substring match, case-insensitive** (C2-01); **không câu nào trùng → giữ NGUYÊN section** (không cắt về câu đầu — cắt việc đó cho budget stage); không xử lý stopword (giữ — deterministic)
  4. Nối câu giữ được; nếu vượt `config.extractive_max_chars` (mặc định 4000/section) → cắt `content[:max_chars-1] + "…"` (cùng quy ước TASK-023 C2-08)
  5. Re-token: `tokens = estimate_tokens(content mới)` (C2-03)
- **Test**: section 10 câu, user_request có term xuất hiện ở 2 câu → output chỉ 2 câu; case-mismatch ("Fix" vs "fix") → match được; punctuation ("bug," vs "bug") → match được; không term trùng → giữ NGUYÊN section; **request rỗng + over-budget → `levels_used == [1]`**; output > max_chars → cắt đúng (max_chars-1 + "…"); P0/P1/P2 không bị đổi; dư budget → L2 không chạy (`levels_used == [1]`); `force_extractive=True` → chạy dù dư budget.

### YC-5 — Level 3 LLM compression — STUB / DEFER (quyết định scope)
- Giữ **interface duy nhất**: `ContentCompressor = Callable[[list[ContextSection], int], list[ContextSection]]` (nhận sections + usable budget → trả sections đã nén) — inject qua `ContextOptimizerConfig.compressor: ContentCompressor | None = None`
- `max_compression_level` mặc định `2`; nếu config có compressor → L3 chạy sau L2 khi vẫn vượt budget (trước khi cắt), ghi `levels_used` có 3; **sau L3, re-token mọi section (C2-05)**
- **KHÔNG implement L3 trong task này** — lý do:
  1. L3 cần model provider + tokenizer — phụ thuộc TASK-025 Model Router (chưa có)
  2. Triết lý Deterministic First: L1+L2 + cut-from-bottom đã phủ trường hợp vượt budget
  3. Tránh scope creep; L3 gắn sau (M5 Phase 2 / harness M6) khi có model pipeline thật
- **Test**: config mặc định → L3 không chạy, không raise; config có compressor (lambda fake) + vượt budget → compressor được gọi đúng 1 lần với sections hợp lệ, output được dùng; compressor trả về sections không hợp lệ (tier không tồn tại) → `ValidationError` khi dựng FinalContext; **compressor đổi content dài gấp đôi → token cập nhật (re-token), cut đúng (C2-05)**; terms rỗng + L2 no-op + vẫn vượt → compressor chạy → `levels_used == [1, 3]` (C2-11).

### YC-6 — Token Budget & loại từ dưới lên (INV-012)
- **Nguồn budget**: tái dùng `MemoryBudget` (từ `memory.contracts`, mirror `MemoryBudgetSettings` config.py — TASK-023 comment đã chốt "system/reserve dành cho TASK-024")
- `ContextOptimizerConfig.budget: MemoryBudget = MemoryBudget()` → `total = sum(budget.model_dump().values())` (20K — **KHÔNG `sum(budget)` — pydantic v2 iter trả (key,value) tuples → TypeError — R1-1**), `usable = total - budget.reserve` (19K)
- **Tier caps** (giữ nguyên số liệu PLAN §3.3; **P0/P1 exempt khỏi per-tier cap enforcement — cap = trần BÁO CÁO, không cắt — C1-02**):
  | Tier | Cap |
  |------|-----|
  | P0 | `budget.system` (3000) — báo cáo, không enforce |
  | P1 | `None` (giữ nguyên vẹn) |
  | P2 | `budget.task` (2000) |
  | P3 | `budget.knowledge` (6000) |
  | P4 | `budget.history` (5000) — **shared cap với P5; ghi ở P4, P5 `cap=None`** (C3-08) |
  | P5 | `None` (shared với P4 — ưu tiên loại P5 trước P4) |
  | P6 | `budget.artifacts` (3000) |

  → `sum(caps thực thi: P2..P6) = 16000`; usable = 19000 — chênh lệch 3000 = P0 (exempt, pre-check riêng). **Ghi chú (C3-09)**: P1 tokens hiệu quả "mượn" từ tier dưới qua total cut — hành vi cố ý theo priority ("nhất quán không cắt thêm" chỉ đúng khi P1 = 0)
- **Thứ tự xử lý**: build (YC-2) → **L1** (YC-3) → nếu vượt usable → **L2** (YC-4) → nếu vẫn vượt → **L3** (nếu có compressor, YC-5) → **pre-check** → **cut từ dưới lên**:
  1. **Pre-check fail-fast (C2-10: chạy SAU L2/L3, trên token đã re-token)**: nếu `P0 + P1 tokens > usable` → `raise ValueError("system + user request exceed usable budget")` (input bất khả thi — không thể tuân INV-012) — **đây là enforcement DUY NHẤT cho P0/P1** (C1-02)
  2. Per-tier cap: với mỗi tier từ P6 → P2 (**P0/P1 exempt — C1-02**), loại section từ CUỐI tier (ít ưu tiên nhất) tới khi tier ≤ cap (P4/P5 gộp: loại hết P5 trước rồi mới P4); **section đơn > cap tier → KHÔNG drop trắng: giữ prefix `content[:X-1] + "…"` với X chars = cap_tokens × 4 (C2-07)**
  3. Tổng: nếu `sum(tokens) > usable` → loại section từ tier thấp nhất (P6 → P5 → P4 → P3 → P2; **P0/P1 không bao giờ loại**) tới khi ≤ usable
- `truncated = True` nếu có bất kỳ section nào bị LOẠI (tier cap hoặc tổng — force_extractive chỉ cắt content, không set truncated — C2-15; **prefix-truncate section đơn > cap cũng KHÔNG set truncated, phần cắt KHÔNG tính dropped_by_budget — chỉ section bị drop — R2-1**); `dropped_by_budget` = tổng tokens bị loại; `tier_reports` ghi `used/dropped_*` per tier (`final_tokens` = tổng cuối sau MỌI bước — C3-08); **re-token sau mọi transform kể cả prefix-truncate (R2-1)**
- **Test (INV-012 — định lượng theo PLAN §23)** — budget cụ thể từng scenario (C2-06/R1-2 — usable = sum(5 field không reserve)):
  - **Scenario thứ tự loại**: `MemoryBudget(system=400, task=500, knowledge=600, history=800, artifacts=500, reserve=800)` → total 3600 → **usable = 2800**; seed P0 400 + P1 300 + P2 500 + P3 600 + P4 800 + P5 600 + P6 500 = 3700 → per-tier: P4+P5 = 1400 > 800 → loại P5 (600) → 800 = cap ✓; total: 3100 > 2800 → loại P6 (500) → 2600 ≤ 2800 ✓ — assert P5 loại ở per-tier, P6 loại ở total, P4 sống, `total_tokens ≤ 2800`, P0/P1 nguyên vẹn
  - **Item-level**: 2 candidate cùng tier (memory.knowledge), cap cắt → candidate cuối (score thấp hơn) bị loại trước (C1-01)
  - **P0 vượt cap (R3-5)**: budget riêng `MemoryBudget(system=3500, task=500, knowledge=600, history=800, artifacts=500, reserve=800)` → usable 5900; seed P0 3600 + P1 100 = 3700 ≤ 5900 → giữ nguyên vẹn, `tier_reports` ghi `used 3600 > cap 3500` (báo cáo — C1-02)
  - Per-tier cap: P3 vượt cap → loại cuối tier P3; P0+P1 > usable → `ValueError`; đủ budget → `truncated=False`; **edge: sau re-token (merge/L2) vượt đúng 2 token → cut dừng đúng, không cắt thừa (C2-14)**

### YC-7 — Final Context & render (đầu ra chuẩn cho model)
- `FinalContext.sections` đã sort: `tier asc` (P0→P6), trong tier giữ thứ tự build (rank/insertion)
- `render() -> str` deterministic:
  ```
  [System]
  <content P0 sections, join "\n">
  [User Request]
  <content P1>
  [Execution State]
  ...
  [Knowledge]
  ...
  [Memory]
  ...
  [Historical]
  ...
  [Optional]
  ...
  ```
  (header theo tier; section cùng tier nối `"\n"`; tier rỗng → bỏ header; **ngoại lệ: P1 section rỗng vẫn emit header `[User Request]`, không có dòng content — R3-4/C2-12**)
- **Test**: render đúng thứ tự 7 tier (tier rỗng bỏ header); cùng input 2 lần render → y hệt; render không chứa budget-report nội dung (report tách riêng trong model); `optimize("")` → output có header `[User Request]` không kèm content.

### YC-8 — Deterministic tổng thể
- Cùng input (ContextService state + user_request + config + fixed clock) → `FinalContext.model_dump()` y hệt 2 lần chạy (giá trị + thứ tự sections)
- Không LLM, không random; `now` clock injectable (mặc định `datetime.now(timezone.utc)`) — test dùng datetime cố định
- **Test**: chạy `optimize` 2 lần trên cùng fixture (clock cố định) → `model_dump()` bằng nhau; thay đổi 1 state key → output khác đúng chỗ (không lan toả).

### YC-9 — Wiring (RuntimeKernel.create, additive)
- Trong `RuntimeKernel.create` (sau block memory coordinator — TASK-023):
  ```python
  from ..context.optimizer import ContextOptimizer, ContextOptimizerConfig
  context_optimizer = ContextOptimizer(
      context=context_service,
      config=ContextOptimizerConfig(budget=MemoryBudget(**settings.memory.budget.model_dump())),
  )
  container.register_instance(ContextOptimizer, context_optimizer)
  ```
- KHÔNG thêm settings mới (tái dùng `settings.memory.budget`); `RuntimeKernel.create()` chạy được với Settings default; KHÔNG sửa service đã đăng ký
- **Test** (integration): `RuntimeKernel.create().container.resolve(ContextOptimizer)` trả instance; `optimize("hello")` chạy end-to-end với tmp settings (pattern `make_settings(tmp_path)` — TASK-023 R2-1).

### YC-10 — Integration MemoryCoordinator ↔ ContextOptimizer (end-to-end)
- Chuỗi: `MemoryCoordinator.inject(query)` (TASK-023, tmp stores) → `ContextOptimizer.optimize(user_request)` → `FinalContext`
- Assert: sections kind=KNOWLEDGE/CONVERSATION/ARTIFACT/SESSION hiện đúng tier P3/P4-P5/P6/P2 với đúng content; `total_tokens` của phần memory ≤ budget tương ứng; `truncated` phản ánh đúng
- **Test**: dùng `MemoryCoordinator` thật (conversation db + knowledge db tmp, seed vài message/chunk/artifact) + ContextService chung → inject → optimize → assert đủ 4 loại memory xuất hiện đúng tier.

## 5. Yêu cầu kiến trúc

### 5.1 INV-012 — Context Budget (behavioral enforcement)
- Bản chất: "Context không được vượt budget" là invariant HÀNH VI — AST không verify được → enforcement = **test functional** `test_inv012_context_budget` trong `test_context_optimizer.py`: seed vượt budget (usable 2K, PLAN §23 pattern) → assert `final.total_tokens ≤ usable` + thứ tự loại từ dưới lên (§YC-6). Test chạy nhiều scenario (vượt nhẹ, vượt nặng, per-tier cap, P0+P1 bất khả thi)
- Arch test hỗ trợ: `context/` không import models/knowledge/orchestrator (allow-list §5.2) — chặn đường "bỏ qua budget bằng cách ôm logic model/other service"

### 5.2 Allow-list import `context/` (test mới `test_inv_context_import_allowlist` — pattern `test_inv_memory_import_allowlist`)
- **aios_core allowed**: `aios_core.kernel.services` (ContextService/ContextScope) + `aios_core.memory` + `aios_core.memory.contracts` (MemoryBudget/MemoryContext/MemorySelection/MemoryCandidate/MemoryKind) + `aios_core.memory.coordinator` (estimate_tokens — public)
- **CẤM**: `aios_core.models` (deterministic — INV-010), `aios_core.knowledge` (optimizer không truy cập knowledge trực tiếp — chỉ qua memory.context), `aios_core.orchestrator` (context/ là intelligence độc lập, không phụ thuộc control plane), `aios_core.contracts` (INV-006 — contracts domain-local) — **kể cả dưới TYPE_CHECKING** (bài học TASK-023 C2-01: `collect_imports` đếm MỌI Import node)
- **external allowed**: `pydantic`, `typing`, `datetime`, `enum`, `re`, `hashlib`, `math`, **`json`** (C2-01 — YC-2 `_serialize_value` dùng `json.dumps`)
- Scan toàn dir `context/*.py` qua `collect_imports` (pattern y hệt memory/), loại trừ intra-package (`startswith("aios_core.context")`)
- **Cycle check**: `context/ → memory/` 1 chiều (memory/ không import context/) — không cycle; `memory/` allow-list hiện tại không đổi (không thêm import mới vào memory/)

### 5.3 Deterministic first
- Mọi stage thuần hàm (build/dedup/merge/extractive/cut đều module-level functions hoặc private methods thuần): không LLM, không random, clock injectable; thứ tự sections cố định; tie-break đầy đủ; test `model_dump()` bằng nhau qua 2 lần chạy (YC-8)
- L1/L2 test trực tiếp trên hàm thuần (không cần ContextService)
- **Config defaults (C3-06)**: `budget=MemoryBudget()`, `relevant_threshold=0.5`, `max_compression_level=2`, `force_extractive=False`, `extractive_max_chars=4000`, `compressor=None`; **clock chỉ ở `__init__` param** (config không chứa clock)

### 5.4 No God Object
- `ContextOptimizer` **chỉ điều phối** pipeline: đọc input qua `ContextService` public API (`get`/`get_all` — KHÔNG `set`/`delete`, không sửa context service); logic compress tách module-level functions (`Level1Compressor`-style pure functions); logic budget/cut là function riêng
- Optimizer **không biết** MemoryCoordinator implementation — chỉ đọc contract `MemoryContext` từ ContextService; không gọi lại pipeline memory

### 5.5 Additive only
- `git diff` sau implement: `memory/*`, `kernel/services/context.py`, `kernel/services/execution.py`, `orchestrator/*`, `config.py`, `contracts/` **không đổi**; chỉ thêm file mới (`context/`) + mở rộng `runtime_kernel.py` / `test_architecture.py` / `test_runtime_kernel.py` / tests mới
- KHÔNG đổi API có sẵn: `ContextService`, `MemoryCoordinator`, `ExecutionService` giữ nguyên

### 5.6 Vị trí package (quyết định mở — cho critic phản biện)
- **Đề xuất: package mới `aios_core/context/`** (2 file + `__init__`), KHÔNG đặt trong `orchestrator/`:
  1. PLAN §26: M5 intelligence "dùng chung cho Runtime, Orchestrator và Harness (M6)" — package độc lập (như `memory/` TASK-023) phục vụ được nhiều client; `orchestrator/` là 1 client (control plane xử lý request)
  2. Tránh đảo chiều phụ thuộc: `orchestrator → memory` là coupling mới (orchestrator hiện độc lập memory); `context/ → memory/` giữ đúng chiều intelligence → data
  3. INV-005/INV-010 đang ràng buộc `orchestrator/` (cấm models) — optimizer không vi phạm, nhưng đặt chung sẽ khiến allow-list tương lai phức tạp + trộn 2 trách nhiệm
  4. Pattern đồng nhất M5: `memory/` (023) → `context/` (024) → Model Router (025) — mỗi năng lực 1 package, contracts riêng (INV-006), allow-list riêng
- **Phương án thay thế**: `orchestrator/context_optimizer.py` (gần nơi dùng) — không vi phạm INV-005/010 hiện tại (không import models), nhưng thêm coupling orchestrator→memory + không dùng chung được sạch cho Harness M6
- Critic được phép phản biện chọn phương án khác; nếu đổi → cập nhật allow-list tương ứng (orchestrator/ không có allow-list tổng hiện tại — cần thêm test rule riêng)

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — 5 models pydantic `extra="forbid"` (PriorityTier 7 giá trị, ContextSection, TierBudgetReport, CompressionReport, FinalContext); thừa field → `ValidationError`; `render()` deterministic (YC-1, YC-7)
- [ ] **AC2**: Tier mapping — seed đầy đủ 7 nguồn → đúng tier/đúng content/đúng thứ tự; conversation theo `relevant_threshold` phân P4/P5; chưa inject memory → P3..P6 rỗng không crash (YC-2)
- [ ] **AC3**: L1 — dedup toàn cục (giữ tier cao hơn; **P0/P1 không là victim**), bỏ state metadata thừa (`_`-key, None/""), merge cùng (tier, source) **trừ source `memory.*`** (defensive — C2-02/C2-08) (YC-3)
- [ ] **AC4**: L2 extractive — chỉ giữ câu trùng term (substring case-insensitive); không trùng → giữ NGUYÊN section; request rỗng → L2 no-op (kể cả `force_extractive=True` — C2-09); cắt đúng `max_chars-1 + "…"`; chỉ áp dụng P3..P6; không chạy khi dư budget; `force_extractive` override (YC-4)
- [ ] **AC5**: L3 stub — mặc định không chạy/không raise; có compressor → gọi đúng 1 lần khi vượt budget; compressor trả sections sai tier → `ValidationError` (YC-5)
- [ ] **AC6**: **INV-012** — test seed vượt usable (budget cụ thể từng scenario — C2-06) → `final.total_tokens ≤ usable`; **loại từ dưới lên đúng thứ tự (P6 → P5 → P4 → P3 → P2)**, trong tier loại từ cuối; **item-level: 2 candidate cùng tier → loại candidate cuối (score thấp) trước**; per-tier cap đúng (P2 2000/P3 6000/P4+P5 5000/P6 3000); **section đơn > cap → truncate prefix thay vì drop (C2-07)**; **P0/P1 exempt per-tier cap nhưng giữ nguyên vẹn; P0 > cap → báo cáo, không cắt**; P0+P1 > usable → `ValueError`; đủ budget → `truncated=False` (YC-6, PLAN §23 test strategy)
- [ ] **AC7**: FinalContext — sections sort tier asc; `render()` đúng format 7 header (tier rỗng bỏ header; **P1 rỗng vẫn emit header, không có dòng content — C2-12**); token/budget/compression report chính xác (YC-1, YC-7)
- [ ] **AC8**: Deterministic — cùng fixture + clock cố định chạy 2 lần → `model_dump()` bằng nhau (YC-8)
- [ ] **AC9**: Integration — `MemoryCoordinator.inject` → `ContextOptimizer.optimize` end-to-end với store thật (tmp db) → memory xuất hiện đúng tier, không vượt budget (YC-10)
- [ ] **AC10**: Wiring — `RuntimeKernel.create()` resolve `ContextOptimizer`; optimize chạy end-to-end; test dùng tmp settings; full suite pytest pass; coverage toàn suite ≥ 80% cứng (95% mục tiêu) (YC-9)
- [ ] **AC11**: Architecture — `test_inv_context_import_allowlist` pass (context/ chỉ import allow-list; cấm models/knowledge/orchestrator/contracts kể cả TYPE_CHECKING); `test_inv012_context_budget` pass; git diff verify additive only (§5.1, §5.2, §5.5)

## 7. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Chồng lấn compress/budget với TASK-023 (023 đã cắt per category + truncate per candidate) | Ranh giới cứng: 023 = chọn memory + truncate per candidate + budget per category; 024 = dedup TOÀN CỤC (mọi nguồn) + extractive + tier priority P0..P6 + tổng budget + final context. Tier caps TRÙNG số category budget → không double-cut khi không vượt (thiết kế cố ý, §YC-6) |
| L3 LLM compression defer — PLAN nói "chỉ khi cần" | Chốt defer + lý do (cần Model Router TASK-025 + tokenizer; deterministic first; tránh scope creep); giữ interface Protocol để gắn sau không phá API |
| `orchestrator/` là nơi dùng — đặt package riêng có xa rời thực tế? | §5.6 nêu 2 phương án + lý do chọn `context/` (dùng chung Runtime/Orchestrator/Harness M6 — PLAN §26); critic phản biện được |
| Budget tổng 20K cố định ≠ context window model thật | Budget là cấu hình (`MemoryBudget`, tái dùng `settings.memory.budget` — env override được `AIOS_MEMORY__BUDGET__*`); việc lấy context window từ model là TASK-025 Model Router — ghi nhận giả định |
| `get_all(EXECUTION)` có thể chứa value không serializable (object) | Serialize deterministic: `str(value)`; `MemoryContext` value (key `memory.context`) tách xử lý riêng qua contract — không `str()` lên nó |
| Double-cut: memory.context đã cắt 16K → optimizer cắt lại gây mất thông tin ngoài ý muốn | Tier caps = đúng số category budget của 023 → phần memory chỉ bị cắt THÊM khi tổng (system+user+state) vượt usable — cắt từ dưới lên đúng PLAN §5; test AC6 bao phủ |
| P4/P5 phân loại bằng threshold 0.5 — mang tính heuristic | Deterministic + cấu hình được (`relevant_threshold`); score.total từ TASK-023 đã là tổng hợp semantic/relevance/recency/importance/source_priority — nền tảng hợp lý; ghi giả định |
| `render()` format chưa tối ưu cho prompt thật | Đây là format v1 deterministic — tối ưu prompt format là việc của task gắn model (TASK-025/harness M6); API `render()` đổi được không phá contract model |

**Giả định**:
- Token estimate dùng heuristic `ceil(len/4)` của TASK-023 (import `estimate_tokens` — 1 nguồn duy nhất); chính xác hoá khi có tokenizer thật (TASK-025)
- `memory.context` là nguồn DUY NHẤT của P3/P4/P5/P6 — optimizer không gọi `MemoryCoordinator` lại (INV-011 giữ nguyên: Agent/optimizer không chạm memory trực tiếp)
- `MemorySelection.items` giữ `(candidate, score)` với content đã compress per-candidate bởi 023 — optimizer tái dùng content đó, không re-truncate per-candidate (extractive L2 là cấp khác)
- P2 gộp session memory + execution state dưới 1 cap `task` (2000) — vì cả 2 đều là trạng thái execution hiện tại
- Session id của optimizer = `session_id` trong `MemoryContext` (đọc từ memory.context); nếu chưa inject memory → `session_id = ""` + ghi nhận trong FinalContext
- KHÔNG inject FinalContext vào ContextService — người dùng nhận return value (tránh ghi đè memory.context / tạo phụ thuộc ẩn)
- `RuntimeKernel.create()` eager tạo db — hành vi đã có từ TASK-023, không đổi; test dùng tmp settings

## 8. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/context/contracts.py` | NEW | `PriorityTier` + `ContextSection` + `TierBudgetReport` + `CompressionReport` + `FinalContext` (pydantic `extra="forbid"`) |
| `backend/src/aios_core/context/optimizer.py` | NEW | `ContextOptimizer` + `ContextOptimizerConfig` + `ContentCompressor` Protocol (L3 stub) + pure functions: `_normalize`/`deduplicate`/`merge_fragments` (L1), `extractive_compress` (L2), `apply_budget`/cut-from-bottom (INV-012) |
| `backend/src/aios_core/context/__init__.py` | NEW | Re-export public API (additive) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring `register_instance(ContextOptimizer, ...)` (additive, tái dùng `settings.memory.budget`) |
| `backend/tests/test_context_optimizer.py` | NEW | Unit (contracts/mapping/L1/L2/L3-stub/budget INV-012/render/deterministic) + integration (MemoryCoordinator inject → optimize; RuntimeKernel wiring) |
| `backend/tests/test_architecture.py` | MOD | `test_inv_context_import_allowlist` + ghi chú INV-012 (behavioral — §5.1) |
| `backend/tests/test_runtime_kernel.py` | MOD | `make_settings` tái dùng; test resolve `ContextOptimizer` (additive) |
| `aios/progress/tasks/TASK-024/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 9. Ghi chú thiết kế (cho critic phản biện)

- **Vị trí package `context/` vs `orchestrator/`** — quyết định mở (§5.6); nếu critic chọn `orchestrator/` cần: (a) verify không vi phạm INV-005/INV-010 (không import models — pass), (b) thêm allow-list rule riêng cho file đó, (c) chấp nhận coupling orchestrator→memory
- **Budget mapping tái dùng `MemoryBudget`** — KHÔNG thêm settings mới; tier caps trùng số category budget 023 (cố ý, tránh double-cut); critic cân nhắc: có cần `ContextBudgetSettings` riêng (total context window) không?
- **L3 defer nhưng giữ interface** — cân nhắc: nên fail-fast (raise khi cần L3 mà không có compressor) hay fallback cut im lặng? Spec chốt fallback + ghi `levels_used` không có 3
- **P4/P5 = threshold theo `score.total`** (0.5) — heuristic đơn giản; phương án khác: dùng recency threshold (cần clock) — spec chọn content/score-based để deterministic không phụ thuộc thời gian
- **P1 user request là tham số bắt buộc** — không đọc USER scope từ ContextService (tránh mơ hồ nguồn); critic có thể muốn đọc USER scope làm fallback
- **Không inject FinalContext vào ContextService** — return value trực tiếp; nếu critic muốn inject key `context.final` (EXECUTION) cần cân nhắc ghi đè/chu kỳ sống
