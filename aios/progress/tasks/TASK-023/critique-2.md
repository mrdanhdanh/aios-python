# Critique vòng 2 — TASK-023 (Memory Coordinator)

**Critic**: subagent critic | **Ngày**: 2026-08-14 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
C1-01 RESOLVED (tạo mâu thuẫn mới → C2-01 P1) · C1-02 RESOLVED ĐÚNG · C2-01 RESOLVED ĐÚNG · C2-02 RESOLVED ĐÚNG · C2-03 RESOLVED ĐÚNG · C2-04 RESOLVED ĐÚNG · C2-05 RESOLVED ĐÚNG · C2-06 RESOLVED ĐÚNG · C3-01 RESOLVED KHÔNG ĐẦY ĐỦ (AC2 còn sót → C2-04 P2) · C3-02 RESOLVED ĐÚNG · C3-03 RESOLVED 1 PHẦN (chỉ vá test → C2-05 P2) · C3-04 RESOLVED ĐÚNG (lưu ý field `created` → C2-15 P3) · C3-05 RESOLVED ĐÚNG

## Mục B — Vấn đề mới

### P1
**C2-01**: `TYPE_CHECKING` không thoát được AST allow-list (`collect_imports` đếm MỌI Import node kể cả trong `if TYPE_CHECKING:`) → `test_inv_memory_import_allowlist` fail như spec v2 viết.
→ **Resolution**: Cấm import `aios_core.knowledge` tuyệt đối trong `memory/*.py` kể cả TYPE_CHECKING. `KnowledgeSource` dùng **local structural Protocol** khai báo ngay trong `memory/sources.py` (duck-typed; store + embedder nhận `Any`). `runtime_kernel.py` là nơi duy nhất import `KnowledgeMemory`.

### P2
**C2-02**: `MemoryCandidate.created_at` required nhưng knowledge chunks không có timestamp.
→ **Resolution**: `KnowledgeSource` đặt `created_at = datetime(1970,1,1, tzinfo=utc)` cố định (epoch) → recency = 0 deterministic, đúng matrix "recency ✗". Ghi Giả định §7.

**C2-03**: Pipeline order sai — Dedup (trên content đầy đủ) trước Compress → 2 content dài cùng prefix thành duplicate sau truncate.
→ **Resolution**: Đổi pipeline thành `Retrieve → Filter → Rank → Compress → Deduplicate → Prioritize` + regression test (2 content dài cùng prefix → 1 section).

**C2-04**: AC2 còn sót "strategy lạ → ValueError".
→ **Resolution**: Sửa AC2 → "strategy không hợp lệ → `ValidationError` (pydantic tại boundary `MemoryQuery`)".

**C2-05**: `RuntimeKernel.create()` eager tạo conversation.db + knowledge.db — đổi hành vi runtime CLI/API (4 call site không settings trong workflow/cli.py + api/app.py).
→ **Resolution**: Chốt **eager creation** (persistence là mục đích; pattern đã có: EventService tạo audit.db eager) + ghi nhận vào Phạm vi/Rủi ro như hành vi mới chủ ý; test dùng tmp settings.

**C2-06**: Test YC-9 ("2 lần chạy model_dump() bằng nhau") tự fail nếu không dùng fake clock (recency trôi theo time.time()).
→ **Resolution**: YC-9/AC3 test bắt buộc **fixed fake clock** (hằng số epoch) + fixture `created_at` cố định.

### P3
- **C2-07**: tie-break top_k khi created_at bằng nhau → chốt `created_at desc → id asc`.
- **C2-08**: "…" có tính vào max_chars → chốt `content[:max_chars-1] + "…"` (tổng = max_chars).
- **C2-09**: chuẩn hoá cosine → chốt `(cos + 1) / 2`.
- **C2-10**: recency clamp `max(0.0, min(1.0, ...))` — tránh created_at tương lai → recency > 1.
- **C2-11**: Field constraints hiện trong sketch: `top_k_per_source: int = Field(gt=0)`, `min_importance: float = Field(ge=0, le=1)`, `max_chars: int = Field(gt=0)`.
- **C2-12**: filter `since` với knowledge (created_at = epoch) loại toàn bộ → chốt: **knowledge bỏ qua `since` filter** (ghi chú).
- **C2-13**: AC5 seed cụ thể: artifact name > 200 ký tự (51 tokens × 10 = 510 > cap 500); knowledge 30 chunks × ~125 tokens = 3750 > 1000; total cách biệt rõ.
- **C2-14**: `list_chunks` query sqlite trực tiếp trong knowledge.py (không sửa ChunksStore) + `ORDER BY source_id, chunk_index` deterministic.
- **C2-15**: ArtifactContract field timestamp là `created` (kế thừa AiOSMetadata) → adapter map `contract.created → created_at`.

## Kết luận
- [x] Cần sửa trước khi implement: resolve C2-01..C2-06 + P3 → spec v3. Sau vòng này **approve** (không cần critique vòng 3).
