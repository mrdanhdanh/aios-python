# TASK-067 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P1) — ToolGuard chặn "trước khi tool chạy" phải đo được
Không chỉ assert decision — phải chứng minh tool._run KHÔNG được gọi.
→ **Resolve**: Test dùng tool với counter trong _run; guard deny → counter == 0.

### C2-02 (P2) — ASK_HUMAN từ policy — gọi lại sau approve?
→ **Resolve**: SafetyEnforcer.evaluate chỉ trả ASK_HUMAN; việc gọi lại với approval là của caller (không tự loop). Test: ASK_HUMAN không tự ALLOW.

### C2-03 (P3) — Risk bảng nên tách hằng số
→ **Resolve**: `RISK_TABLE: dict[str, int]` + `SENSITIVE_TARGETS: set[str]` module-level — dễ test/điều chỉnh.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
