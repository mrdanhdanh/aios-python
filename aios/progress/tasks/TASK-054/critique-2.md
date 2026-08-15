# TASK-054 — Critique vòng 2 (critic độc lập)

## C2-01 (P2) — Budget entry leak (goal không bao giờ kết thúc)
Nếu budget entry không được xóa, memory phình.
→ **Resolve**: `end_goal(goal_id)` xóa entry; loop gọi end_goal khi goal kết thúc (final). Test: check_action sau end_goal → lazy-init mới (fresh budget).

## C2-02 (P2) — `usage` contract: field nào?
→ **Resolve**: `UsageSnapshot(steps: int, llm_calls: int, cost: float, duration_s: float, tool_calls: int, retries: int, parallel_agents: int)` — extra=forbid; loop tự cập nhật sau mỗi Act (actor trả usage delta → loop cộng dồn → check lần sau).

## C2-03 (P3) — Risk table cấu hình từ settings hay constants?
→ **Resolve**: `risk_table: dict[RiskClass, str]` injectable, mặc định từ `AutonomousRiskSettings` (config) — nhưng constants chung trong contracts.py cho planner đọc (C1-04 TASK-051). Đồng bộ: governor nhận risk table qua constructor, planner nhận riêng (cùng nguồn mặc định).

## C2-04 (P3) — world.changed() predicate mặc định?
→ **Resolve**: mặc định = `lambda: False` (không replan trừ khi injected). Loop/world wiring quyết định.

## Kết luận
Resolve xong — spec đủ chặt để implement.
