# TASK-024 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (11 + 15 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. Contracts** — `context/contracts.py`: `PriorityTier` (7 giá trị), `ContextSection` (tokens: rỗng → 0 — C2-12), `TierBudgetReport` (cap=None = uncapped/shared — C2-13), `CompressionReport` (levels_used có [1,3] — C2-11), `FinalContext` + `render()` — extra=forbid
- [ ] **T2. Optimizer core** — `context/optimizer.py`: `ContextOptimizerConfig` (6 defaults — C3-06), `ContextOptimizer` (`__init__` nhận context + config + now clock), `optimize(user_request)` pipeline: build → L1 → L2 (nếu vượt) → L3 (nếu có compressor) → pre-check → cut
- [ ] **T3. Build & tier mapping** — YC-2: P0 get_all(SYSTEM), P1 user_request, P2 state keys + session (thứ tự state trước, session sau — C2-04), P3/P4/P5/P6 từ `memory.context.selection.items` (P4/P5 theo relevant_threshold); `_serialize_value` (json.dumps sort_keys + try/except fallback — C2-03); bỏ `_`-keys; memory.context None → P2(session)/P3..P6 rỗng không crash
- [ ] **T4. L1 compress** — dedup toàn cục (P0/P1 không victim — C3-07), bỏ metadata thừa, merge defensive loại trừ memory.* (C1-01/C2-02), re-token sau transform (C2-03)
- [ ] **T5. L2 extractive** — thuần hàm `extractive_compress`: terms rỗng → no-op toàn pipeline (kể cả force_extractive — C2-09); substring case-insensitive; no-match → giữ nguyên; max_chars cắt `[:X-1]+"…"`; chỉ P3..P6; re-token
- [ ] **T6. L3 stub** — `ContentCompressor` Callable + config.compressor; re-token sau L3 (C2-05); levels_used [1,3]
- [ ] **T7. Budget & cut** — YC-6: pre-check SAU L2/L3 (C2-10) `P0+P1 > usable → ValueError`; per-tier cap P6→P2 (P0/P1 exempt — C1-02); section đơn > cap → truncate prefix X = cap×4 (C2-07); total cut P6→P2; truncated chỉ khi drop section (C2-15); tier_reports/final_tokens sau mọi bước (C3-08)
- [ ] **T8. Wiring** — `runtime_kernel.py`: lazy import + `register_instance(ContextOptimizer, ...)` tái dùng `settings.memory.budget`; KHÔNG thêm settings
- [ ] **T9. Unit tests** — `tests/test_context_optimizer.py`: contracts, tier mapping, L1 (dedup/merge defensive), L2 (case/punctuation/empty/no-match), L3 stub (gọi 1 lần, ValidationError, re-token, [1,3]), budget scenarios (C2-06: thứ tự P6→P5→P4, item-level, P0 vượt cap, per-tier, ValueError, edge 2 token — C2-14), render (P1 rỗng header — C2-12), determinism 2 lần chạy, INV-012 functional test
- [ ] **T10. Arch tests** — `tests/test_architecture.py`: `test_inv_context_import_allowlist` (json — C2-01; cấm models/knowledge/orchestrator/contracts kể cả TYPE_CHECKING) + `test_inv012_context_budget` (behavioral — gọi optimizer thật)
- [ ] **T11. Integration + wiring tests** — `test_context_optimizer.py` (MemoryCoordinator.inject → optimize end-to-end — YC-10) + `test_runtime_kernel.py` (resolve ContextOptimizer)
- [ ] **T12. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (95% mục tiêu); git diff verify additive only
- [ ] **T13. test.md + evaluation.md** — đối chiếu 11 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
