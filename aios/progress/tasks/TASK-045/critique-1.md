# TASK-045 — Critique v1

## Phản biện
- **P1-01 `^` semantics**: `^2.0` = `>=2.0.0 <3.0.0` (major pinned). Không được hiểu lỏng.
- **P1-02 Missing contract**: requires trỏ contract không tồn tại trong runtime → FAIL (fail-closed, không silently pass).
- **P2-01 Namespace enforce**: ApiNamespace là marker + gate — matrix phải từ chối contract nằm ngoài namespace được phép khi `allow_namespaces` được cấu hình.
- **P2-02 Constraints**: hỗ trợ ít nhất `^`, `>=`, exact, `*`; constraint lạ → error.
- **P3-01 Result**: errors/warnings tách biệt, có message rõ.

## Resolution
- ✅ `^X.Y.Z` → major pinned; `>=X.Y.Z`; exact; `*`.
- ✅ Missing → error entry.
- ✅ `check(..., allowed_namespaces)` optional gate.
- ✅ `CompatibilityResult` errors/warnings list.
