# TASK-056 — Long-Horizon Execution (M9-P2)

## Mục tiêu
AIOS chạy được 30p/2h/8h/nhiều ngày mà không phụ thuộc context window (PLAN §M9-17): `Goal → Execution Session → Checkpoint → Context Compaction → Persisted State → Resume`. Checkpoint: `Completed · Current · Pending · State` (§M9-18). **INV-032: execution dài hạn phải checkpoint/resume được** (arch test).

## Phạm vi
- `autonomous/long_horizon.py`: `LongHorizonManager` — ExecutionSession (SQLite persist), checkpoint(session, completed, current, pending, state), resume(session) → Checkpoint, compact_note (persisted structured notes)
- `contracts.py`: `ExecutionSession`, `Checkpoint` (session_id, completed[], current, pending[], state dict, notes[], at)

## Input/Output
- In: `create_session(goal_id)`; Out: session id + checkpoint flow
- Fail-closed: resume session không có checkpoint → raise (không tự bịa trạng thái)

## Tiêu chí chấp nhận (AC)
1. `create_session` tạo session persist (SQLite), status ACTIVE
2. `checkpoint()` lưu completed/current/pending/state/notes — overwrite checkpoint mới nhất (idempotent)
3. **INV-032**: `resume(session_id)` trả checkpoint mới nhất — process chết → restart → load → continue (không chạy lại completed)
4. `compact_note(session_id, note)` — persisted structured notes (context compaction — không phụ thuộc context window)
5. Session lifecycle: ACTIVE → COMPLETED/FAILED (terminal)
6. Checkpoint count + timestamps (audit)
7. Cross-instance: manager mới đọc được session + checkpoint cũ (SQLite)
8. Resume từ checkpoint giữa chừng: completed 12, current 13 → resume trả đúng
9. Contract `extra=forbid`
10. Unit tests coverage ≥ 90% (behavioral)

## Amend (critique ×2 resolve)
- C1-01: checkpoint ghi trong 1 transaction (atomic)
- C1-02: completed: list[str], current: str, pending: list[str], state: dict, notes: list[str] (JSON)
- C1-03: bảng `autonomous_sessions` (1 row/session — checkpoint mới nhất) + `autonomous_checkpoints` (history, bounded 50)
- C1-04: session status ACTIVE/RESUMED/COMPLETED/FAILED
- C1-05: notes bounded 200 (FIFO)
- C2-01: resume chỉ khi ACTIVE/RESUMED — terminal → raise
- C2-02: current default ""; completed ∩ pending = ∅
- C2-03: goal_id field (không FK cứng)
