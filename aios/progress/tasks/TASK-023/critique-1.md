# Critique vòng 1 — TASK-023 (Memory Coordinator)

**Critic**: subagent critic | **Ngày**: 2026-08-14 | **Spec phản biện**: v1

## Đánh giá chung
Spec đối chiếu PLAN.md §M5-3 (Retrieval §3.1 / Ranking §3.2 / Budget §3.3 / Contract §3.4) không lệch; kiểm chứng code: `ContextScope.EXECUTION` tồn tại, `ContextService.set(scope,key,value,ttl)` khớp YC-8, `MemorySettings` đúng 2 field hiện tại (additive OK), container `register_instance` pattern khớp, allow-list cơ chế khớp, agents/ hiện không import memory (INV-011 pass trivially). Ranh giới TASK-024 rõ ràng.

Có **2 P1** làm một số YC/AC không implement/test được như viết. Mức sẵn sàng: 3/5.

## P1 — Blockers

### C1-01: KnowledgeSource không thể thực hiện keyword/exact/metadata với public API hiện tại
- **Vị trí**: YC-2, §5.2 (cấm import knowledge runtime), Phạm vi Out, §5.5, YC-11
- **Vấn đề**: `KnowledgeMemory` public API chỉ có `index_text / search / delete_source / count`; `ChunksStore` không có enumerate. Spec cấm memory/ import `aios_core.knowledge` runtime, cấm sửa knowledge/*, `KnowledgeSource` chỉ nhận instance → **không tồn tại đường nào đọc chunk text** để keyword/exact/metadata match. Với embedder=None mặc định, KnowledgeSource luôn trả rỗng.
- **Resolution (chọn phương án 1)**: Thêm **additive method read-only** vào `KnowledgeMemory`: `list_chunks(source_id: str | None = None) -> list[ChunkRecord]` (dataclass: `id, source_id, chunk_index, text`). Không đổi hành vi method có sẵn; sửa §5.5 thành "không thay đổi hành vi method có sẵn — chỉ thêm method additive read-only"; Expected artifacts bổ sung `knowledge/knowledge.py` (MOD, additive).

### C1-02: AC5 không kiểm chứng được như viết — mâu thuẫn budget + sai toán học
- **Vị trí**: AC5, YC-7
- **Vấn đề 1**: AC5 ghi "budget 4K" nhưng default budget = 20K → `total_tokens ≤ 4000` không được đảm bảo nếu không override.
- **Vấn đề 2**: "candidate bị loại là candidate total thấp nhất (toàn cục)" sai với cơ chế per-category cap: candidate total 0.7 (history đầy) bị loại trong khi candidate total 0.5 (task còn chỗ) được giữ.
- **Resolution**: Viết lại AC5: (a) test dùng `MemoryBudgetSettings` tùy chỉnh tổng 4K (history 1500, task 1000, knowledge 1000, artifacts 500); (b) assertion "candidate bị loại là candidate có total thấp nhất **trong category tương ứng**"; (c) seed sao cho mỗi category đều vượt cap (tính trước bằng công thức `estimate_tokens = ceil(len/4)`); (d) test overflow 1 category riêng.

## P2 — Major

### C2-01: `MemorySelection.budget`/`tokens_by_category` typed `dict[MemoryKind, int]` nhưng budget thực tế 6 category
- **Resolution**: Đổi tên `tokens_by_category` → `tokens_by_kind`; `budget: dict[MemoryKind, int]` biểu diễn 4 kind khớp 4 category dùng (task/knowledge/history/artifacts); system/reserve chỉ ở `MemoryBudgetSettings`. Thống nhất toàn spec + test.

### C2-02: Query rỗng mâu thuẫn YC-7 vs YC-2 (exact `"" in content` luôn True)
- **Resolution**: Short-circuit ngay đầu pipeline: `text.strip() == ""` → trả `MemorySelection` rỗng (không chạy retrieval); thêm test edge này vào YC-7.

### C2-03: `top_k_per_source` chưa định nghĩa cơ chế cắt khi candidate sau filter vượt top_k
- **Resolution**: Định nghĩa cứng: "sau filter, nếu > `top_k_per_source` → giữ N mới nhất theo `created_at` desc (deterministic)"; sửa phát biểu risk table ("giới hạn sau filter").

### C2-04: SessionSource chưa được spec hóa (enumerate + mapping dữ liệu)
- **Resolution**: SessionSource enumerate qua `context.get_all(ContextScope.SHARED)` + lọc prefix `session:{session_id}:`; `content = str(value)`; `created_at` từ `Context.created` (qua `context.get_context(scope, key)`); `metadata = {}`; `importance = 0.5`.

### C2-05: YC-2 gán metadata/importance cho source không có metadata thật
- **Resolution**: Thay bằng ma trận source×strategy liệt kê chiến lược nào áp dụng source nào có dữ liệu thật: metadata chỉ áp dụng artifact (thật); conversation/knowledge/session không có metadata → metadata strategy trả rỗng cho các source đó (deterministic, không crash). Importance fallback 0.5 là thiết kế — ghi vào Giả định.

### C2-06: Determinism cross-machine của recency khi `created_at` naive
- **Resolution**: Normalize trong source: `created_at` phải tz-aware; naive → giả định UTC (`.replace(tzinfo=timezone.utc)`); thêm test với naive input → chuẩn hóa đúng (không raise, không phụ thuộc timezone máy).

## P3 — Minor

### C3-01: "strategy lạ → ValueError" sai cơ chế exception
- **Resolution**: `MemoryStrategy` là Enum trong pydantic model → string không hợp lệ bị **`ValidationError`** tại boundary `MemoryQuery`; sửa test: assert `ValidationError`. ValueError chỉ dành cho giá trị enum hợp lệ nhưng không hỗ trợ (không xảy ra trong thiết kế — bỏ).

### C3-02: INV-011 arch test gần như dư thừa với allow-list agents hiện có
- **Resolution**: Giữ test (phòng ngừa); ghi chú trong spec §5.1: "đã được bao phủ bởi allow-list agents hiện có (`_AGENTS_ALLOWED_AIOS` = {models.base, models.errors}) — thêm để tường minh INV-011".

### C3-03: Eager DB creation khi `RuntimeKernel.create()` với default settings
- **Resolution**: AC9 test bắt buộc dùng tmp settings (pattern `make_settings(tmp_path)` trong test_runtime_kernel.py) — ghi rõ vào spec.

### C3-04: Artifact candidate `content` chưa định nghĩa
- **Resolution**: Chốt `content = artifact.name` (không đọc bytes file ở retrieval); metadata strategy dùng `artifact.type` + `artifact.metadata` dict thật.

### C3-05: Test YC-8 "không thấy ở scope khác" viết khó hiểu
- **Resolution**: Sửa wording: assert `get(AGENT, "memory.context", inherit=True) is None` (inheritance đi hướng xuống SYSTEM←…←AGENT←EXECUTION) + `get(EXECUTION, "memory.context", inherit=False)` trả đúng `MemoryContext`.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve 2 P1 + 6 P2 + 5 P3 → spec v2
- Khuyến nghị: sau khi resolve, chạy critique vòng 2 trên spec v2.
