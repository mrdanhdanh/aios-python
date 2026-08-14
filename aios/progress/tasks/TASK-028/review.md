# Review — TASK-028 (Parallel Scheduler) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-15

## Kết luận
- [x] **CHANGES REQUESTED** — 1 R1 (blocking: pin test §5.3) + 3 R2 + 3 R3.

## Kiểm chứng trọng tâm (đối chiếu code thật)
- (a) Gated runner ✓ — acquire_slot_wait blocking FIFO; ResourceUnavailableError → FAILED (reason chứa timeout); RUNNING-while-waiting đúng
- (b) 1-node plan ✓ — PlanNode name required (adapter truyền đủ); node_results key = node id
- (c) GraphResult nested pydantic OK ✓
- (e) Wiring cuối + singleton shared ✓
- (f) FailurePolicy str→enum convert ✓
- (g) cancel namespace khớp ✓

## Vấn đề
### R1 (blocking)
- **R1-1**: §5.3 pin test hỏng kép — exclude SLASH (no-op với rel dotted) + forbidden chứa execution_plan (mâu thuẫn §5.2 nới pin toàn dir).
  → **Resolution**: `dir_imports(kernel/scheduler, ["aios_core.kernel.services.execution"], exclude=["aios_core.kernel.scheduler.execution_runner"]) == []` (dotted, 1 module).

### R2 (major)
- **R2-1**: YC-3 comment "executor mặc định = GraphExecutor(state_service)" mâu thuẫn C2-06 v2.
  → **Resolution**: `GraphExecutor(state_service, settings=graph_settings)`.
- **R2-2**: `ResourceService(max_concurrent=1)` sai constructor — `ResourceService(ResourcesSettings(max_concurrent=1))` (mọi test site).
- **R2-3**: `list(self._permissions)` với None → TypeError → `list(self._permissions or [])`.

### R3 (minor)
- **R3-1**: §7 thiếu rows gnode giới hạn (C2-05 P2) + retry nhân đôi (C2-07 P2).
- **R3-2**: Thống nhất timeout 0.1s.
- **R3-3**: Allow-set gồm cả trunk `aios_core.kernel.graph`.

## Resolution ghi nhận (phản ánh trong spec v3.1 + implement)
- R1-1, R2-1..R2-3, R3-1..R3-3 → spec + tasks.md (T7 đã đúng)
