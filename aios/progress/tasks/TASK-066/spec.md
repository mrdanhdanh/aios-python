# TASK-066 — M10-F3: Durable Execution 1.0

## Mục tiêu
PLAN §M10-13/14: checkpoint/snapshot/resume (M1/M9) thành **production-grade guarantee**: crash → load journal → verify → resume từ node chưa xong (KHÔNG chạy lại node đã xong trừ khi policy yêu cầu). Idempotency classification: `Read → safe retry · Idempotent write → retry · Non-idempotent write → approval/transaction/compensation`.

## Phạm vi
- `kernel/durability.py`:
  - `ExecutionJournal` (SQLite): ghi mỗi node `{execution_id, node, status: pending/running/done, payload}` + `journal_start/verify/resume`
  - `JournaledExecutor`: wrapper quanh ExecutionService — trước node: journal pending; sau node: journal done; crash → `resume(execution_id)` verify journal → tiếp tục node chưa done
  - `IdempotencyClassifier`: phân loại op `read / idempotent_write / non_idempotent_write` theo danh sách khai báo + quyết định `retry / approve / compensate` (non-idempotent → KHÔNG tự retry — phải approve)
  - `DurabilityPolicy`: cho phép chính sách "rerun từ đầu" nếu policy yêu cầu (mặc định: resume)
- Wiring: `RuntimeKernel.create` optional journal (settings.durability) — không bắt buộc thay ExecutionService
- Tests: crash mô phỏng giữa node 2/4 → resume → node 1–2 không chạy lại

## Ngoài phạm vi
- Không thay thế ExecutionService hiện có (journal là lớp tăng cường — opt-in)
- Không distributed lease (M7 đã có)

## Input
- `kernel/services/execution.py` (snapshot/resume hiện có), `kernel/services/state.py`, `kernel/events.py` (SNAPSHOT_SAVED)

## Output
- `backend/src/aios_core/kernel/durability.py` + `tests/test_durability.py` + config `DurabilitySettings`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | Journal ghi đủ trạng thái mỗi node (pending/running/done) + persist SQLite | Unit test |
| AC2 | Crash giữa node (mô phỏng raise) → `resume()` load journal → verify → tiếp tục node chưa done; node đã done KHÔNG chạy lại (count event) | Test end-to-end (ExecutionService thật, workflow 4 node) |
| AC3 | Journal corrupt/thiếu → resume fail-closed (raise, không chạy bừa) | Test |
| AC4 | IdempotencyClassifier: read → retry an toàn; idempotent_write → retry; non_idempotent_write → approve (không tự retry) | Test 3 nhánh |
| AC5 | Non-idempotent op bị retry tự động → chặn (raise/deny) | Test |
| AC6 | DurabilityPolicy: mặc định resume; policy rerun → chạy lại từ đầu (có ghi chú) | Test |
| AC7 | Config `DurabilitySettings` (enabled, db_path, policy) + config.yaml | Test config |
| AC8 | Regression full suite pass | pytest full |
| AC9 | Đóng DoD | checklist |

## Ghi chú
- Journal = bảng `execution_journal` riêng (không đụng state service) — verify bằng đối chiếu journal với state snapshot.
- Node done = node có journal status done + snapshot tương ứng.
