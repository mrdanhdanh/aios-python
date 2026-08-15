# TASK-057 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Promote: gate duy nhất là validated? Confidence?
→ **Resolve**: promote cần validated=True VÀ confidence ≥ 0.5 (double gate — an toàn hơn INV-034 tối thiểu). Chưa đủ → MemoryPromotionError kèm lý do.

## C2-02 (P2) — Promote đi đâu (Knowledge)?
→ **Resolve**: v1 promote = đánh dấu `promoted=True` trong autonomous memory + emit event (AIOS Knowledge pipeline wiring ở phase sau — M9 không sửa knowledge/). Ghi chú trong spec: INV-034 enforce ở cổng promote của AutonomousMemory.

## C2-03 (P3) — Key tự sinh hay người gọi?
→ **Resolve**: `store(kind, key, ...)` — key do caller; learn() tự sinh key `lesson:{fingerprint}` (tái dùng recovery fingerprint hash).

## Kết luận
Resolve xong — spec đủ chặt.
