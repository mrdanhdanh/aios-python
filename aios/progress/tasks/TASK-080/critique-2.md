# TASK-080 — Critique vòng 2 (spec)

> **Critic**: AIOS Orchestrator (vòng 2 — sau resolve vòng 1)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved

## P1 — Phải sửa

### C2-01. Threshold pixel diff 30/255 — cố định hay tham số?
→ **Resolve**: tham số `pixel_threshold: int = 30` (default) — probe config; test dùng 0 để
phát hiện chính xác. Ghi rõ.

### C2-02. UIState "canonical JSON" — sort keys ổn định?
→ **Resolve**: canonical = `json.dumps(obj, sort_keys=True, separators=(",", ":"))` — deterministic
cross-version; state_hash = SHA256(canonical). Ghi rõ.

### C2-03. Probe trả gì khi cả 2 evidence đều thiếu ref?
→ **Resolve**: 2 bên thiếu ref → vẫn `MISSING_EVIDENCE` (không PASS) + evidence note "both missing".
Không có đường tắt.

## P2 — Nên sửa

### C2-04. Input timeline trong evidence — dùng InputEvent của P1 hay copy?
→ **Resolve**: dùng `InputEvent` (P1) trực tiếp — không duplicate contract.

### C2-05. CLI visual-probe flags?
→ **Resolve**: `--ref`/`--current` (JSON file evidence — viết file bằng `--dump-ref`/`--dump-current`
từ mock), `--threshold`. Mock evidence: ref hợp lệ + current giống → PASS; `--missing-ref` mô phỏng
thiếu ref → MISSING_EVIDENCE.

### C2-06. Observability register khi nào (kernel wiring)?
→ **Resolve**: register qua `MetricsRegistry` trong module (lazy, idempotent) — không cần sửa
RuntimeKernel (tránh chạm nhiều). Ghi chú tasks.

## P3 — Ghi nhận

### C2-07. VisualEvidence version?
→ Resolve: thêm `version: str = "1.0"` — cùng tư duy UIState version.

### C2-08. Có cần `render_state` bắt buộc không?
→ Resolve: bắt buộc (field required) — R10 là nền R1; evidence thiếu state → MISSING_EVIDENCE.

## Kết luận
Spec v2 sau resolve C2-01..06 → **APPROVED — được phép implement** (đủ 2 vòng critique).
