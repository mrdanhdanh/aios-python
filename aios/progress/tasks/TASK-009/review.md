# Review — TASK-009 (Pre-Implementation)

## Tổng quan
Spec qua 2 vòng critique (4 P1 + 7 P2 v1; 5 P2 + 10 P3 v2 — đều resolve vào spec). 4 module độc lập, API surface pin đầy đủ (unknown behavior, idempotent, ordering, thread-safe). PLAN.md đã amend 3 chỗ (Knowledge Graph in-memory, M1-P2 populate thủ công, Prompt str.format v1) — nhất quán. **APPROVED.**

## Đối chiếu AC (9 AC ↔ tasks.md)
AC1↔J1.1/J1.3 ✓; AC2↔J1.2 ✓; AC3↔J1.2 ✓; AC4↔J2.1 ✓; AC5↔J2.2 ✓; AC6↔J2.4 ✓; AC7↔J3.1 ✓; AC8↔J3.1 ✓; AC9↔PLAN amend (đã làm) ✓.

## Lưu ý implement (từ critique)
1. Regex lookaround `(?<!\{)\{([A-Za-z_]\w*)\}(?!\})` — Python re hợp lệ; scan escape-first
2. `evaluate` bind version + append cùng lock (read-latest atomic)
3. Catalog search bỏ qua None; sorted (kind, id)
4. Graph neighbors dedup + relation gốc; add_edge missing node → GraphError
5. `from aios_core import capabilities, prompts, catalog, knowledge_graph` — thêm cuối __init__

## Kết luận
- [x] **APPROVED — sẵn sàng implement (đóng M1).**
