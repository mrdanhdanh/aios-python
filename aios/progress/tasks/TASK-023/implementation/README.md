# TASK-023 — M5 Memory Coordinator — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `memory/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/memory/coordinator.py` — `MemoryCoordinator` (Retrieve → Filter → Rank → Dedup → Compress → Prioritize → Inject)
- `backend/src/aios_core/memory/contracts.py` — 5 models (`MemoryQuery`/`MemoryCandidate`/`MemoryScore`/`MemorySelection`/`MemoryContext`, extra=forbid) + `MemoryBudget` (local — tránh memory→config dependency, allow-list)
- `backend/src/aios_core/memory/sources.py` — 7 strategies (exact/keyword/semantic/metadata/recency/importance/hybrid)

## Key behavior
- 7 retrieval strategies; HYBRID mở rộng → {semantic, keyword, recency}
- Ranking deterministic: weights + tie-break 4 cấp + fake clock (naive → UTC)
- Budget: per-kind cap + total cap + dropped min + truncated flag (INV-012 context cho Memory)
- Compress `max_chars-1 + "…"`; dedup giữ candidate tốt nhất
- Inject EXECUTION scope, overwrite, inherit qua ContextService
- Agent KHÔNG truy cập Memory trực tiếp — INV-011 (allow-list memory/: cấm knowledge kể cả TYPE_CHECKING)

## Verification
- `pytest` full suite: **855 passed, coverage 95.16%, 10/10 AC** (xem `test.md`)
