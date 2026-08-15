# TASK-051 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Capabilities rỗng → raise là quá cứng?
Nếu goal đơn giản không cần capability (VD: goal "ghi chú") thì raise sẽ chặn. Nhưng AIOS triết lý "mọi hành động qua capability" — giữ raise nhưng nới: capabilities rỗng nhưng steps rỗng → raise; capabilities rỗng + objective đơn giản (không có keyword hành động) → plan 1 step "noop"? Không — phức tạp.
→ **Resolve**: giữ fail-closed: capabilities rỗng → raise `PlanError`. Goal không cần hành động không thuộc scope M9 (goal luôn hướng hành động).

## C1-02 (P2) — Steps sinh từ đâu (deterministic)?
Spec không nói thuật toán sinh steps. Cần xác định: keyword-based decomposition (objective chứa "fix" → step capability "python"; "test" → "python"; "docs" → "filesystem")?
→ **Resolve**: v1 dùng keyword-based: map từ điển `ACTION_KEYWORDS = {fix: [python, filesystem], test: [python], docs: [filesystem], review: [filesystem], deploy: [docker]...}`; mỗi keyword khớp → 1 step (description = objective + keyword). Deterministic, sorted. Ghi rõ trong spec.

## C1-03 (P2) — dependencies giữa steps?
AC2 yêu cầu mỗi step có dependencies — nhưng keyword-based thì step nào phụ thuộc gì?
→ **Resolve**: v1 dependencies = [] cho mọi step (độc lập). Trường dependencies tồn tại cho tương lai + test replan. Ghi rõ.

## C1-04 (P3) — rollback.enabled theo risk nào?
Spec: "False khi risk chứa delete". Risk table ở TASK-054 (governor) — planner đọc risk từ đâu?
→ **Resolve**: planner nhận `risk_table: dict[RiskClass, str]` injectable (mặc định từ constants chung trong contracts.py — dùng chung với governor). Đồng bộ nguồn constants.

## C1-05 (P3) — Estimate tổng ≤ max_duration?
AC7 mơ hồ — estimate thế nào nếu không có duration từng step?
→ **Resolve**: v1: mỗi step có `estimated_duration_s` (mặc định 60s); tổng > max_duration_s → plan vẫn sinh nhưng đánh dấu `over_budget: true` (không raise — replan có thể cắt). Bỏ cụm "không vượt".

## Kết luận
P1 giữ fail-closed; P2 xác định thuật toán keyword-based; P3 đã resolve. Vòng 2 kiểm tra.
