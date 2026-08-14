# Critique vòng 1 — TASK-028 (Parallel Scheduler)

**Critic**: subagent critic | **Ngày**: 2026-08-15 | **Spec phản biện**: v1

## Đánh giá chung
Spec kỹ (wrap-vs-replace có căn cứ, allow-list, determinism); kiểm chứng code: `acquire_slot_wait(timeout=None) -> bool`, `ExecutionService.execute(plan, runner)`, singleton container, baseline 1055. 2 P1 + 6 P2 + 6 P3.

## P1 — Blockers

### C1-01: ExecutionServiceRunner + max_concurrent hữu hạn = FAILED chắc chắn
- ExecutionService `_run()` dùng `acquire_slot()` NON-blocking nội bộ (execution.py L205-212). Gate ngoài giữ slot duy nhất + max_concurrent=1 → acquire_slot trong ExecutionService trả False → mọi node FAILED — không phải "hơi conservative".
- **Resolution (chọn a)**: ghi nhận hard limitation + test tường minh: adapter + max_concurrent=1 → node FAILED reason "resource unavailable", gate release sạch, `stats()["running"]==0`.

### C1-02: `schedule_plan` không tiêu thụ `GraphSettings.default_failure_policy` — mâu thuẫn evaluation 027
- **Resolution**: thêm `graph_settings: GraphSettings | None = None` vào `GraphScheduler.__init__` (wiring truyền settings.graph); `schedule_plan(..., failure_policy: FailurePolicy | None = None)` → resolve `graph_settings.default_failure_policy` khi None.

## P2 — Major
- **C2-01**: `slots_acquired` field chết/sai semantic với retries. → **Resolution**: định nghĩa "tổng số lần acquire THÀNH CÔNG của node (tính cả retry)" + tăng dưới lock + test (retries=1 → 2); `resource_wait_ms` = tổng thời gian chờ (không phải attempt cuối).
- **C2-02**: AC3 test max_parallel=3 nhưng scheduler không nhận graph settings → executor default max_parallel=1 → fail. → **Resolution**: AC3 inject `executor=GraphExecutor(state, GraphSettings(max_parallel=3))`; e2e dùng `Settings(resources=max_concurrent=2, graph=max_parallel=3)`; ghi chú §7: default config = gate no-op.
- **C2-03**: `exclude` trong dir_imports sai dạng (slash vs dotted). → **Resolution**: dùng `exclude=["aios_core.kernel.scheduler.execution_runner"]` (dotted) hoặc loop per-file.
- **C2-04**: literal `execution_service.execute(` vs pseudocode `self._execution.execute(`. → **Resolution**: đổi thuộc tính thành `self.execution_service` + gọi `self.execution_service.execute(plan, ...)`.
- **C2-05**: Cancel-while-waiting không test + default None làm cancel vô hiệu vô hạn + GraphScheduler thiếu cancel. → **Resolution**: thêm test (max_concurrent=1, 2 node độc lập, slot giữ barrier → cancel → node chờ CANCELLED ≤ timeout 0.05, pending()==0); ghi rõ trade-off default None; thêm `GraphScheduler.cancel(execution_id)` delegate.
- **C2-06**: Pin execution_plan chỉ execution_runner.py xung đột annotation `schedule_plan`. → **Resolution**: nới pin `aios_core.kernel.execution_plan` cho TOÀN dir (contracts thuần); giữ pin `kernel.services.execution` chỉ execution_runner.py.

## P3 — Minor
- **C3-01**: Topology timeout test — dùng {X,Y,Z} độc lập (max_parallel=3, max_concurrent=1) + Y→W; X giữ slot barrier, Y/Z timeout FAILED, W BLOCKED, X SUCCEEDED, graph FAILED, stats running==0, pending==0.
- **C3-02**: Retry nhân đôi (retries+1)² qua adapter + daemon thread leak — ghi chú §7 khuyến nghị retries=0 khi dùng adapter + document timeout-leak.
- **C3-03**: Namespace `gnode:{node.id}` xung đột giữa runs + cancel-flag poisoning → **Resolution**: `gnode:{execution_id}:{node.id}`.
- **C3-04**: no_private_access giới hạn (bỏ sót a.b._c) — ghi giới hạn v1.
- **C3-05**: AC12 loại trừ thêm `resource_stats` HOẶC determinism test dùng service instance mới mỗi run (khuyến nghị cách 2).
- **C3-06**: Đảo thứ tự `slots_held -= 1` rồi mới `release_slot()` (trong finally, if acquired); ghi chú peak_slots_used = slot scheduler giữ ≠ stats().running.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C1-01, C1-02 (P1) + C2-01..C2-06 (P2) + P3 → spec v2, rồi critique vòng 2.
