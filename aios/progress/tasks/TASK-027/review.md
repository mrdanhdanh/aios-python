# Review — TASK-027 (Execution Graph) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-15

## Kết luận
- [x] **APPROVED có điều kiện** — 0 R1; 2 R2 (bắt buộc trong implement) + 7 R3.

## Kiểm chứng trọng tâm (đối chiếu code thật)
- `validate_dag` duck-typed — `_DagView` adapter khả thi; AST gate literal trong cả 2 file ✓
- `container.register(StateService, ...)` SINGLETON + resolve cache instance → shared instance đảm bảo (AC11) ✓
- `update_state` shallow merge giữ reference ✓; worker gán key pre-init GIL-atomic ✓ (nodes) — **results cần pre-init → R2-1**
- `get_state` deepcopy TRẦN không fallback — note C2-12 sai → R2-2
- Env override `AIOS_GRAPH__MAX_PARALLEL` khả thi ✓

## Vấn đề
### R2 (major)
- **R2-1**: `results: {}` không pre-init → worker insert key → dict resize → `get_state` deepcopy race RuntimeError.
  → **Resolution**: pre-init `results: {id: None for id in node_ids}` (protocol no-resize đồng nhất).
- **R2-2**: Note C2-12 sai — `get_state` deepcopy TRẦN (không fallback repr; `_safe_deepcopy` chỉ trong `snapshot()`).
  → **Resolution**: sửa note "get_state deepcopy trần (snapshot() mới có fallback repr); 028 đọc result qua GraphResult"; test persist dùng giá trị deepcopy-able.

### R3 (minor)
- **R3-1**: `cancel()` dùng key `f"graph:{id}"` — ghi chú.
- **R3-2**: `settings=None` → `settings = settings or GraphSettings()` trước khi đọc.
- **R3-3**: Main join toàn bộ futures (shutdown(wait=True)) trước khi áp policy — ghi rõ.
- **R3-4**: TRANSITIONS PENDING có RUNNING (dead transition — giữ vì C1-02) — ghi chú.
- **R3-5**: Test FAIL_FAST + queued cùng wave: D queued vẫn chạy (policy áp ranh giới wave) — thêm test chốt.
- **R3-6**: cancel-before-execute không ghi state (get_state → None) — ghi rõ.
- **R3-7**: Xóa note "sửa block register services" (container đã singleton); đồng bộ comment metadata plan_ref/request_ref.

## Resolution ghi nhận (phản ánh trong spec + implement)
- R2-1/R2-2 → spec v3.1 + implement (pre-init results; note sửa)
- R3-1..R3-7 → spec + implement
