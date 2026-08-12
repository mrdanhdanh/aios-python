# Test — TASK-009

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Kết quả | **346 passed** (46 mới + 300 baseline) |
| Coverage | **95.30%** (ngưỡng 80%) |
| Git sạch | ✅ |

Test mới: test_capabilities (9), test_prompts (16), test_catalog (11), test_knowledge_graph (12), test_integration (1) + test_import.

## Lỗi phát hiện + fix (5)
1. **Fixture name conflict**: `g`/`cat` — pytest không inject khi tên test thiếu tham số → thêm tham số rõ ràng
2. **Self-loop neighbors**: logic cũ `ti if (tk,ti)!=key else tk` trả nhầm kind thay vì id
3. **In-index unpack đảo biến**: entry = (rel, source_kind, source_id) — đầu kia là source_id (không phải source_kind)
4. **Integration relation**: workflow dùng "requires" (không phải "uses") — assert đúng relation
5. **Thread-safe agent id trùng giữa 2 thread** (agent-0..49 ×2 = 50 unique, không phải 100) → thread_id prefix

## Đối chiếu AC (9 AC)
**9/9 PASS** — AC1 capability (bind/unbind/agents_using/thread-safe), AC2 prompt extract edge ({{}}/format spec/positional/triple), AC3 registry (semver latest, evaluations history), AC4 catalog (nested/None/key-no-search/sorted), AC5 graph (bidirectional, cascade, self-loop), AC6 imports, AC7 offline, AC8 integration flow, AC9 PLAN amend.

## Kết luận
- [x] **TẤT CẢ PASS (9/9 AC)** — M1 hoàn tất.
