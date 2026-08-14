# TASK-025 — Model Router (M5-P9, Phase 2)

**Metadata**: TASK-025 | M5/P9 | 2026-08-14 | v3 (critique-1 + critique-2 resolved) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/models/` (mở rộng: `capability.py` + subpackage `router/`) + `config.py` + `config.yaml` + `kernel/runtime_kernel.py` + `tests/`

## 1. Mục tiêu

Xây **Model Router** — tầng trả lời *"Request này nên dùng model nào?"* (PLAN §7) — trách nhiệm KHÁC `ModelRegistry` (TASK-006 trả lời *"model nào tồn tại?"*). Router chọn model theo **Routing Policy** (PLAN §8, deterministic filter theo capability metadata §8.1), có **fallback** tuân policy (PLAN §9: `GPT → timeout → DeepSeek → rate limit → Ollama`), KHÔNG thành God Object (PLAN §10: chia 6 module nhỏ).

Pipeline (PLAN §7): `Request → Model Router {Quality · Cost · Latency} → Model Selection`. Router **chỉ chạy khi request cần model** (PLAN §20 — việc nối vào pipeline orchestration là TASK-026, ngoài phạm vi).

- **Routing Policy** (PLAN §8): `routing: {default: balanced, policies: {cheap: {max_cost: 0.01}, fast: {max_latency_ms: 2000}, quality: {min_quality: 0.9}, local: {providers: [ollama]}}}` — đánh giá **deterministic** (filter theo `ModelCapability`), không LLM.
- **Model Capability** (PLAN §8.1): `model_id, provider, context_window, input_cost, output_cost, latency_class, reasoning, coding, vision, tool_calling, structured_output, availability` — **lưu ở ModelRegistry** (quyết định §5.6), provider hiện tại KHÔNG đổi.
- **Fallback** (PLAN §9): lỗi model (timeout/rate limit/unavailable) → model kế tiếp trong danh sách đã qua policy; **PHẢI tuân Policy** (INV-013); `ModelHealth` theo dõi trạng thái (cooldown/disable).
- **INV-013** (PLAN §22): Model selection phải qua Routing Policy — enforcement behavioral + AST (§5.1).

Toàn bộ routing/filter/fallback **deterministic, không LLM, offline** — mọi bước test được bằng unit test (PLAN §23): cheap policy → model rẻ nhất; quality policy → model chất lượng nhất; timeout → fallback đúng thứ tự; offline (mock 0 lần gọi LLM) vẫn chọn được deterministic.

## 2. Phạm vi

**In**:
- `models/capability.py` — NEW: `ModelCapability` (pydantic, `extra="forbid"`) + factory `default()`
- `models/registry.py` — MOD (additive): `register_capability` / `capability` / `capabilities()`; `register()` thêm kwarg `capability=None` (backward compatible); resolution: explicit → provider `capability()` duck-typed → `ModelCapability.default()`
- `models/router/` — NEW subpackage 8 file: `contracts.py` (RoutingPolicy/PolicyRule/RouteRequest/RouteDecision/RejectedCandidate/HealthStatus/HealthConfig/ModelRouterConfig), `policy.py` (RoutingPolicy — parse + validate), `cost.py` (CostEstimator — cost/quality/latency/balanced, thuần hàm), `availability.py` (AvailabilityChecker), `health.py` (ModelHealth state machine, clock injectable), `selector.py` (ModelSelector — filter + rank + pick), `fallback.py` (FallbackResolver), `router.py` (ModelRouter — chỉ điều phối: `select()` + `chat()` fallback loop)
- `models/errors.py` — MOD (additive): thêm `RouterError(ModelError)` + **`ModelRateLimitError(ModelError)`** (C1-02 — chain fallback PLAN §9 có rate-limit)
- `models/__init__.py` — MOD (additive): re-export `ModelCapability`, `ModelRouter`, `RoutingPolicy`, `RouteRequest`, `RouteDecision`
- `config.py` — MOD (additive): `RoutingRuleSettings` + `RoutingSettings` (pydantic `extra="forbid"`, mirror contract — pattern `MemoryBudgetSettings`) + `ModelsSettings.routing: RoutingSettings = RoutingSettings()`
- `config.yaml` — MOD: block `models.routing` (default balanced + 4 policies theo PLAN §8)
- `kernel/runtime_kernel.py` — MOD (additive): wiring `register_instance(ModelRouter, ...)` + `register_capability("mock", ...)`; tái dùng `settings.models.routing`
- `tests/test_model_router.py` — NEW: unit + integration (deterministic, INV-013)
- `tests/test_architecture.py` — MOD: allow-list `models/router/` + INV-013 (AST + behavioral ghi chú)
- `tests/test_runtime_kernel.py` — MOD (additive): resolve `ModelRouter`
- `tests/test_models.py` — MOD (additive): test registry capability API

**Out (không làm — tránh scope creep)**:
- **KHÔNG sửa provider hiện tại** (`mock.py` / `openai_provider.py` / `ollama_provider.py`) và **KHÔNG sửa `ModelContract` ABC** — capability gắn qua registry, provider duck-typed (optional, chưa provider nào implement)
- **KHÔNG sửa `PolicyService`** (kernel/services/policy.py — pre-execution permission policy) — routing policy là domain `models/`, KHÔNG import kernel/policy (allow-list §5.2); không trộn 2 hệ thống policy
- **KHÔNG sửa `orchestrator/`** (planner, orchestrator, api/wiring.py...) — nối router vào pipeline (PLAN §20) là TASK-026; `api/wiring.py` + `runtime_kernel.py` là composition root (exemption INV-013, §5.1); **GHI NHẬN**: TASK-026 cần inject `ModelRouter` instance (pattern `Orchestrator.model` hiện tại — untyped) vì INV-005 rule A chặn `orchestrator/ → models`
- **KHÔNG nối L3 compression (TASK-024) vào router** — chỉ ghi nhận: L3 cần model provider/tokenizer; kết nối ở task sau (harness M6); router cung cấp `context_window`/cost trong `ModelCapability` cho việc đó
- **KHÔNG gọi `model.is_available()` trong routing** — `OllamaModel.is_available()` là HTTP call (network I/O) → vi phạm deterministic-first offline; availability dùng flag tĩnh trong `ModelCapability`, trạng thái động qua `ModelHealth` (§YC-5)
- **KHÔNG emit event mới** (EventType giữ nguyên); observability "model selected / model fallback" (M5 DoD) — số liệu nằm trong `RouteDecision` (return value), gắn metrics ở task sau
- **KHÔNG persistence `ModelHealth`** (in-memory; mất khi restart — chấp nhận, ghi giả định)
- **KHÔNG retry/backoff ngoài fallback** (mỗi model thử tối đa 1 lần per request — deterministic); không streaming/tool-calling (contract v1)
- **KHÔNG làm**: multi-tenant, GPU scheduling, model marketplace, auto-tuning (M5 scope guard PLAN §M5-1)

## 3. Input / Output

- **Input**:
  - `RouteRequest` (pydantic `extra="forbid"`): `policy: str | None = None` (None → policy default), `prompt_tokens: int | None = None`, `completion_tokens: int | None = None` (None → canonical estimate 1000/1000 từ `ModelRouterConfig`)
  - `ModelRegistry` (đã có + capability API mới) — nguồn duy nhất của candidate
  - `RoutingPolicy` từ `settings.models.routing` (config yaml / env `AIOS_MODELS__ROUTING__*`)
  - `ModelRouterConfig` (`max_attempts=None` — mặc định thử TOÀN BỘ chain; là cap an toàn — C2-06; `canonical_prompt_tokens=1000`, `canonical_completion_tokens=1000` — **fallback chỉ khi request không truyền tokens; budget chính xác khi request truyền (TASK-024)** — C1-01) + `HealthConfig` (`cooldown_seconds=30`, `max_failures_before_disable=3`); clock injectable ở `ModelHealth.__init__` + **`ModelRouter.__init__` (now — dùng cho created_at, pattern TASK-024 C3-06 — C2-02)**
- **Output**:
  - `ModelRouter.select(request: RouteRequest) -> RouteDecision` — KHÔNG gọi LLM: `model_name` (hoặc `None` + reason), `policy_used`, `rule_applied`, `candidates_considered` (đã sort), `rejected: list[RejectedCandidate(name, reason)]`, `cost_estimate`, `quality_score`, `latency_class`, `health_snapshot`
  - `ModelRouter.chat(messages, request) -> ChatResponse` — `select()` → `model.chat()`; lỗi model → `ModelHealth.record_failure` → `FallbackResolver` → thử model kế tiếp (≤ `max_attempts`); hết → raise lỗi cuối (bao `ModelError`); thành công → `record_success` + `response.model = model_name` nếu provider để trống; `RouteDecision` cuối lưu ở `router.last_decision` (property, thread-safe) + `fallback_chain: list[str]`
  - KHÔNG tự inject kết quả vào orchestrator/execution (người dùng nhận return value — TASK-026 nối sau)

## 4. Yêu cầu chức năng

### YC-1 — `ModelCapability` contract (pydantic, `extra="forbid"`)
Trong `models/capability.py` (đủ 12 field theo PLAN §8.1):
```python
class ModelCapability(BaseModel):              # extra="forbid"
    model_id: str                               # "openai:gpt-4o-mini" | "ollama:llama3.2" | "mock"
    provider: str                               # "openai" | "ollama" | "mock" (prefix trước ":")
    context_window: int = 0                     # 0 = unknown
    input_cost: float = 0.0                     # USD per 1M tokens
    output_cost: float = 0.0                    # USD per 1M tokens
    latency_class: Literal["fast", "medium", "slow"] = "medium"
    reasoning: bool = False
    coding: bool = False
    vision: bool = False
    tool_calling: bool = False
    structured_output: bool = False
    availability: bool = True                   # flag TĨNH (không gọi is_available — §2 Out)

    @classmethod
    def default(cls, model_id: str, availability: bool = True) -> "ModelCapability":
        # provider = model_id.split(":", 1)[0]; "mock" không có ":" → provider="mock"
        # mọi cost 0, latency "medium", flags False — deterministc cho provider không khai báo
```
- `latency_class` dùng `Literal` — validation tự động (giá trị khác → `ValidationError`); input_cost/output_cost ≥ 0 (field_validator), context_window ≥ 0
- **Test**: đủ 12 field; field thừa → `ValidationError`; `latency_class` sai giá trị → `ValidationError`; cost âm → `ValidationError`; `default()` tạo đúng provider từ model_id (kể cả "mock" không có ":"); `default("ollama:llama3.2")` → provider "ollama", cost 0, flags False.

### YC-2 — ModelRegistry mở rộng (additive — KHÔNG phá API có sẵn)
`models/registry.py` (quyết định: **capability lưu ở registry**, không sửa contract — lý do §5.6):
```python
class ModelRegistry:
    def register(self, name, model, capability: ModelCapability | None = None) -> None
        # additive kwarg; nếu capability given → _capabilities[name] = capability
        # elif getattr(model, "capability", None) callable → capability = model.capability()  # duck-typed
        # else → ModelCapability.default(model_id=name, availability=True)  # C2-05: KHÔNG gọi is_available (Ollama = HTTP)
    def register_capability(self, name: str, capability: ModelCapability) -> None   # overwrite warn (pattern register); caller chịu trách nhiệm đồng bộ model↔capability (C3-05)
    def capability(self, name: str) -> ModelCapability                               # unknown → ModelError
    def capabilities(self) -> dict[str, ModelCapability]                             # sorted keys (deterministic)
```
- `register(name, model)` cũ (2 tham số) hoạt động y hệt — backward compatible; **duck-typed `capability()`** (pattern `KnowledgeSource` TASK-023 — không import ngược, provider future-proof, provider hiện tại chưa implement → rơi vào default)
- **Test**: `register_capability` + `capability` round-trip; `capability` unknown → `ModelError`; `register("x", model, cap)` lưu đúng; `register("x", model)` không cap → default (availability=True — C2-05, KHÔNG gọi is_available); provider fake có method `capability()` → được gọi đúng 1 lần (duck-typed); overwrite warning không crash; `capabilities()` keys sorted.

### YC-3 — Routing Policy (PLAN §8): contract + config + validate
`models/router/contracts.py`:
```python
class PolicyRule(BaseModel):                   # extra="forbid" — policy không biết field → ValidationError (fail-fast)
    max_cost: float | None = None              # USD per request (dùng estimate_cost với canonical tokens khi request không cho)
    max_latency_ms: int | None = None          # so với latency_ms(cap) mapping §YC-4
    min_quality: float | None = None           # 0..1, so với quality_score(cap)
    providers: list[str] | None = None         # filter provider ==

class RoutingPolicy(BaseModel):                # extra="forbid"
    default: str = "balanced"
    policies: dict[str, PolicyRule] = Field(default_factory=dict)
    # "balanced" là tên DÀNH RIÊNG cho policy mặc định — không được định nghĩa lại trong policies (ValidationError)

    @model_validator(mode="after")
    def _validate_default(self):
        # C2-07: fail-fast — default phải ∈ {"balanced"} ∪ policies.keys()
        if self.default != "balanced" and self.default not in self.policies:
            raise ValueError(f"unknown default policy: {self.default!r}")
        if "balanced" in self.policies:
            raise ValueError("'balanced' is reserved")
        return self

    @classmethod
    def from_settings(cls, s: RoutingSettings) -> "RoutingPolicy": ...
    def rule(self, name: str) -> PolicyRule | None   # name == "balanced" → None (không có rule constraint)
```
- Validation: `min_quality` ∈ [0,1], `max_cost` ≥ 0, `max_latency_ms` > 0, `providers` non-empty + không chứa str rỗng; policy rỗng rule (toàn field None) → chấp nhận (== balanced behavior — no filter, rank balanced)
- `config.py` MOD: `RoutingRuleSettings`/`RoutingSettings` mirror (extra="forbid"; fields y hệt PolicyRule); **`ModelsSettings` thêm `extra="forbid"` (C2-04 — typo nested trong block models bị chặn; config.yaml hiện chỉ có `default` — safe)**; `ModelsSettings.routing: RoutingSettings = RoutingSettings()`
- **Test**: `from_settings` parse đúng 4 policy PLAN §8; rule field lạ (vd `max_budget`) → `ValidationError`; `min_quality=1.5` → `ValidationError`; `policies.balanced` → `ValidationError` (tên dành riêng); **`default: "nope"` + policies rỗng → `ValidationError` (C2-07)**; rule toàn None chấp nhận; `rule("balanced")` → None; `rule("nope")` → None (request sai policy name → router raise `RouterError` §YC-9); **typo key trong block `models` → `ValidationError` (C2-04)**.

### YC-4 — CostEstimator (thuần hàm deterministic — `models/router/cost.py`)
- Đơn vị: `input_cost`/`output_cost` = **USD per 1M tokens**; `cost_rate(cap) = input_cost + output_cost`
- `estimate_cost(cap, prompt_tokens, completion_tokens) = (input_cost*pt + output_cost*ct) / 1_000_000`
- `quality_score(cap) = 0.30*reasoning + 0.30*coding + 0.15*vision + 0.15*tool_calling + 0.10*structured_output` → [0,1] (trọng số CỐ ĐỊNH, tổng = 1.0 — nêu rõ, critic phản biện được)
- `latency_ms(cap)` mapping CỐ ĐỊNH: `fast=1000, medium=5000, slow=15000` (ms đại diện per class — ghi giả định §7); `latency_score`: `fast=1.0, medium=0.6, slow=0.3`
- `cost_score(cap) = 1 - min(cost_rate / COST_SCALE, 1.0)` với `COST_SCALE = 0.1` (USD/1M — constant trong cost.py)
- `balanced_score(cap) = 0.5*quality_score + 0.3*latency_score + 0.2*cost_score`
- **Test (số liệu chính xác)**: cap gpt-4o-mini-like (input 0.15, output 0.60, latency fast, reasoning+coding+tool_calling+structured_output=True, vision=False) → `cost_rate=0.75`, `estimate_cost(1000,1000)=0.00075`, `quality_score=0.85` (0.3+0.3+0+0.15+0.1), `latency_ms=1000`, `latency_score=1.0`, `balanced_score` đúng số; cap cost 0.5 → `cost_score=0`; cost âm → ValidationError (YC-1).

### YC-5 — AvailabilityChecker (`models/router/availability.py`)
- `is_available(cap: ModelCapability) -> bool` = `cap.availability` **chỉ đọc flag tĩnh — KHÔNG gọi `model.is_available()`** (lý do §2 Out: Ollama is_available = HTTP call → phá deterministic offline)
- Trạng thái động (lỗi runtime) do `ModelHealth` (§YC-8) — tách 2 nguồn: tuyên bố (static) vs quan sát (dynamic)
- **Test**: cap.availability=False → không chọn được (kể cả model thật available); True → qua; không gọi model.is_available (fake provider đếm số lần gọi — assert 0).

### YC-6 — ModelSelector (filter → rank → pick — `models/router/selector.py`)
- `select(candidates: list[ModelCandidate], rule: PolicyRule | None, request: RouteRequest) -> SelectorResult`  # C3-01: KHÔNG có now param — health ở router
  - `ModelCandidate = (name, capability, model)` — dataclass
  - **Filter** (deterministic, theo rule fields): `max_cost` → `estimate_cost(cap, tokens) ≤ max_cost` (tokens từ request, thiếu → canonical 1000/1000 từ `ModelRouterConfig`); `max_latency_ms` → `latency_ms(cap) ≤ max_latency_ms`; `min_quality` → `quality_score(cap) ≥ min_quality`; `providers` → `cap.provider ∈ providers`; mọi candidate `availability=False` → reject "unavailable"
  - **Rank** theo policy: `cheap` → cost_rate asc; `fast` → latency_ms asc; `quality` → quality_score desc; `local` → (provider filter xong, rank balanced desc); `balanced`/rule=None → balanced_score desc
  - **Pick**: candidate đầu tiên; **tie-break cuối cùng: `name` asc** (deterministic tuyệt đối — kể cả 2 model cùng rank value)
  - `SelectorResult`: `model_name | None`, `rejected: list[RejectedCandidate(name, reason)]` (mọi candidate bị loại + lý do: unavailable/cost/latency/quality/provider/health), `ranking: list[(name, rank_value)]`
- KHÔNG gọi LLM, KHÔNG random, không network — offline deterministic
- **Test (PLAN §23 — định lượng, số liệu sửa theo C1-01)**: đăng ký 3 capability fake (`cheap-m` cost_rate 0.005 / `mid-m` 5.0 / `exp-m` 20.0 → estimate với canonical 1000/1000 = 1e-5 / 0.01 / 0.04) → `cheap` (max_cost 0.01, so sánh `≤`) → `cheap-m` + `mid-m` qua (mid == max → qua), `exp-m` reject "cost", pick `cheap-m`; `fast` (2000) với {fast-m, medium-m} → chỉ fast-m; `quality` (0.9) với {q-0.9 (reasoning+coding+vision+tool_calling), q-0.85} → chỉ q-0.9; `local` (["ollama"]) với {ollama:x, openai:y} → chỉ ollama:x; `balanced` không filter → pick balanced cao nhất; tie-break: 2 model cùng cost → name asc; unavailable bị reject với reason đúng; same input 2 lần → kết quả y hệt.

### YC-7 — FallbackResolver (tuân Policy — `models/router/fallback.py`)
- `next(candidates: list[ModelCandidate], rule: PolicyRule | None, excluded: set[str], now: datetime) -> ModelCandidate | None`
- **`next()` nhận RAW candidates và tự re-filter lại rule mỗi hop** (defense-in-depth thật — C3-02): filter theo rule rồi mới loại `excluded` (failed trong request này) + model bị `ModelHealth` chặn (`can_use == False`) → trả model đầu tiên còn lại; KHÔNG trả model ngoài policy-filtered (INV-013)
- **Test**: chain [a, b, c], excluded {a} → b; b chặn health (cooldown) → c; rule max_cost cấm c (re-filter trên raw) → None (dù c tồn tại — INV-013); tất cả excluded → None.

### YC-8 — ModelHealth (state machine, clock injectable — `models/router/health.py`)
```python
class HealthStatus(str, Enum):
    OK = "ok"; DEGRADED = "degraded"; COOLDOWN = "cooldown"; DISABLED = "disabled"

class ModelHealth:
    def __init__(self, config: HealthConfig, now: Callable[[], datetime] = datetime.now) -> None
    def record_success(self, name) -> None                      # → OK + RESET failures về 0 (C2-03)
    def record_failure(self, name, error: ModelError) -> None   # failures++; transition table (C2-03):
        # failures == 1 → DEGRADED
        # failures == 2 → COOLDOWN (cooldown_until = now + cooldown_seconds)
        # failures >= max_failures_before_disable → DISABLED
    def can_use(self, name, now: datetime | None = None) -> bool  # OK → True; DEGRADED → True; COOLDOWN hết hạn → True (lazy → OK, KHÔNG reset failures — cumulative C2-03); COOLDOWN chưa hết → False; DISABLED → False
    def status(self, name) -> HealthStatus
    def snapshot(self) -> dict[str, HealthStatus]               # keys sorted — deterministic
```
- In-memory, `_lock` (pattern ModelRegistry); unknown model → OK (không crash); `now` injectable → test deterministic; **transition table đủ 4 trạng thái (C2-03)**
- **Test**: OK → 1 failure → DEGRADED (can_use True); 2 failures → COOLDOWN, `can_use` False khi chưa hết hạn, True sau hết hạn (clock cố định + advance, failures KHÔNG reset sau cooldown — cumulative); 3 failures → DISABLED, `can_use` False mãi; `record_success` reset về OK + failures=0; snapshot sorted; unknown → OK; 2 instance độc lập không ảnh hưởng nhau.

### YC-9 — ModelRouter (chỉ điều phối — `models/router/router.py`)
- `__init__(registry: ModelRegistry, policy: RoutingPolicy, config: ModelRouterConfig | None = None, health: ModelHealth | None = None, cost: CostEstimator | None = None, availability: AvailabilityChecker | None = None, selector: ModelSelector | None = None, fallback: FallbackResolver | None = None, now: Callable[[], datetime] = datetime.now(timezone.utc))` — mặc định tự dựng 6 module nhỏ (DI-friendly, override từng cái trong test); **now dùng cho RouteDecision.created_at (C2-02)**
- `select(request: RouteRequest) -> RouteDecision`:
  1. `policy_name = request.policy or policy.default`; name không tồn tại (và ≠ "balanced") → `raise RouterError`
  2. candidates = mọi `registry.list()` có capability (bỏ model không có capability → reject "no-capability"); **router chạy health check TRƯỚC selector: loại model `can_use == False` → reject reason "health" (C2-08)**
  3. `AvailabilityChecker` filter → `ModelSelector.select` → pick
  4. `RouteDecision`: `model_name | None`, `policy_used`, `rule_applied`, `candidates_considered` (ordered — **semantics: candidates sau health check, TRƯỚC selector filter — C2-04 v2**), **`rejected = health_rejected + selector_result.rejected` (C2-08 v1)**, `cost_estimate`, `quality_score`, `latency_class`, `health_snapshot`, `fallback_chain=[]`, `created_at`
- `chat(messages: list[ChatMessage], request: RouteRequest) -> ChatResponse`:
  - `decision = select(request)`; `model_name = None` → `raise RouterError(decision.reason or "no model")`
  - Loop (mỗi model thử 1 lần; `max_attempts=None` → toàn bộ chain — C2-06 v1; nếu set → cap an toàn): `registry.get(name).chat(messages)` → success: `health.record_success`, `response.model = name` nếu `response.model` rỗng, **tạo `last_decision` MỚI (copy decision + fallback_chain + model_name cuối — KHÔNG mutate decision từ select — C3-03 v1)**, return
  - **`fallback.next(all_candidates, rule, excluded)` với `all_candidates = toàn bộ registry candidates có capability (CHƯA filter)` — next tự re-filter rule + health + excluded (C2-02 v2 — defense-in-depth đầy đủ)**
  - `ModelError` (gồm `ModelTimeoutError`/`ModelNotAvailableError`/**`ModelRateLimitError` — C1-02 v1**): `health.record_failure`, thêm vào excluded, `fallback_chain.append(name)`; `fallback.next(...)` → model kế; hết → `raise` lỗi CUỐI cùng (giữ nguyên type nếu `ModelError`, wrap `ModelError(f"all models failed: {chain}")` nếu none)
  - `last_decision: RouteDecision | None` property (thread-safe — lock; phục vụ observability/test)
- KHÔNG import kernel/orchestrator/context (allow-list §5.2); không logic filter/cost trong router.py — chỉ điều phối (arch assert §5.4)
- **Test**: select đủ policy (tham số hóa); `RouterError` khi policy name sai; chat với fake provider raise `ModelTimeoutError` → fallback đúng chain [a→b], `last_decision.fallback_chain == ["a", "b"]`; **fake provider raise `ModelRateLimitError` → fallback tiếp tục đúng chain (C2-05 v2)**; cả 2 fail → raise; thành công lần 2 → `response.model == "b"`; `max_attempts=1` → không fallback; select KHÔNG gọi chat (mock.calls == 0 — offline).

### YC-10 — Wiring (RuntimeKernel.create + config.yaml, additive)
- `config.yaml` MOD:
```yaml
models:
  default: "mock"
  routing:
    default: "balanced"
    policies:
      cheap:   { max_cost: 0.01 }
      fast:    { max_latency_ms: 2000 }
      quality: { min_quality: 0.9 }
      local:   { providers: ["ollama"] }
```
- `RuntimeKernel.create` (sau block model registry — TASK-006; block additive):
```python
# Model router (TASK-025): policy-driven selection + fallback.
from ..models import ModelCapability  # (hoặc from ..models.capability import ModelCapability)
from ..models.router import ModelRouter, ModelRouterConfig, RoutingPolicy
model_registry.register_capability(
    "mock", ModelCapability.default(model_id="mock", availability=True),
)
router = ModelRouter(
    registry=model_registry,
    policy=RoutingPolicy.from_settings(settings.models.routing),
    config=ModelRouterConfig(),
)
container.register_instance(ModelRouter, router)
```
- KHÔNG sửa service đã đăng ký; `RuntimeKernel.create()` chạy được với Settings default (routing mặc định balanced); env override: `AIOS_MODELS__ROUTING__DEFAULT`, `AIOS_MODELS__ROUTING__POLICIES__CHEAP__MAX_COST`... **— test_config phải verify: scalar (`DEFAULT=cheap`) + dict nested (`POLICIES__CHEAP__MAX_COST=0.05`); nếu pydantic-settings không hỗ trợ dict nested qua env → ghi chú config.yaml là nguồn chính, env chỉ scalar (C2-03 v2)**
- **Test** (integration): `RuntimeKernel.create().container.resolve(ModelRouter)` trả instance; `select(RouteRequest(policy="balanced"))` với registry chỉ có mock → `model_name == "mock"`, không gọi chat (mock.calls == 0); `Settings` parse đúng config.yaml block (test_config.py pattern — policy cheap → `max_cost=0.01`).

### YC-11 — Integration ModelRouter ↔ ModelRegistry ↔ providers (end-to-end)
- Đăng ký qua `ModelRegistry`: mock thật + 2 fake provider (subclass `ModelContract` trong test, `chat` raise `ModelTimeoutError` / trả response) + capability tương ứng → `router.chat` fallback end-to-end
- **Test**: registry 3 model (a: timeout, b: timeout, c: ok) + capability (c cheap nhất) → `chat(request policy="cheap")` → chain ["a","b"]→"c" đúng thứ tự, response content từ c; health sau đó chặn a/b (cooldown) → lần 2 chain ngắn hơn; policy `fast` → chọn khác `cheap` → `RouteDecision.policy_used` đúng.

## 5. Yêu cầu kiến trúc

### 5.1 INV-013 — Model Routing Policy (behavioral + AST enforcement)
Bản chất: *"Model selection phải qua Routing Policy"* — invariant HÀNH VI + cấu trúc:

1. **Behavioral (test functional — `test_inv013_policy_followed` trong `test_model_router.py`)**:
   - Tham số hóa theo PLAN §23: cheap policy → model rẻ nhất; quality policy → model quality cao nhất; fast → chỉ latency ≤ ngưỡng; timeout → fallback đúng thứ tự; offline: `select()` với mock-only registry → chọn được, `mock.calls == 0`
   - Fallback tuân policy: rule cấm model X (cost/latency/quality/provider) → X KHÔNG BAO GIỜ được chọn kể cả khi là model kế tiếp duy nhất (FallbackResolver re-filter §YC-7)
2. **AST hỗ trợ — `test_inv013_selection_via_router_only`**: model selection phải qua router; ai cũng có thể dùng `ModelRegistry.get/default` trực tiếp để "chọn" model → chặn: **mọi module ngoài `models/` import `ModelRegistry` / `aios_core.models.registry`** → phải nằm trong danh sách exemption (composition root — nơi ASSEMBLE, không phải select):
   - Exemption CHÍNH XÁC (C2-01 v1 — đã grep thật, không có doctor): `aios_core.kernel.runtime_kernel` (wiring), `aios_core.api.wiring` (orchestrator mặc định offline), **`aios_core` (root __init__ — re-export composition root, import models trần để re-export — C2-01 v2)**
   - Scan: `collect_imports` toàn `aios_core/` (trừ `models/**` + 3 exemption) — import chạm `aios_core.models.registry` HOẶC `aios_core.models` trần (module_imports match 2 chiều — C2-01 v1) hoặc name `ModelRegistry` → fail. **Lưu ý AST đếm MỌI Import node kể cả TYPE_CHECKING (bài học TASK-023 C2-01)** — comment rõ trong test
   - Hệ quả tự động: planner allow-list (INV-005 rule B, chỉ {models.base, models.errors}) đã chặn `planner → models.router`; rule A chặn `orchestrator → models` → **GHI NHẬN cho TASK-026**: pipeline gọi router phải inject instance (pattern `Orchestrator.model` untyped) hoặc amend rule A — KHÔNG xử trong task này
3. **Test chi tiết**: 3 test arch mới (§5.2/§5.4) + `test_inv013_policy_followed` behavioral.

### 5.2 Allow-list import `models/router/` (test mới `test_inv_router_import_allowlist` — pattern `test_inv_context_import_allowlist`)
- **aios_core allowed**: `aios_core.models.base` (ChatMessage/ChatResponse/ModelContract), `aios_core.models.errors` (ModelError + RouterError), `aios_core.models.registry` (ModelRegistry), `aios_core.models.capability` (ModelCapability) + intra-package `aios_core.models.router.*` (loại trừ trong scan)
- **CẤM**: `aios_core.kernel.*` (KHÔNG import PolicyService — routing policy độc lập), `aios_core.orchestrator`, `aios_core.context`, `aios_core.memory`, `aios_core.policy` (không tồn tại — phòng future), `aios_core.contracts` (INV-006 — contracts domain-local) — **kể cả TYPE_CHECKING** (C2-01)
- **external allowed**: `pydantic`, `typing`, `datetime`, `enum`, `abc`, `dataclasses`, **`threading`** (R2-1 — health/router dùng RLock pattern registry)
- Scan toàn dir `models/router/*.py` qua `collect_imports`, loại trừ `startswith("aios_core.models.router")`
- **models/__init__.py thứ tự import (C3-04)**: base → errors → capability → registry → router (tránh cycle); ghi chú chi phí import
- **Cycle check**: `registry → capability` (1 chiều, capability leaf); `router → registry`; `models/__init__ → registry + router` — không cycle mới; `models/capability.py` không import gì từ aios_core (leaf)

### 5.3 Deterministic first
- Routing/filter/rank/fallback/health đều thuần hàm hoặc state machine có clock injectable: không LLM, không random, không network (không gọi `model.is_available()` — §YC-5)
- Tie-break đầy đủ: rank value → `name` asc; `capabilities()`/`snapshot()` keys sorted; cùng input + cùng clock → `RouteDecision.model_dump()` y hệt 2 lần chạy (test)
- `select()` KHÔNG gọi `model.chat` (assert `calls == 0`) — offline deterministic (PLAN §23)

### 5.4 No God Object (PLAN §10 — ModelRouter chỉ điều phối)
- Dependency DAG (mỗi module nhỏ 1 trách nhiệm, chiều đi xuống):
```
capability.py  contracts.py        (leaf — không import aios khác)
   ↑               ↑
registry.py ──→ policy.py ←── contracts
   │               │
   ├────────────→ availability.py → capability
   ├──→ cost.py ─────────────────→ capability
   ├──→ health.py → contracts (HealthConfig/HealthStatus) + stdlib
   │        ↑
selector.py → {policy, cost, availability, capability}     # filter+rank+pick
fallback.py → {policy, health, capability}                 # re-filter + health
router.py   → {selector, fallback, health, registry, base, errors}   # CHỈ điều phối
```
- **Arch assert `test_inv013_no_god_object`**: (a) `router.py` import ĐỦ 6 module (ModelSelector, RoutingPolicy, CostEstimator, AvailabilityChecker, FallbackResolver, ModelHealth — qua `collect_imports`); (b) `selector.py`/`fallback.py` KHÔNG import `router` (không đảo chiều); (c) `cost.py`/`availability.py`/`health.py`/`policy.py` KHÔNG import `selector`/`fallback`/`router`; (d) `router.py` không chứa `estimate_cost`/`quality_score`/`latency_ms`/`balanced_score` (logic cost không nằm trong router — scan source text)
- **GHI NHẬN**: `ContextOptimizer` (TASK-024) L3 compression cần model/tokenizer — TASK-025 cung cấp `ModelCapability.context_window` + cost; KHÔNG nối trong task này (harness M6)

### 5.5 Additive only
- `git diff` sau implement: `mock.py`, `openai_provider.py`, `ollama_provider.py`, `models/base.py`, `kernel/services/*`, `orchestrator/*`, `context/*`, `memory/*`, `contracts/` **không đổi**
- MOD (chỉ THÊM field/method/kwarg, không đổi hành vi cũ): `models/registry.py` (capability API), `models/errors.py` (thêm class), `models/__init__.py` (re-export), `config.py` (routing settings), `config.yaml` (routing block), `runtime_kernel.py` (wiring block), `tests/*` (additive test)
- `register(name, model)` 2 tham số cũ hoạt động y hệt (test cũ pass không sửa)

### 5.6 Vị trí package (quyết định mở — cho critic phản biện)
- **Đề xuất: subpackage `aios_core/models/router/` (8 file) + `models/capability.py`** — KHÔNG đặt router.py đơn file, KHÔNG package ngoài models/:
  1. Cùng domain `models/` (gần ModelRegistry — nguồn candidate duy nhất); PLAN §10 cần 6 module + contracts → đơn file `router.py` (~400 dòng) = God Object ngay tại chỗ — subpackage bắt buộc
  2. Pattern M5 đồng nhất: mỗi năng lực 1 package riêng (`memory/` 023, `context/` 024) → `models/router/` 025 — allow-list riêng, contracts domain-local (INV-006)
  3. Không đảo chiều phụ thuộc: `models/ → registry` là dependency tự nhiên; đặt ngoài (vd `routing/`) tạo import ngược `routing → models.registry` + phá scan `models/` hiện có
  4. INV-005/INV-010 KHÔNG bị ảnh hưởng: planner allow-list ({base, errors}) tự chặn `planner → router`; orchestrator rule A giữ nguyên; `api/wiring.py` không đổi (composition root)
- **Phương án thay thế**: (a) `models/router.py` đơn file — đơn giản nhưng vi phạm tinh thần PLAN §10 (6 module riêng); (b) package mới `aios_core/routing/` — tách domain models, cần import `models.registry` (chiều ngược), allow-list phức tạp; (c) capability lưu trong `ModelContract` (method `capability()`) — phá additive (đổi ABC + 3 provider) — **loại**
- Critic được phép phản biện chọn phương án khác; nếu đổi → cập nhật allow-list + exemption INV-013 tương ứng

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — `ModelCapability` đủ 12 field PLAN §8.1 (`extra="forbid"`); `PolicyRule`/`RoutingPolicy`/`RouteRequest`/`RouteDecision`/`HealthStatus`/`HealthConfig`/`ModelRouterConfig` pydantic `extra="forbid"`; thừa field / `latency_class` sai / cost âm → `ValidationError`; `RoutingSettings` config mirror (YC-1, YC-3)
- [ ] **AC2**: Registry capability API — `register_capability`/`capability`/`capabilities`/`register(capability=...)`; unknown → `ModelError`; duck-typed `capability()` provider gọi đúng; `register(name, model)` cũ không đổi hành vi (test cũ pass) (YC-2)
- [ ] **AC3**: Routing Policy — parse yaml 4 policy PLAN §8; field lạ → `ValidationError` (fail-fast — trả lời câu hỏi "policy không biết field → lỗi?": **CÓ**); `min_quality` range; tên `balanced` dành riêng; rule toàn None chấp nhận (YC-3)
- [ ] **AC4**: CostEstimator — công thức exact (gpt-4o-mini-like: cost_rate 0.75, canonical est 0.00075, quality 0.85, latency 1000ms); `balanced_score` đúng số; `COST_SCALE` constant (YC-4)
- [ ] **AC5**: Selector — cheap → model rẻ nhất; fast → chỉ latency ≤ 2000ms; quality → chỉ ≥ 0.9 rank desc; local → chỉ ollama; balanced → top balanced; tie-break `name` asc; unavailable reject đúng reason; 2 lần chạy y hệt (YC-6, PLAN §23)
- [ ] **AC6**: Fallback — timeout → model kế đúng thứ tự; health-block bỏ qua; **re-filter policy (INV-013: model bị rule cấm không bao giờ được chọn)**; tất cả excluded → None (YC-7)
- [ ] **AC7**: ModelHealth — OK→COOLDOWN→DISABLED; clock injectable (fixed + advance); hết hạn tự cho dùng; `record_success` reset; snapshot sorted (YC-8)
- [ ] **AC8**: **INV-013 behavioral** — `test_inv013_policy_followed`: cheap→cheapest, quality→best, timeout→fallback chain đúng; **offline: `select()` mock-only → chọn được + `mock.calls == 0`** (YC-9, YC-11, PLAN §23)
- [ ] **AC9**: Router — `select` trả `RouteDecision` đầy đủ (rejected/chain/cost/quality/latency/health snapshot); policy name sai → `RouterError`; `chat` fallback end-to-end (fake providers) → `response.model` đúng model cuối; hết chain → raise lỗi cuối; `max_attempts` tôn trọng; `last_decision` thread-safe (YC-9)
- [ ] **AC10**: Wiring — `RuntimeKernel.create()` resolve `ModelRouter`; config.yaml `models.routing` parse đúng (default balanced + 4 policies); Settings default chạy được; env override `AIOS_MODELS__ROUTING__*`; full pytest pass (baseline 896 + test mới ≥ ~45), coverage ≥ 95% mục tiêu (hard ≥ 80%) (YC-10)
- [ ] **AC11**: Architecture — `test_inv_router_import_allowlist` pass (router/ chỉ import base/errors/registry/capability/intra; CẤM kernel/orchestrator/context/memory kể cả TYPE_CHECKING); `test_inv013_no_god_object` pass (router import đủ 6 module; không logic cost trong router.py; không đảo chiều import); `test_inv013_selection_via_router_only` pass (ngoài models/ + **3 exemption** {runtime_kernel, api.wiring, root aios_core}, không ai import `ModelRegistry`); git diff verify additive only (§5.1, §5.2, §5.4, §5.5)

## 7. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Chồng lấn với ModelRegistry (TASK-006) — "tồn tại" vs "chọn" | Ranh giới cứng: registry = đăng ký/lookup/capability (trả lời "có gì"); router = chọn theo policy (trả lời "dùng gì"); registry KHÔNG có logic filter/rank; router KHÔNG sửa registry |
| `latency_class` là enum 3 mức nhưng policy dùng `max_latency_ms` — mapping 1000/5000/15000 là ước lượng | Mapping CỐ ĐỊNH, nêu rõ trong spec (constant `LATENCY_MS`); deterministic + test exact; critic phản biện được; khi có đo lường thật (M6 harness) thay hằng số không phá API |
| `quality_score` trọng số cờ khả năng là heuristic | Trọng số CỐ ĐỊNH + tổng 1.0 + test exact số; PLAN không định nghĩa quality metric → spec chọn công thức tường minh deterministic; critic phản biện được |
| Cost ước lượng (canonical 1000/1000) sai lệch request thật | Request có thể truyền `prompt_tokens`/`completion_tokens` chính xác (ContextOptimizer TASK-024 cung cấp token count — ghi nhận tích hợp sau); canonical chỉ là fallback khi không biết |
| `ModelHealth` in-memory mất khi restart | Chấp nhận cho v1 (routing policy deterministic vẫn đúng); persistence + metrics gắn observability task sau (M5 DoD "model fallback") |
| INV-013 chặn `ModelRegistry` ngoài exemption quá cứng (TASK-026 cần dùng router qua pipeline) | Exemption danh sách tường minh (3 composition root); TASK-026 inject instance (pattern `Orchestrator.model` untyped — rule A không phá); ghi nhận rõ trong spec để orchestrator amend nếu cần |
| Provider không khai báo capability → default sai (cost 0 = "rẻ nhất" gây chọn nhầm) | Default chỉ áp dụng khi KHÔNG có capability; RuntimeKernel đăng ký capability tường minh cho mock; provider thật (M6) BẮT BUỘC đăng ký capability khi dùng router — test phủ (candidate thiếu capability → reject "no-capability", không silent default trong router) |
| AST đếm cả TYPE_CHECKING (bài học TASK-023 C2-01) — router cần type hint nội bộ | Dùng import runtime bình thường cho dependency thật (không TYPE_CHECKING); comment rõ trong test allow-list |
| Fallback "tuân policy" quá phức tạp (re-filter mỗi hop) | Re-filter là hàm thuần rẻ (filter theo metadata, không LLM); spec chốt defense-in-depth — INV-013 là invariant, đáng trả giá |

**Giả định**:
- Cost đơn vị USD per 1M tokens (chuẩn ngành OpenAI/Anthropic); `max_cost` là budget PER REQUEST (so với `estimate_cost`), không phải per token
- `ModelCapability.availability` là flag tĩnh khai báo; trạng thái động chỉ qua `ModelHealth` (failures quan sát được) — không gọi `model.is_available()` trong routing (network I/O phá deterministic — Ollama)
- Router v1 chọn model DUY NHẤT cho cả request (không phân model per-step trong 1 request); per-step routing là TASK-026/027 khi có Execution Graph
- `api/wiring.py` (orchestrator mặc định offline mock) và `runtime_kernel.py` là composition root — dùng `ModelRegistry` trực tiếp để ASSEMBLE, không phải selection per-request (exemption INV-013)
- `models/__init__.py` re-export router KHÔNG phá INV-005 rule B (planner không import `aios_core.models` trần — test rule B giữ nguyên)
- Không có model nào đăng ký capability trong baseline wiring ngoài mock → `select("balanced")` với registry chỉ mock trả "mock" (default capability: cost 0, latency medium, quality 0) — deterministic

## 8. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/models/capability.py` | NEW | `ModelCapability` (12 field PLAN §8.1, pydantic `extra="forbid"`) + `default()` factory (leaf — không import aios khác) |
| `backend/src/aios_core/models/router/contracts.py` | NEW | `PolicyRule` + `RoutingPolicy` + `RouteRequest` + `RouteDecision` + `RejectedCandidate` + `HealthStatus` + `HealthConfig` + `ModelRouterConfig` + `ModelCandidate` (dataclass) |
| `backend/src/aios_core/models/router/policy.py` | NEW | `RoutingPolicy` (parse/validate từ `RoutingSettings`; `rule(name)`) |
| `backend/src/aios_core/models/router/cost.py` | NEW | `CostEstimator` (thuần hàm: `cost_rate`/`estimate_cost`/`quality_score`/`latency_ms`/`latency_score`/`cost_score`/`balanced_score` + constants) |
| `backend/src/aios_core/models/router/availability.py` | NEW | `AvailabilityChecker.is_available(cap)` — chỉ flag tĩnh |
| `backend/src/aios_core/models/router/health.py` | NEW | `ModelHealth` state machine (OK/DEGRADED/COOLDOWN/DISABLED, clock injectable, snapshot) |
| `backend/src/aios_core/models/router/selector.py` | NEW | `ModelSelector.select` (filter → rank → pick, tie-break name asc, rejected reasons) |
| `backend/src/aios_core/models/router/fallback.py` | NEW | `FallbackResolver.next` (re-filter policy + health + excluded — INV-013) |
| `backend/src/aios_core/models/router/router.py` | NEW | `ModelRouter` (chỉ điều phối: `select` + `chat` fallback loop + `last_decision`) |
| `backend/src/aios_core/models/router/__init__.py` | NEW | Re-export public API |
| `backend/src/aios_core/models/registry.py` | MOD | `register_capability`/`capability`/`capabilities` + `register(capability=None)` + duck-typed resolution (additive) |
| `backend/src/aios_core/models/errors.py` | MOD | Thêm `RouterError(ModelError)` (additive) |
| `backend/src/aios_core/models/__init__.py` | MOD | Re-export `ModelCapability`/`ModelRouter`/`RoutingPolicy`/`RouteRequest`/`RouteDecision` (additive) |
| `backend/src/aios_core/config.py` | MOD | `RoutingRuleSettings` + `RoutingSettings` + `ModelsSettings.routing` (additive) |
| `backend/config.yaml` | MOD | Block `models.routing` (PLAN §8) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring `register_capability("mock")` + `register_instance(ModelRouter)` (additive) |
| `backend/tests/test_model_router.py` | NEW | Unit (contracts/policy/cost/selector/fallback/health/deterministic) + INV-013 behavioral + integration (registry ↔ router ↔ RuntimeKernel) |
| `backend/tests/test_architecture.py` | MOD | `test_inv_router_import_allowlist` + `test_inv013_no_god_object` + `test_inv013_selection_via_router_only` |
| `backend/tests/test_runtime_kernel.py` | MOD | `test_model_router_wired` (additive, pattern `test_context_optimizer_wired`) |
| `backend/tests/test_models.py` | MOD | Registry capability API tests (additive) |
| `aios/progress/tasks/TASK-025/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 9. Ghi chú thiết kế (cho critic phản biện)

- **Capability lưu ở đâu — registry vs contract**: spec chốt **registry** (thêm API additive, provider không đổi). Phương án khác: mở rộng `ModelContract` thêm method `capability()` (phá additive — đổi ABC + 3 provider) — critic cân nhắc: có chấp nhận phá ABC vì "capability là bản chất model" không? Spec loại vì Out-of-scope "không sửa provider"
- **`model.is_available()` không dùng trong routing**: quyết định mạnh — deterministic-first thắng độ chính xác availability; Ollama `is_available` = HTTP call. Critic phản biện: có nên dùng `is_available()` với injectable checker (test fake) + cache TTL? Spec chọn KHÔNG (đơn giản, offline tuyệt đối)
- **quality_score trọng số cố định** (0.3/0.3/0.15/0.15/0.10) — heuristic tường minh; phương án khác: bỏ quality, chỉ filter flag `require` (thêm field policy)? Spec giữ trọng số vì PLAN §8 có `min_quality` — critic cân nhắc đơn giản hơn
- **Fallback chain = chính danh sách policy-filtered** (không danh sách riêng) — tuân Policy tự nhiên (INV-013); phương án khác: fallback list riêng trong policy (explicit `fallback: [a, b]`) — spec loại (PLAN §9 mô tả chuỗi do lỗi runtime, không phải config)
- **`last_decision` mutable state trong router** — cần cho observability/test (M5 DoD "model selected/fallback"); phương án khác: `chat` trả `(ChatResponse, RouteDecision)` tuple — đổi kiểu trả về, phá call-site tương lai; spec chọn property + lock
- **`max_attempts=3` mặc định** nhưng chain có thể dài hơn (5 model) — spec: mỗi model thử tối đa 1 lần, tổng ≤ max_attempts (cắt chain); critic cân nhắc: nên mặc định = len(chain)?
- **Registry `register()` duck-typed `capability()`** — thêm khái niệm nhưng future-proof (provider M6 implement được mà không đổi registry); phương án khác: bỏ duck-typed, chỉ explicit + default
- **Exemption INV-013 gồm `observability.doctor`** — đọc `get_all()` cho healthcheck, không phải selection; critic kiểm tra lại danh sách exemption có sót module nào dùng `ModelRegistry` không
- **Router không emit event** — ghi nhận: M5 DoD observability (model selected/fallback) qua `RouteDecision`/`last_decision`; gắn metrics + event ở task sau (pattern TASK-024 Out tương tự)
