# TASK-016 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Architecture invariant tests (AST, fail-closed) | `backend/tests/test_architecture.py` |
| AST scan helper (pure — không import runtime) | `backend/tests/_arch_scan.py` |
| Reference docs | `docs/architecture.md` §7 (INV-001..010), `docs/adr/0004-architecture-invariants.md`, link + index trong `docs/PLAN.md` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- 10 Architecture Invariants chốt thành contract; enforcement tự động qua AST scan trong pytest.
- Scanner KHÔNG import `aios_core` (pure static) → coverage report unaffected, không thể
  bị bypass bằng runtime monkey-patch.
- INV-001/002 active only khi `agents/`+`tools/` tồn tại (skipif), đảm bảo fail-closed
  khi package thiếu.
