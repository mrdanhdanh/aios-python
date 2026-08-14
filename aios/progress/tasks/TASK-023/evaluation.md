# TASK-023 — Evaluation (Memory Coordinator)

**Ngày**: 2026-08-14 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (10/10 AC pass — xem test.md)

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 Contracts | ✅ | test_memory_coordinator.py TestContracts (4 test) |
| AC2 7 strategies | ✅ | TestStrategies (9 test) |
| AC3 Ranking | ✅ | TestRanking (5 test) + TestDeterminism |
| AC4 Dedup | ✅ | TestDedup (3 test) |
| AC5 Budget 4K | ✅ | test_ac5_budget_4k (seed 100 memories, per-kind cap, dropped min-total) |
| AC6 Compress | ✅ | TestCompress (2 test) |
| AC7 Inject | ✅ | TestInject (3 test) + test_inv011_memory_isolation |
| AC8 Settings | ✅ | test_config.py budget default + env override |
| AC9 Wiring | ✅ | test_runtime_kernel (resolve + inject E2E) + 855 pass / 95.16% |
| AC10 Architecture | ✅ | test_inv_memory_import_allowlist + git diff additive only |

## Đánh giá so với PLAN.md §M5-3
- **Retrieval 7 strategies** (§3.1): đủ, ma trận source×strategy tường minh (chỉ strategy có dữ liệu thật)
- **Ranking** (§3.2): `MemoryScore = 0.35·semantic + 0.25·relevance + 0.15·recency + 0.10·importance + 0.15·source_priority` — deterministic, weights validate sum=1
- **Memory Budget** (§3.3): 6 category trong Settings (3K/2K/6K/5K/3K/1K), 4 kind map; system/reserve dành TASK-024
- **Contract** (§3.4): 5 models đúng tên (MemoryQuery/Candidate/Score/Selection/Context); coordinator không phụ thuộc store implementation (duck-typed)
- **INV-011 Memory Isolation**: enforced bằng AST test (agents/ không import memory/knowledge; memory/ không import knowledge kể cả TYPE_CHECKING)

## Bài học
1. **AST scan đếm cả TYPE_CHECKING** — đừng bao giờ đề xuất `TYPE_CHECKING` cho import bị cấm (critic vòng 2 bắt được — P1). Dùng structural Protocol + Any.
2. **Query rỗng không đồng nghĩa "không có gì"**: RECENCY/IMPORTANCE hợp lệ với text rỗng — short-circuit phải phân biệt strategy cần text.
3. **HYBRID là strategy gộp** — source không nên khai báo hỗ trợ HYBRID; coordinator mở rộng trước khi dispatch.
4. **Giới hạn filesystem Windows** (filename ~255 chars) phá giả định seed test — kiểm chứng bằng thực nghiệm, không chỉ lý thuyết.
5. **BOM UTF-8 trong file cũ** có thể phá AST scan — kiểm tra encoding khi mở rộng phạm vi scan.

## Đề xuất cho task sau
- TASK-024 Context Optimizer có thể đọc `memory.context` từ ContextService (EXECUTION scope) — key đã ổn định
- Embedder thật (Ollama) gắn vào `KnowledgeSource(embedder=...)` trong wiring — semantic sẽ có hiệu lực
- Memory Coordinator là consumer tiềm năng của Orchestrator (Memory Coordinator trong M5 flow: `Request → ... → Memory Coordinator → Context Optimizer → ...`)

## Kết luận
- [x] ĐẠT spec (10/10 AC)
- [x] Không phá architecture (INV-011 enforced, additive only)
- [x] Deterministic verified, coverage 95.16% (toàn suite 855 pass)
