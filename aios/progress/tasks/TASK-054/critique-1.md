# TASK-054 — Critique vòng 1 (critic độc lập)

## C1-01 (P1) — Usage tracking: ai gọi `start_goal`?
Governor giữ budget theo goal_id — nhưng ai reset? Nếu loop quên reset, budget sai.
→ **Resolve**: governor `check_action(goal_id, ...)` tự khởi tạo budget entry nếu chưa có (lazy init, now = clock()). Loop vẫn gọi `start_goal()` để rõ ràng (idempotent — không reset nếu đã tồn tại). Test cả 2 đường.

## C1-02 (P2) — RiskClass có 5 cấp nào?
Spec nói "5 cấp" nhưng không liệt kê.
→ **Resolve**: READ, EDIT, COMMIT, DEPLOY, DELETE (deploy = push production; delete = impossible). Mỗi cấp map 1 hành động mẫu. DELEGATE không phải risk class riêng — delegate action dùng risk của hành động thật; max_parallel_agents check theo usage.parallel_agents.

## C1-03 (P2) — STOP vs PAUSE: khác nhau thế nào khi vượt budget?
→ **Resolve**: STOP = không tiếp tục được (budget cạn — terminal cho goal); PAUSE = tạm dừng (parallel agents đang đầy — có thể chờ). Budget exceeded → STOP; parallel đầy → PAUSE.

## C1-04 (P3) — REPLAN/ROLLBACK khi nào?
Governor chỉ quyết định — ai trigger replan/rollback?
→ **Resolve**: governor trả REPLAN/ROLLBACK khi world thay đổi (loop gọi `world.changed()` — injectable predicate) hoặc verify fail nhiều lần; loop thực thi (gọi planner.replan / recovery). Governor không tự thực thi — chỉ quyết định (đúng INV-030 tinh thần: quyết định qua governor, thực thi qua loop).

## C1-05 (P3) — Reason format
→ **Resolve**: reason = `f"{category}.{limit} exceeded (used {used}/{limit})"` — deterministic, test được bằng prefix.

## Kết luận
P1-P2 resolve; P3 ghi rõ ngữ nghĩa. Vòng 2 kiểm tra.
