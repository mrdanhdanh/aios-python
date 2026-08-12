# Review — TASK-006 (Pre-Implementation)

## Tổng quan
Spec chi tiết, patch target module-level rõ ràng, 13/13 AC phủ. RuntimeKernel thêm ModelRegistry KHÔNG phá TASK-005 (đã verify container/test pattern). **APPROVED kèm 2 điều kiện (R2) + 4 R3.**

## Vấn đề + Resolution

### R2-1 — api_key fallback env làm AC5 mất determinism
- **Resolution**: pin env var `OPENAI_API_KEY`/`OPENAI_BASE_URL`; test AC5 phải `monkeypatch.delenv` 2 biến này (pattern test_config).

### R2-2 — MockModel(responses=None) chưa định nghĩa
- **Resolution**: `responses=None` ≡ không có response → `_chat()` raise `ModelError("MockModel responses exhausted")`; thêm test case `MockModel()` → ModelError.

### R3 (áp khi implement)
1. Test AC13 đặt ở `test_runtime_kernel.py`
2. `metadata()`: version = `aios_core.__version__` ("0.1.0"), id = `models.<name>`
3. `default()` dùng `default_name` constructor param (registry không giữ Settings)
4. `chat()` default temperature=0.7; echo trả content message CUỐI (bất kể role)

## Kết luận
- [x] **APPROVED có điều kiện — 2 R2 + 4 R3 resolve khi implement.**
