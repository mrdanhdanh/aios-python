# TASK-023 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (13 + 15 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. Contract models** — `memory/contracts.py`: `MemoryKind`, `MemoryStrategy`, `MemoryQuery` (Field constraints C2-11), `MemoryCandidate`, `MemoryScore`, `MemorySelection` (`tokens_by_kind`/`budget` 4 kind — C2-01), `MemoryContext` — tất cả `extra="forbid"`
- [ ] **T2. KnowledgeMemory.list_chunks** — `knowledge/knowledge.py` thêm method additive `list_chunks(source_id=None) -> list[ChunkRecord]` (dataclass mới; query sqlite trực tiếp; `ORDER BY source_id, chunk_index` — C1-01/C2-14); không sửa `ChunksStore`
- [ ] **T3. Sources adapters** — `memory/sources.py`: `MemorySource` Protocol local + `ConversationSource`, `SessionSource` (get_all SHARED + prefix, content=str(value), created_at từ Context.created — C2-04), `KnowledgeSource` (structural Protocol + Any, created_at = epoch UTC — C2-02), `ArtifactSource` (content=name, created→created_at — C3-04/C2-15)
- [ ] **T4. Coordinator pipeline** — `memory/coordinator.py`: `MemoryCoordinatorConfig` (weights sum=1 validate, half_life, source_priority, budget), `MemoryCoordinator` với pipeline `Retrieve → Filter → Rank → Compress → Deduplicate → Prioritize` (C2-03), `estimate_tokens`, short-circuit query rỗng (C2-02), clock injectable, inject() → ContextService EXECUTION scope
- [ ] **T5. Ranking** — công thức total, tie-break `total→source_priority→created_at→id`, cosine normalize `(cos+1)/2` (C2-09), recency clamp [0,1] (C2-10), tz-aware normalize (C2-06)
- [ ] **T6. Compress + Dedup** — `content[:max_chars-1] + "…"` (C2-08); dedup key SHA-256 normalize content sau compress
- [ ] **T7. Budget/prioritize** — greedy theo total desc theo category; per-kind cap; truncated flag
- [ ] **T8. Settings** — `config.py`: `MemoryBudgetSettings` 6 field + `MemorySettings.budget` (additive)
- [ ] **T9. Wiring** — `runtime_kernel.py`: dựng conversation/knowledge/coordinator + `register_instance`; eager db creation (C2-05)
- [ ] **T10. `__init__.py` re-export** — additive
- [ ] **T11. Unit tests** — `tests/test_memory_coordinator.py`: contracts (extra=forbid, Field constraints, ValidationError strategy lạ), 7 strategies + ma trận C2-05, filter + top_k cắt (C2-07), rank (weights, tie-break, fake clock, naive→UTC), compress (C2-08), dedup + regression prefix dài (C2-03), budget AC5 seed cụ thể (C2-13), short-circuit rỗng, inject (C2-05 wording C3-05), deterministic 2 lần chạy fake clock (C2-06)
- [ ] **T12. Arch tests** — `tests/test_architecture.py`: `test_inv_memory_import_allowlist` (C2-01 — cấm knowledge kể cả TYPE_CHECKING; thu hẹp external allow-list — bỏ sqlite3/json/uuid/itertools nếu adapter không dùng, R3-3) + INV-011 tường minh (agents không import memory/knowledge)
- [ ] **T13. Config + wiring tests** — `tests/test_config.py` (budget default + env override) + `tests/test_runtime_kernel.py` (make_settings override cả conversation + knowledge db — R2-1; resolve MemoryCoordinator) + `tests/test_api.py` fixture override knowledge_db_path (R2-1)
- [ ] **T14. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (mục tiêu ≥ 95% — R3-4); git diff verify additive only
- [ ] **T15. test.md + evaluation.md** — ghi kết quả, đối chiếu 10 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
