# TASK-006 — Breakdown checklist

## G1 — Models package
- [ ] G1.1 `errors.py` — ModelError hierarchy
- [ ] G1.2 `base.py` — ChatMessage (Literal role), ChatResponse (usage enforce), ModelContract template-method
- [ ] G1.3 `mock.py` — MockModel (echo/responses/loop/exhausted/calls/usage)
- [ ] G1.4 `openai_provider.py` — OpenAIModel (client seam, lazy-build, is_available)
- [ ] G1.5 `ollama_provider.py` — OllamaModel (urllib module-ref, timeout, 3-nhánh error map)
- [ ] G1.6 `registry.py` — ModelRegistry (register/get/list/default, lock)
- [ ] G1.7 `__init__.py` exports

## G2 — Wiring + Settings
- [ ] G2.1 `ModelsSettings` + config.yaml `models:` + test_config
- [ ] G2.2 `runtime_kernel.py`: register_instance(ModelRegistry) + pre-register mock
- [ ] G2.3 test_import cập nhật

## G3 — Tests + Verify
- [ ] G3.1 test_models.py (contract validate, mock 8 case, registry 6 case, openai 4 case, ollama 6 case)
- [ ] G3.2 pytest pass, coverage ≥ 80%, git sạch
- [ ] G3.3 Commit code + progress files + commit cuối
