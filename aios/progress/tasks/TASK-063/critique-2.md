# TASK-063 — Critique vòng 2 (M10-F1, spec v2)

> Critic vòng 2 (độc lập, sau khi resolve vòng 1 M10-F1). Kiểm tra spec v2 + bổ sung đã resolve.

## Các vấn đề tìm được

### C2-01 (P2) — Kiểm tra "mọi INV có enforcement test" phải nêu ngoại lệ thực tế
Một số INV được enforce bằng literal/allow-list trong test (vd `test_inv007_*`), số khác bằng scanner runtime (`arch_health.py`) hoặc label `test_m9_*` (INV-030..034). Script đối chiếu đơn giản grep `inv0XX` có thể miss nhãn `m9_*`.
→ **Resolve**: Script đối chiếu grep cả 2 dạng: `test_inv0xx` (dạng đầy đủ: `test_inv007_hard_call_site`...) và `test_m9_*` cho 030..034; ghi rõ trong test.md cơ chế enforce từng nhóm (M2=M1–M10 arch tests, M5=test_inv011..016, M6=test_inv017..021, M7=test_inv022..029, M9=test_m9_*).

### C2-02 (P3) — Layer-model thứ tự tầng dễ sai chữ
PLAN §M10-4 kiến trúc cuối: `USER/SYSTEM → UI/SDK/API → AUTONOMY CONTROL → ORCHESTRATOR → Workflow/Agent/Capability → Runtime Kernel → Tools/State/Events → Infra` — 7 tầng đếm: (1) UI/SDK/API, (2) Autonomy Control, (3) Orchestrator, (4) Workflow/Agent/Capability, (5) Runtime Kernel, (6) Tools/State/Events, (7) Infra.
→ **Resolve**: layer-model.md liệt kê đúng 7 tầng theo thứ tự trên (đánh số L1..L7), kèm bảng module thật của từng tầng.

### C2-03 (P3) — Constitution cần mục "Hệ quả"
Freeze có hệ quả quy trình: thay đổi INV phải qua ADR + M10 release gate A (INV violations = 0).
→ **Resolve**: constitution-1.0.md thêm mục "Hệ quả" — Gate A (release), ADR bắt buộc cho sửa INV, AIOS 2.0 cho renumber/breaking.

## Kết luận vòng 2
Các vấn đề đã resolve — **spec v2 đạt, được phép implement** (tạo docs/architecture/* + constitution + script đối chiếu).
