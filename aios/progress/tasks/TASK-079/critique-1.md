# TASK-079 — Critique vòng 1 (spec)

> **Critic**: AIOS Orchestrator (vòng phản biện độc lập)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved

## P1 — Phải sửa

### C1-01. `render_fn` contract chưa đủ chặt — ai định nghĩa "pixel"?
Spec nói `(frame: RenderFrame) -> bytes` nhưng không nói bytes là gì (PNG? raw pixel?).
→ **Resolve**: contract `RenderFn = Callable[[RenderFrame], bytes]` — bytes là **raw pixel buffer**
(W×H×3 RGB, không nén) do harness quy định `width`/`height`; pixel_hash = SHA256 của buffer.
Harness cung cấp `frame.index`, `frame.t`, `frame.seed` — render_fn không được đọc ngoài frame (pure).
Ghi rõ vào spec §2.1.

### C1-02. Freeze policy chưa định nghĩa — "frozen state" là gì?
Proposal §1b nhắc "frozen state" (đóng băng thời gian render, particles dùng PRNG seeded).
→ **Resolve**: `freeze_policy: str = "none"` — `none` (time thật), `fixed` (t = frame.t cố định
theo timeline), `paused` (t = 0 sau frame đầu). Harness sinh frame.t theo policy. Ghi rõ.

### C1-03. AssetIdempotencyClassifier "exactly-once" cho asset generation — cơ chế đảm bảo gì?
→ **Resolve**: classifier CHỈ phân loại + quyết định (retry/approve/compensate) — cơ chế đảm bảo
(exactly-once) là do caller + journal (tái dùng M10). Classifier: `exactly-once` = idempotent write
(retry OK), `at-least-once` = read-like (retry OK), `at-most-once` = non-idempotent (approve/compensate).
Fail-closed: không khai báo → at-most-once.

## P2 — Nên sửa

### C2-01. Replay cần persist không (journal)?
→ **Resolve**: P1 chưa cần persist — replay in-memory; journal/durability cho visual để P2/R1
(VisualEvidence lưu artifact). Ghi vào tasks.md.

### C2-02. Frame rate mặc định?
→ **Resolve**: fps mặc định 60, max_frames mặc định 300 (5s @60fps). CLI cho override.

### C2-03. So sánh hash toàn buffer hay từng frame?
→ **Resolve**: harness so sánh **toàn bộ chuỗi frame hash** (list) — một frame khác → unstable.
Ngoài ra lưu `diff_frames: list[int]` (chỉ số frame khác) để chẩn đoán.

## P3 — Ghi nhận

### C3-01. Test render_fn mock sinh pixel theo (state, t, seed)?
→ Resolve: mock deterministic đơn giản — `pixel = (state + t + seed*7) % 256` đủ phát hiện thay đổi.

### C3-02. Có cần arch test (import allow-list) cho rendering/?
→ Resolve: có — thêm 1 test `test_rendering_import_allowlist` (chỉ import kernel.durability +
verification + stdlib; không import agents/enterprise...) — mirror M5–M9 pattern.

## Kết luận
Spec khả thi sau resolve C1-01..03 + C2-01..03 → chuyển vòng 2.
