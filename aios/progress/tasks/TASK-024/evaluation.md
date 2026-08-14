# TASK-024 — Evaluation (Context Optimizer)

**Ngày**: 2026-08-14 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (11/11 AC pass — xem test.md)

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 Contracts + render | ✅ | TestContracts (4 test) |
| AC2 Tier mapping | ✅ | TestTierMapping (7 test) |
| AC3 L1 | ✅ | TestLevel1 (5 test) |
| AC4 L2 | ✅ | TestLevel2 (8 test) |
| AC5 L3 stub | ✅ | TestLevel3 (4 test) |
| AC6 INV-012 budget | ✅ | TestBudget (7 test) + test_inv012_context_budget |
| AC7 FinalContext + render | ✅ | TestContracts + TestLevel2 |
| AC8 Determinism | ✅ | TestDeterminism |
| AC9 Integration | ✅ | TestIntegration (MemoryCoordinator→Optimizer) |
| AC10 Wiring | ✅ | test_context_optimizer_wired + 896 pass / 95.21% |
| AC11 Architecture | ✅ | test_inv_context_import_allowlist + git diff additive only |

## Đánh giá so với PLAN.md §M5-4/5/6
- **Trách nhiệm tách bạch với TASK-023** (§4): Memory Coordinator = "nên lấy memory nào"; Context Optimizer = "đưa bao nhiêu và dưới dạng nào vào model" — optimizer chỉ đọc `memory.context` (EXECUTION scope), không gọi pipeline memory lại
- **Context Priority P0..P6** (§5): đủ 7 tier; loại TỪ DƯỚI LÊN (P6→P2) cả per-tier cap lẫn total budget — không truncate ngẫu nhiên; P0/P1 exempt per-tier cap (chỉ pre-check tổng) — quyết định qua critique C1-02
- **Context Compression 3 cấp** (§6): L1 deterministic (dedup + metadata + merge defensive + re-token) · L2 extractive (substring case-insensitive, chỉ P3..P6, no-match giữ nguyên) · L3 = interface stub (defer — cần Model Router TASK-025; deterministic-first)
- **INV-012 Context Budget**: enforcement behavioral (functional test seed vượt budget → total ≤ usable) + allow-list chặn đường ôm logic model — AST không verify được hành vi nên đây là enforcement đúng bản chất

## Bài học
1. **pydantic v2 `sum(BaseModel)` → TypeError** — `model_dump().values()` (reviewer bắt được bằng cách chạy thật — R1-1)
2. **Số liệu scenario phải tính đúng công thức thật**: "usable = sum(5 field không reserve)" — reviewer chạy verify phát hiện 2800 ≠ 2000 (R1-2)
3. **Merge dễ thành dead code**: source per-key unique → merge không fire input thật — phải tường minh "defensive" trong spec, không viết test giả vờ pipeline
4. **Test edge tokens phải tính prefix content** (`"{key}: "` thêm ký tự → token khác)
5. **P0/P1 exempt cap nhưng pre-check tổng** — 2 cơ chế bổ sung nhau; "cap" trở thành trần báo cáo cho P0

## Đề xuất cho task sau
- **TASK-025 Model Router**: L3 compression sẽ dùng model + tokenizer — optimizer đã có interface `ContentCompressor` + `max_compression_level=3` sẵn
- Orchestrator flow (PLAN §20): `Request → ... → Memory Coordinator → Context Optimizer → Policy → Model Router → Planner...` — optimizer đã sẵn sàng qua DI (`register_instance`)
- Observability M5 DoD: `FinalContext` chứa sẵn context size + compression report — metrics gắn sau

## Kết luận
- [x] ĐẠT spec (11/11 AC)
- [x] Không phá architecture (INV-012 behavioral + allow-list, additive only)
- [x] Deterministic verified, coverage 95.21% (toàn suite 896 pass)
