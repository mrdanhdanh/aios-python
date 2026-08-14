# Critique vòng 2 — TASK-028 (Parallel Scheduler)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
C1-01 ⚠️ MỘT PHẦN (test tường minh thiếu → C2-02 P1) · C1-02 ⚠️ MỘT PHẦN (YC-5 wiring thiếu graph_settings → C2-01 P1) · C2-01 ✅ (thiếu test retry → P3-08) · C2-02 ⚠️ MỘT PHẦN (không tường minh inject → C2-06 P2) · C2-03 ❌ CHƯA ÁP DỤNG (exclude vẫn slash → C2-03 P1) · C2-04 ✅ · C2-05 ⚠️ MỘT PHẦN (test cancel thiếu → C2-04 P2) · C2-06 ❌ CHƯA ÁP DỤNG (pin chưa nới → C2-03 P1) · C3-01 ✅ · C3-02 ❌ (§7 thiếu row → C2-07 P2) · C3-03 ❌ (gnode chưa xử lý → C2-05 P2) · C3-04 ❌ (P3-03) · C3-05 ⚠️ (P3-04) · C3-06 ✅

## Mục B — Vấn đề mới

### P1
- **C2-01**: YC-5 wiring thiếu `graph_settings=settings.graph` → `schedule_plan` mặc định không tiêu thụ `default_failure_policy`. → **Resolution**: thêm vào wiring + AC10 assert `scheduler._graph_settings is settings.graph`; convert str → FailurePolicy tại call-site.
- **C2-02**: Test C1-01 tường minh thiếu (adapter + max_concurrent=1 → FAILED "resource unavailable"). → **Resolution**: thêm test vào YC-4/AC8.
- **C2-03**: §5.2 pin execution_plan "CHỈ execution_runner.py" mâu thuẫn annotation schedule_plan; §5.3 exclude slash → vô hiệu. → **Resolution**: nới pin `execution_plan` TOÀN DIR; §5.3 sửa exclude dotted `aios_core.kernel.scheduler.execution_runner` + chỉ pin `services.execution`.

### P2
- **C2-04**: Test cancel-while-waiting thiếu + retries detail. → **Resolution**: thêm test (retries ≥ 1 → CANCELLED; ghi rõ retries=0 → FAILED timeout).
- **C2-05**: `gnode:{node.id}` — runner contract không mang execution_id. → **Resolution (a)**: giữ `gnode:{node.id}` + ghi giới hạn §7 (poisoning nếu cancel ngoài; re-run clobber — không hỗ trợ v1).
- **C2-06**: AC3/YC-3 không tường minh inject executor max_parallel=3; executor mặc định không nhận graph_settings. → **Resolution**: ghi tường minh inject; executor mặc định = `GraphExecutor(state_service, settings=graph_settings)`.
- **C2-07**: Retry nhân đôi + thread leak chưa vào §7. → **Resolution**: thêm row §7 (khuyến nghị retries=0 với adapter; timeout-leak document).

### P3
- **P3-01**: allow-list ghi rõ liệt kê đủ submodule graph (prefix filter pattern test_inv_graph).
- **P3-02**: import `kernel.services` trần không nằm allow — bắt buộc import đường dẫn đầy đủ (.state/.resource).
- **P3-03**: ghi giới hạn no_private_access v1 (Name._attr; a.b._c lọt — bù behavioral + review).
- **P3-04**: determinism test dùng ResourceService instance mới mỗi run.
- **P3-05**: §7 note default config = gate no-op.
- **P3-06**: §7 scope cancel v1 (graph-level flag; gnode 1-node plan không cancel in-flight).
- **P3-07**: test timeout dùng barrier-poll thay sleep + timeout 0.1s (tránh flaky).
- **P3-08**: test `slots_acquired == 2` với retries=1.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C2-01..C2-03 (P1) + C2-04..C2-07 (P2) + P3 → spec v3. Sau vòng này **approve** (không cần vòng 3 — không đổi kiến trúc).
