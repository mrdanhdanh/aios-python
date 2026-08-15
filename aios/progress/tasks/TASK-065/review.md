# TASK-065 — Review (trước implement)

> Reviewer (tự). Review spec v2 sau critique ×2.

## Đánh giá
- Failure Matrix 12 loại đúng PLAN §M10-12; mục tiêu detect→contain→recover→resume. ✅
- Hook-based inject (không sửa service) — an toàn cho production. ✅
- Đo lường cụ thể (checkpoint count, event count) — chống pass giả. ✅

## Yêu cầu
1. **R1**: KHÔNG sửa `kernel/services/*` — mọi fault qua hook/test double.
2. **R2**: Runner `run_all()` bắt exception từng scenario (một scenario fail không crash suite) — outcome FAIL kèm lý do.
3. **R3**: 12 FailureKind khớp đúng tên PLAN: model, tool, agent, process, network, db, plugin, worker_timeout, resource, memory_corruption, checkpoint, event_consumer.
4. **R4**: Test 8/12 end-to-end bắt buộc; 4 còn lại (db, memory_corruption, network, agent) có scenario chạy được ở mức hook (không bắt buộc full resume).

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép implement.
