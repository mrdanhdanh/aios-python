# TASK-045 — Critique v2

## Phản biện độc lập
- **P1-01 Không God Object**: matrix là pure function module, không class stateful; contract model thuần dữ liệu.
- **P1-02 extra=forbid** trên ExtensionContract và ContractRequirement.
- **P2-01 Invalid constraint** phải raise `ExtensionError` (không phải ValueError lạ).
- **P2-02 Warnings**: constraint deprecated (ví dụ `~`) → warning không fail.
- **P3-01 `__all__`** giới hạn public API.

## Resolution
- ✅ Pure function `check_requires(requires, runtime_versions, allowed_namespaces=None)`.
- ✅ Pydantic extra=forbid.
- ✅ Constraint parse lỗi → `ExtensionError`.
- ✅ `~` (pessimistic) → warning.
- ✅ `__all__` đầy đủ.
