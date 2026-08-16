# TASK-080 — Critique vòng 1 (spec)

> **Critic**: AIOS Orchestrator (vòng phản biện độc lập)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved

## P1 — Phải sửa

### C1-01. `screenshot` là path hay base64 — thiếu quy ước
Proposal nói "Screenshot" nhưng evidence cần chạy được trong CI (không phụ thuộc file).
→ **Resolve**: `screenshot: str` = base64 data URI (`data:image/png;base64,...`) — self-contained;
probe không đọc file. Test dùng PNG 1×1 base64 cố định.

### C1-02. `pixel_diff` định nghĩa thế nào? (0.0 = không so sánh là mơ hồ)
→ **Resolve**: `pixel_diff: float = -1.0` — `-1` = KHÔNG có ref để so (missing evidence),
`0.0` = giống hệt, `>0` = % pixel khác biệt (so sánh pixelwise RGB theo threshold 30/255).
Tránh nhầm "0.0 = không so sánh".

### C1-03. Probe outcome phải có state cụ thể — thiếu ref dùng MISSING_EVIDENCE hay NOT_EXECUTED?
→ **Resolve**: thiếu ref → `MISSING_EVIDENCE`; probe không được gọi → `NOT_EXECUTED`;
render/collector lỗi → `ERROR`. Cả 3 đều KHÔNG PASS (INV-035). Ghi rõ state mapping.

## P2 — Nên sửa

### C2-01. DOM snapshot khác như thế nào — diff thế nào?
→ **Resolve**: dom_snapshot = dict `{"tag": str, "text": str, "attrs": dict, "children": [...]}`
(recursive); so sánh canonical JSON; diff chỉ ghi `{"path": "...", "before": ..., "after": ...}`.

### C2-02. browser_meta gồm gì?
→ **Resolve**: `{"browser": str, "os": str, "viewport": [w, h], "device_scale_factor": float}`
— để chẩn đoán diff do GPU/font (proposal cảnh báo).

### C2-03. Observability metrics — dùng registry nào?
→ **Resolve**: dùng `observability/metrics.py` (MetricsRegistry có sẵn M4) — register counters
`visual_probe_count` + `visual_fail_closed_violations` + gauge `visual_pixel_diff_max`.
Không thêm backend mới.

## P3 — Ghi nhận

### C3-01. UIState có cần version?
→ Resolve: thêm `version: str = "1.0"` — mở đường Contract 1.0 +AssetPipeline (P3/R9).

### C3-02. Probe có nên tự render (gọi render_fn) không?
→ Resolve: probe NHẬN evidence (không render) — tách biệt capture (P1 harness) vs compare (P2 probe).

## Kết luận
Spec khả thi sau resolve C1-01..03 + C2-01..03 → chuyển vòng 2.
