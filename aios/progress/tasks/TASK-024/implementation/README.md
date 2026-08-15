# TASK-024 — M5 Context Optimizer — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `context/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/context/optimizer.py` — `ContextOptimizer` (Deduplicate → Compress → Prioritize → Token Budget → Final Context)
- `backend/src/aios_core/context/contracts.py` — contracts (extra=forbid)

## Key behavior
- Tier mapping 7 nguồn → P0..P6 (P0 System/Safety · P1 User Request · P2 Current Execution · P3 Knowledge · P4 Memory · P5 Historical · P6 Optional)
- Compression 3 cấp: L1 deterministic (dedup — P0/P1 không victim; merge defensive loại trừ memory.*), L2 extractive (substring case-insensitive, chỉ P3..P6, truncate prefix), L3 LLM stub — mặc định không chạy (Deterministic First → LLM Last)
- Token budget: loại từ dưới lên theo tier (INV-012); P0 exempt cap; section đơn > cap → truncate prefix; ValueError khi P0+P1 > usable
- FinalContext sort tier asc + render header; deterministic (2 lần chạy model_dump() bằng nhau)
- Integration MemoryCoordinator → ContextOptimizer end-to-end (wiring RuntimeKernel.create)

## Verification
- `pytest` full suite: **896 passed, coverage 95.21%, 11/11 AC** (xem `test.md`)
