# Review — TASK-023 (Memory Coordinator) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-14

## Kết luận
- [x] **APPROVED có điều kiện** — không có R1 (blocker). Điều kiện: resolve R2-1, R2-2 trong quá trình implement; R3-1..R3-4 cải thiện khi implement, không chặn.

## Kiểm chứng trọng tâm (đối chiếu code thật)
- (a) `ConversationMemory.get_messages(conversation_id, limit)` + `list_conversations(session_id)` tồn tại — ConversationSource khả thi
- (b) `ContextService.get_all(scope)` trả `dict[str, Any]`; `get_context` trả `Context.created` tz-aware — SessionSource khả thi; SHARED scope chỉ SessionMemory ghi
- (c) Eager DB creation không phá test (gitignored) nhưng có side-effect → R2-1
- (d) Module path `aios_core.kernel.services` đúng; allow-list theo pattern `test_inv_agents_import_allowlist`
- (e) `list[tuple[...]]` + `dict[MemoryKind, int]` hợp lệ với pydantic ≥ 2.10
- `arch_scan.py` đếm mọi Import node kể cả TYPE_CHECKING → resolution C2-01 bắt buộc

## Vấn đề
### R2 (major)
- **R2-1**: Eager DB creation chưa xử lý tại 2 fixture: `test_api.py:13-21` (override `conversation_db_path` nhưng thiếu `knowledge_db_path`) + `test_runtime_kernel.py:21-27` (`make_settings` không override memory). → Resolution: cập nhật `make_settings` + fixture `test_api.py` override cả 2 db; §8 thêm `test_runtime_kernel.py` (MOD).
- **R2-2**: `MemoryCoordinatorConfig.budget` type chưa rõ (MemoryBudgetSettings 6 field vs budget 4 kind). → Resolution: chốt `budget: MemoryBudgetSettings` — coordinator tự ánh xạ kind→category, ignore system/reserve.

### R3 (minor)
- **R3-1**: §8 Expected artifacts thiếu `test_runtime_kernel.py` (MOD) — gộp vào R2-1.
- **R3-2**: `estimate_tokens` tính trên content sau compress (pipeline order ngầm định) — ghi rõ 1 câu YC-7.
- **R3-3**: Allow-list external rộng (`sqlite3`, `json`, `uuid`, `itertools`) — thu hẹp khi implement (adapter chỉ dùng store API).
- **R3-4**: tasks.md T14 "coverage ≥ 95%" lệch AC9 "≥ 80% cứng (95% mục tiêu)" — đồng bộ wording.

## Resolution (ghi nhận — sẽ phản ánh trong implement)
- R2-1 → spec v4 §8 + tasks.md T13 (make_settings + fixture test_api override knowledge_db_path)
- R2-2 → spec v4 YC-4/YC-7 chốt `budget: MemoryBudgetSettings`
- R3-2 → spec v4 YC-7: estimate_tokens tính trên content SAU compress
- R3-3 → allow-list thu hẹp: bỏ sqlite3/json/uuid/itertools nếu adapter không dùng
- R3-4 → tasks.md T14 đồng bộ wording AC9
