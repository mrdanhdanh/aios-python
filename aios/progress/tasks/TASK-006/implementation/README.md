# TASK-006 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Model contract | `backend/src/aios_core/models/base.py` (template-method chat) |
| Errors | `models/errors.py` (hierarchy ⊂ ModelError) |
| Mock | `models/mock.py` (echo/responses/loop/exhausted/usage) |
| OpenAI | `models/openai_provider.py` (client seam, lazy build) |
| Ollama | `models/ollama_provider.py` (urllib module-ref, timeout, 3-nhánh error) |
| Registry | `models/registry.py` (lock, overwrite, default_name) |
| Wiring | `runtime_kernel.py` (+ModelRegistry, pre-register mock), `config.py` (+ModelsSettings), `config.yaml` |
| Tests | `tests/test_models.py` (26) + test_config + test_import + test_runtime_kernel |

## Quyết định kỹ thuật (qua critique ×2 + review)
- **Template-method**: base `chat()` validate (messages/temperature/max_tokens) → `_chat()` abstract — mọi provider validate đồng nhất
- **ChatResponse là điểm enforce usage duy nhất** (fill thiếu = 0, âm → ValidationError)
- **OpenAI**: explicit client bypass is_available; is_available = installed AND (key OR base_url) — static check
- **Ollama**: URLError(ConnectionRefused/gaierror) → ModelNotAvailableError; socket.timeout → ModelTimeoutError; HTTPError → ModelError
- **Registry**: class thuần (không singleton), RuntimeKernel pre-register mock, default_name từ settings
