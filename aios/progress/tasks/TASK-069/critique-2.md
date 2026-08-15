# TASK-069 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — Policy bypass đo thế nào khi không có event "bypass"?
Hệ thống không phát event policy.bypass (đúng — bypass bị chặn). Đo "0" mà không có nguồn = pass giả.
→ **Resolve**: policy_bypass gate = count `ERROR_OCCURRED` có payload chứa "bypass" + (nguồn phụ) số lần tool gọi khi policy deny — thực tế mặc định 0 + cho phép inject metrics trong test. Ghi chú: đây là "canary" đo lường gián tiếp — TASK-070 security baseline bổ sung nguồn vững hơn.

### C2-02 (P3) — Event delivery metric
→ **Resolve**: event_delivery ratio = (published - handler_failures)/published; handler_failures đếm từ EventBus (subscribe handler raise). Nếu chưa có counter → mặc định 1.0 + injectable.

### C2-03 (P3) — Contract-breaking release gate
→ **Resolve**: dùng `ContractChecker.check_all().breaking_count` (TASK-064) — nguồn thật, không cần inject.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
