# Critique vòng 1 — TASK-024 (Context Optimizer)

**Critic**: subagent critic | **Ngày**: 2026-08-14 | **Spec phản biện**: v1

## Đánh giá chung
Spec bám PLAN §4/§5/§6/§22/§23 sát, phân vai rõ với TASK-023, phạm vi In/Out cứng. Kiểm chứng code: không cycle (`context → memory` 1 chiều), allow-list khả thi, `MemorySelection.items`/`estimate_tokens`/`MemoryBudget` đúng. Package `context/` mới được đồng thuận. 2 P1 + 4 P2 + 5 P3 — cần resolve trước implement.

## P1 — Blockers

### C1-01: Merge fragments (L1) phá granularity cut-from-bottom
- **Vấn đề**: YC-2 mapping cho mọi candidate cùng kind chung 1 source string (`memory.knowledge`/`memory.history`/...) + YC-3.3 merge cùng (tier, source) → mỗi tier memory luôn gộp thành ĐÚNG 1 section → cut-from-bottom drop cả tier (mất top-rank) thay vì loại item ít ưu tiên; token drift sau join `"\n"` + re-token → cả tier bị drop sạch; AC6 test vacuous.
- **Resolution**: (a) merge **loại trừ source `memory.*`** — chỉ merge fragment thật (execution state keys cùng nguồn); memory tiers giữ 1 section/candidate (thứ tự items = rank desc sẵn có). Thêm test item-level: 2 candidate cùng tier, cap cắt → candidate cuối (score thấp hơn) bị loại trước.

### C1-02: Mâu thuẫn P0 cap (3000) vs "P0/P1 không bao giờ loại"
- **Vấn đề**: YC-6.1 bao gồm P0 trong loop loại tới khi ≤ cap — mâu thuẫn YC-6.2 "P0/P1 không bao giờ loại". Pre-check chỉ raise khi P0+P1 > usable, không phủ P0 > cap riêng.
- **Resolution**: **P0/P1 exempt khỏi per-tier cap enforcement** — cap = trần báo cáo, không cắt; enforcement duy nhất cho P0/P1 = pre-check `P0+P1 > usable → ValueError`. Thêm test: P0 > 3000 nhưng P0+P1 ≤ usable → giữ nguyên vẹn, `tier_reports` ghi `used > cap` (báo cáo, tổng ≤ usable nên không vi phạm INV-012).

## P2 — Major

### C2-01: L2 extractive — semantics "trùng term" chưa đủ + fallback mâu thuẫn
- **Resolution**: Định nghĩa chính xác: `any(term in sentence.lower() for term in terms)` (substring, case-insensitive); **terms rỗng → L2 no-op toàn pipeline**; **no-match → giữ nguyên section** (không cắt về câu đầu); không xử lý stopword (giữ — deterministic, ghi chú). Thêm test: case-mismatch, punctuation, request rỗng + over-budget → `levels_used == [1]`.

### C2-02: Serialization `str(value)` không deterministic cho value tùy ý
- **Resolution**: `_serialize_value(value)`: scalar → `str()`; dict/list → `json.dumps(sort_keys=True, default=str)`; object lạ → `f"<{type(value).__name__}>"` (loại địa chỉ bộ nhớ). Thêm test với object/dict lồng.

### C2-03: Token accounting sau transform chưa định nghĩa
- **Resolution**: Quy tắc "**re-token mọi section sau mỗi transform (merge/extractive/L3)** — `tokens = estimate_tokens(content)` luôn tính từ content hiện tại". Thêm test: merge làm section vượt usable đúng 2 token → vẫn ≤ usable sau cut.

### C2-04: Empty P1 — mâu thuẫn YC-2 vs L1 + token "ma" 1
- **Resolution**: P1 section rỗng **exempt khỏi L1 empty-drop** (vẫn render header User Request); `tokens` cho content rỗng = 0 (không dùng estimate_tokens cho rỗng). Test: `optimize("")` → render có header User Request rỗng.

## P3 — Minor
- **C3-05**: "message cũ" (PLAN §6 L1) → phủ qua P4/P5 threshold (score gồm recency) — L1 không lặp lại; ghi 1 dòng rationale vào YC-3.
- **C3-06**: Consolidate defaults: `budget=MemoryBudget()`, `relevant_threshold=0.5`, `max_compression_level=2`, `force_extractive=False`, `extractive_max_chars=4000`, `compressor=None`; **clock chỉ ở `__init__` param** (config không chứa clock).
- **C3-07**: **P0/P1 không bao giờ là victim của dedup** (chỉ tier thấp hơn bị loại khi trùng P0/P1); thêm test.
- **C3-08**: cap 5000 ghi ở **P4**, P5 `cap=None` (shared với P4); `final_tokens` = tổng cuối sau MỌI bước (bằng `FinalContext.total_tokens`), ratio phản ánh cả cut.
- **C3-09**: Ghi chú: P1 tokens hiệu quả "mượn" từ tier dưới qua total cut — hành vi cố ý theo priority (sum(caps) = 19000 chỉ "nhất quán không cắt thêm" khi P1 = 0).

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C1-01, C1-02 (P1) + C2-01..C2-04 (P2) + P3 → spec v2, rồi critique vòng 2.
