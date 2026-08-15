# TASK-051 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Keyword-based: keyword không khớp → plan rỗng?
Objective "cải thiện độ ổn định" không chứa keyword nào → steps rỗng → raise? Hay 1 step mặc định?
→ **Resolve**: objective không khớp keyword nào → 1 step mặc định `capability="python"` (mô tả = objective) — không raise (goal hợp lệ nhưng không map được). raise chỉ khi capabilities rỗng.

## C2-02 (P2) — Capability yêu cầu của step ∉ capabilities input?
Keyword map ra [python, filesystem] nhưng capabilities input chỉ có [docker] → step dùng capability không có sẵn?
→ **Resolve**: filter: step chỉ sinh nếu ít nhất 1 capability của map ∈ capabilities input (nếu map rỗng sau filter → dùng keyword khác; hết → mặc định lấy capability đầu tiên của input). Ghi rõ trong spec.

## C2-03 (P3) — replan giữ nguyên completed steps?
→ **Resolve**: replan nhận `completed_step_ids: list[str]` — steps mới đánh dấu những step đã hoàn thành (giữ nguyên tiến độ).

## Kết luận
Resolve xong — spec đủ chặt để implement.
