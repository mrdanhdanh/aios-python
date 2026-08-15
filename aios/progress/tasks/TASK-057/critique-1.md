# TASK-057 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — "validate" từ đâu (ai gọi)?
Learning loop tự validate hay cần human/harness?
→ **Resolve**: `validate(key, confidence, source)` — source mô tả nguồn (VD "evaluation", "human", "replay"); v1: bất kỳ ai có quyền gọi đều được (offline), nhưng validate phải có source — không validate trống. Loop tự gọi khi evaluation xác nhận.

## C1-02 (P2) — Deduplicate tăng confidence thế nào?
→ **Resolve**: entry cũ: confidence = min(1.0, old + 0.1), updated_at mới. Deterministic.

## C1-03 (P2) — Lesson extract deterministic?
→ **Resolve**: `learn(failure: dict)` — yêu cầu keys when/failure/cause/fix/confidence; thiếu → raise `MemoryPromotionError`? Không — thiếu cause/fix → lesson vẫn lưu nhưng confidence thấp (0.3) và KHÔNG promote được (INV-034). Đủ 5 keys → confidence = input confidence.

## C1-04 (P3) — retrieve theo kind hay global?
→ **Resolve**: `retrieve(kind, key=None)` — kind bắt buộc; key None → list theo kind.

## C1-05 (P3) — Working memory có TTL không?
→ **Resolve**: v1 không TTL (working = phiên làm việc; cleanup để wiring sau). Ghi chú.

## Kết luận
Resolve xong. Vòng 2 kiểm tra.
