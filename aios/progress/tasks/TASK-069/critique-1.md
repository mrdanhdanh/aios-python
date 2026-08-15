# TASK-069 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-069.

## Các vấn đề

### C1-01 (P1) — Nguồn dữ liệu thật phải rõ ràng từng SLO
"Đọc từ metrics/audit" mơ hồ — SLO nào lấy ở đâu?
→ **Resolve**: Bảng mapping trong spec:
- runtime_availability: MetricsService workflow success/(success+failure) hoặc doctor status
- execution_success: metrics workflow COMPLETED/(COMPLETED+FAILED+CANCELLED)
- recovery_success: audit count RECOVERY_* success/fail (M2 events)
- checkpoint_durability: state snapshot_saved count không lỗi / total
- policy_enforcement: audit PERMISSION_DENIED hợp lệ / total policy decisions
- event_delivery: event bus published vs handler errors
- api_availability: healthcheck status
- 5 gates: policy_bypass (audit ERROR_OCCURRED với payload bypass? → dùng audit PERMISSION_DENIED trái policy hoặc 0 — định nghĩa: count PERMISSION_DENIED là chặn đúng; bypass = ERROR type policy.bypass — thực tế không có → mặc định 0, có thể inject)

### C1-02 (P2) — Metrics nguồn có thể rỗng → đừng fail oan
DB mới: execution_success 0/0 → chia 0.
→ **Resolve**: RATIO với denominator = 0 → SKIPPED (không fail release); ABSOLUTE_ZERO luôn kiểm tra (0 = pass).

### C1-03 (P2) — release_ready cần phân biệt SKIPPED
SKIPPED không chặn release (thiếu dữ liệu ≠ vi phạm).
→ **Resolve**: Status 3 giá trị PASS/FAIL/SKIPPED; release_ready = không FAIL (SKIPPED cho phép).

### C1-04 (P3) — CLI output ổn định
→ **Resolve**: Bảng cột padding cố định + verdict dòng cuối "RELEASE READY/NOT READY (n failures)".

## Kết luận
Resolve vào spec v2 (mapping nguồn, SKIPPED, chia 0).
