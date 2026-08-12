# TASK-006 — M1/P1a: Model Contract + Providers (Mock/OpenAI/Ollama)

## Mục tiêu
Xây Model abstraction theo Contract-First: `ModelContract` (interface chuẩn cho mọi LLM provider), 3 providers (Mock — offline-first cho test/simulation; OpenAI; Ollama), `ModelRegistry` (đăng ký/tra cứu model theo tên). Đây là nền cho General/Coder/Doctor agents (M2) + Simulation Mode.

## Phạm vi
- **In** (thuộc `backend/src/aios_core/models/`):
  1. `base.py` — `ChatMessage` (role: **Literal["system","user","assistant"]**, content), `ChatResponse` (content, model, usage: dict **chứa prompt_tokens/completion_tokens int ≥ 0 — CHATRESPONSE LÀ ĐIỂM ENFORCE DUY NHẤT (validator fill thiếu = 0, âm → ValidationError)**, finish_reason), `ModelContract` ABC: **template-method — base `chat()` validate input (messages rỗng → ValueError; temperature ∈ [0,2]; max_tokens None hoặc > 0) rồi gọi `_chat()` abstract** (mọi provider đều được validate); `name` property, `is_available() -> bool`, `metadata() -> AiOSMetadata` (id/name/version convention: `id="models.<name>"`); KHÔNG có stream param v1; docstring breaking-change policy
  2. `mock.py` — `MockModel(ModelContract)`: `responses: list[str] | None` (1 phần tử = fixed, nhiều = sequence), `echo: bool = False` (**echo ưu tiên khi set cùng responses**), `raise_error: Exception | None`, `loop: bool = False`; **hết responses (kể cả responses=[]) → raise ModelError("MockModel responses exhausted")** (loop=True → lặp); `calls` đếm; **usage = {"prompt_tokens": n, "completion_tokens": n} (n = len(output)//4)**; is_available=True luôn
  3. `openai_provider.py` — `OpenAIModel(ModelContract)`: `__init__(model="gpt-4o-mini", api_key: str | None = None, base_url: str | None = None, client: Any | None = None, timeout: float = 60.0)` — client = injection seam; **chat(): client is not None → dùng trực tiếp (bypass is_available); ngược lại: not is_available() → ModelNotAvailableError → lazy-build client**; `is_available()` = `_is_openai_installed()` (importlib.util.find_spec — **patch target `aios_core.models.openai_provider._is_openai_installed`**) AND (api_key OR base_url); static check, ưu tiên param > env
  4. `ollama_provider.py` — `OllamaModel(ModelContract)`: `__init__(model="llama3.2", base_url="http://localhost:11434", timeout: float = 30.0)`; POST /api/chat (stream:false) — **gọi qua `import urllib.request; urllib.request.urlopen(...)` (patch target `aios_core.models.ollama_provider.urlopen`)**; mọi HTTP call dùng timeout; **map lỗi: URLError(reason=ConnectionRefusedError/socket.gaierror) → ModelNotAvailableError; socket.timeout/URLError(timeout) → ModelTimeoutError; HTTPError khác → ModelError**; is_available() = GET /api/tags 200 (dùng self.timeout); mapping: content ← message.content; prompt_tokens ← prompt_eval_count; completion_tokens ← eval_count (thiếu → 0); finish_reason ← done_reason (thiếu → "stop"); không JSON/thiếu message → ModelError rõ
  5. `registry.py` — `ModelRegistry`: **class thuần (không singleton hardcode)** + helper `default_registry()` lazy; `register(name, model)` (duplicate → overwrite + warning + lock), `get(name)` (unknown → ModelError), `list() -> list[str]`, `default(name=None)` (None → settings default; unknown → ModelError); **RuntimeKernel.create() thêm register_instance(ModelRegistry, ...) + pre-register MockModel "mock"**
  6. `errors.py` — `ModelError`, `ModelNotAvailableError`, `ModelTimeoutError` — **hierarchy: 2 cái sau ⊂ ModelError**
  7. `__init__.py` exports + `settings.models.default: str = "mock"` (ModelsSettings + config.yaml `models:`)
  8. Tests: test_models (contract validate, mock, registry, errors) + test import + config
- **Out (không làm)**: streaming (v1 non-stream — interface để trống cho M2), embeddings (TASK-007), tool calling (M2), auto-retry/timeout policy (Runtime Execution đã có), local model (Ollama là đủ cho local)

## Yêu cầu chi tiết
1. **ChatMessage**: role Literal + content str — pydantic
2. **ChatResponse**: pydantic; validator usage: fill thiếu key = 0, âm → ValidationError; finish_reason default "stop"
3. **ModelContract**: template-method — `chat()` public validate input → `_chat()` abstract; provider không cần tự validate
4. **MockModel**: như Phạm vi #2 (echo ưu tiên, exhausted raise, loop, usage n = len//4)
5. **OpenAIModel**: như Phạm vi #3 (client seam + thứ tự check: client explicit bypass is_available; lazy-build; is_available = installed AND (key OR base_url))
6. **OllamaModel**: như Phạm vi #4 (timeout 30s, map lỗi 3 nhánh, patch target urlopen module-ref)
7. **ModelRegistry**: class thuần; register/get/list/default; duplicate → overwrite + warning + lock; **KHÔNG auto-register mock** (chỉ RuntimeKernel pre-register); test dùng registry instance mới
8. **RuntimeKernel.create()**: sửa `kernel/runtime_kernel.py` — thêm `register_instance(ModelRegistry, ModelRegistry(default_name=settings.models.default))` + pre-register MockModel "mock" (gom logic init registry 1 chỗ)
9. Settings: `ModelsSettings(default: str = "mock")` + config.yaml `models:` (pattern Settings từ TASK-002); mọi test offline; coverage ≥ 80%

## Input / Output
- Input: TASK-002 (metadata AiOSMetadata, Settings pattern), TASK-003 (semver)
- Output: models/ package + tests + exports + RuntimeKernel update + commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: ChatMessage role ∈ {system,user,assistant} (role lạ → ValidationError); usage chứa prompt_tokens/completion_tokens int ≥ 0 (default 0 khi thiếu) (có test)
- [ ] AC2: MockModel: echo trả content cuối; responses fixed/sequence; **hết responses → ModelError (loop=False); loop=True → lặp**; raise_error → raise đúng; **chat input validate: messages rỗng/temperature ngoài [0,2]/max_tokens ≤ 0 → ValueError** (có test)
- [ ] AC3: MockModel.calls đếm; is_available=True; metadata() version semver (có test)
- [ ] AC4: ModelRegistry: register/get/list; get unknown → ModelError; default → mock; duplicate → overwrite; thread-safe (có test)
- [ ] AC5: OpenAIModel: `_is_openai_installed()` monkeypatch False (hoặc không key + không base_url) → is_available=False; chat → ModelNotAvailableError (có test — deterministic)
- [ ] AC6: OpenAIModel với **fake client** (seam): chat → ChatResponse đúng content/usage/finish_reason (có test)
- [ ] AC7: Ollama is_available: monkeypatch urlopen raise ConnectionRefusedError → False nhanh (deterministic, không đụng network) (có test)
- [ ] AC8: Ollama mapping: fake urlopen response (prompt_eval_count/eval_count/done_reason) → ChatResponse đúng (có test)
- [ ] AC9: Ollama: HTTP lỗi → ModelError; **urlopen raise socket.timeout → chat() raise ModelTimeoutError** (có test)
- [ ] AC10: Settings.models.default load từ config.yaml (thêm `models:` vào file thật) + default "mock" (test_config)
- [ ] AC11: pytest pass + coverage ≥ 80%; test_import: `from aios_core.models import ModelContract, MockModel, ModelRegistry, ModelError, ModelNotAvailableError, ModelTimeoutError` pass
- [ ] AC12: Mọi test offline + không sleep lâu — git sạch
- [ ] AC13: RuntimeKernel.create: container.has(ModelRegistry) + resolve → default "mock" sẵn sàng (có test)

## Phụ thuộc
- TASK-002/003 (metadata, semver), TASK-004/005 (Settings pattern)
- Không cài openai/ollama deps (optional — lazy import)

## Rủi ro
- R1: openai không cài → test unavailable path ổn; mapping test dùng stub class (không cần cài)
- R2: Ollama HTTP test — monkeypatch urllib.request.urlopen; timeout test dùng fake raise socket.timeout
- R3: Stream API đổi (M2) → interface để trống stream param, không implement v1
