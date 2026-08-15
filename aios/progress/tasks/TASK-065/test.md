# TASK-065 — Test + Evaluation (Runtime Hardening)

## Test — `tests/test_hardening.py` **18/18 pass**
- 12 FailureKind đủ (AC1) + validation trùng id/kind lạ (AC7)
- Runner bắt exception per-scenario (AC4) + outcome fields (AC5)
- **12 scenario end-to-end thật** (AC3 — vượt mức 8/12): model, tool, agent, process (crash→resume từ snapshot, node done không chạy lại), network, db, plugin, worker_timeout, resource, memory_corruption, checkpoint, event_consumer
- Matrix phủ 12 kind (AC3)

## Full suite: **1855 passed** (baseline 1815 + 40 Phase 2) — không phá M1–M9 (AC6).

## Evaluation — 8/8 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 12 FailureKind | ✅ |
| AC2 detect→contain→recover→resume mỗi scenario | ✅ |
| AC3 ≥8/12 end-to-end | ✅ (12/12) |
| AC4 runner không crash suite | ✅ |
| AC5 outcome fields | ✅ |
| AC6 không sửa 9 services | ✅ (chỉ hook/test double) |
| AC7 validation | ✅ |
| AC8 DoD | ✅ |

## Bài học
1. **Runner contract của ExecutionService nhận `PlanNode` object** (không phải string id) + chạy trong thread khi timeout_s > 0 → exception trong thread bị đóng hộp, không lan ra main. Scenario phải assert qua kết quả (status/reason) không phải exception.
2. **Tool.run() không raise** — bắt exception → ToolOutput(ok=False). Detect phải qua output, không try/except.
3. **ConversationMemory mở connection mỗi lần + recreate bảng** khi khởi tạo — corruption detect phải dùng instance cũ.
