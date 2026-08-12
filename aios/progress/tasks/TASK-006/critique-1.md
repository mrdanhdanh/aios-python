# Critique vòng 1 — TASK-006

## Đánh giá chung
Khung tốt, out-list chặn creep đúng. Nhưng 3 P1 (Registry không DI-safe; OpenAI thiếu injection seam; Ollama chat không timeout) + 7 P2 + 9 P3. **Sẵn sàng: 2.5/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — ModelRegistry không DI-safe, không wire RuntimeKernel
- **Resolution**: ModelRegistry class thuần + `register_instance(ModelRegistry, ModelRegistry(default_name=settings.models.default))` trong `RuntimeKernel.create()` + pre-register MockModel "mock"; helper `default_registry()` lazy (cho CLI/test) nhưng AC test qua Container.

### P1-2 — OpenAIModel thiếu injection seam
- **Resolution**: `__init__(..., client: Any | None = None)` — test truyền fake client; `client=None` → build lazy trong chat() sau is_available; `is_available()` dùng `_is_openai_installed()` (importlib.util.find_spec) — test monkeypatch hàm này.

### P1-3 — Ollama chat() không timeout
- **Resolution**: `OllamaModel.__init__(..., timeout: float = 30.0)` (và OpenAI client timeout tương tự); mọi HTTP call dùng timeout; socket.timeout/URLError(timeout) → ModelTimeoutError; thêm AC: fake urlopen raise socket.timeout → chat() raise ModelTimeoutError.

### P2 — (đặc tả)
1. **MockModel hết responses → raise ModelError("MockModel responses exhausted")** + option `loop: bool = False`; thống nhất: responses 1 phần tử = fixed, nhiều = sequence; sửa AC2 test cả 2 nhánh
2. **role: Literal["system", "user", "assistant"]** (AC1 đổi)
3. **Validate chat input ở base**: messages rỗng → ValueError; temperature ∈ [0.0, 2.0]; max_tokens None hoặc > 0 (≤0 → ValueError); AC tương ứng
4. **Mapping Ollama**: content ← message.content; prompt_tokens ← prompt_eval_count; completion_tokens ← eval_count (thiếu → 0); finish_reason ← done_reason (thiếu → "stop"); không JSON/thiếu message → ModelError rõ
5. **usage validate**: phải chứa prompt_tokens/completion_tokens int ≥ 0 (default 0 khi thiếu)
6. **is_available OpenAI**: installed AND (api_key OR base_url); static check; ưu tiên param > env
7. **AC7 deterministic**: monkeypatch urlopen raise ConnectionRefusedError → False (không đụng network)

### P3 — (áp)
1. V1 KHÔNG có stream param trong signature (M2 thêm = bump contract version)
2. `list() -> list[str]` (tên đã đăng ký)
3. Duplicate register → overwrite + warning + lock (pattern Container)
4. `default(name=None)` → settings default; tên không đăng ký → ModelError; RuntimeKernel pre-register mock
5. Thêm AC metadata() cho OpenAI/Ollama (version semver); docstring breaking-change policy
6. Error hierarchy: ModelNotAvailableError/ModelTimeoutError ⊂ ModelError
7. AC10 cập nhật cả `backend/config.yaml` (thêm `models:`)
8. Ollama is_available timeout cấu hình ở constructor (gộp P1-3)

## Kết luận
- [x] **Resolve toàn bộ (3 P1 + 7 P2 + 9 P3)** — cập nhật spec, chuyển critique vòng 2.
