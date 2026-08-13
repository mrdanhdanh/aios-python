# Evaluation — TASK-014 (M2-P4: Tools 6 loại + Tool Registry + capability binding)

> Ngày: 2026-08-13 | Chuỗi: Spec → Critique ×2 (27 vấn đề) → Review (APPROVED + 3 lưu ý) → Implement → Test → **Evaluate**

## Kết quả test

- **622 passed, 0 skipped** (baseline 549 + 73 mới), coverage **96.15%**
- 73 test mới: tools_base 13, tool_stubs 22, tool_registry 14 + architecture allow-list tools/
- Allow-list `tools/` PASS — tools/ chỉ import metadata + pydantic + stdlib; urllib module-con check (R3/AST)

## Đối chiếu 14 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | Package + exports + allow-list + INV giữ nguyên | ✅ `test_inv_tools_import_allowlist` pass; 0 skip |
| AC2 | Contract models + template run (mismatch, _run raise, error → duration 0.0) | ✅ 4 test |
| AC3 | PythonTool (ast.parse no-exec, marker VẪN tồn tại, execute flag) | ✅ 7 test |
| AC4 | DockerTool (3 actions, unsupported, invalid arg) | ✅ 3 test |
| AC5 | RestTool (method/url validate, no network) | ✅ 4 test |
| AC6 | McpTool (servers validate/inject, unknown server/method) | ✅ 6 test |
| AC7 | ShellTool (no-exec marker, shell scope bắt buộc) | ✅ 4 test |
| AC8 | GitTool (status/branch/log, unsupported) | ✅ 3 test |
| AC9 | Gate invariants (deny/none/raise fail-closed, scope cross-check) | ✅ 8 test tham số hóa |
| AC10 | Events (started/finished symmetric, error finished, sink best-effort/none) | ✅ 5 test |
| AC11 | Registry (duplicate, unknown, capability, available, concurrent RLock) | ✅ 8 test |
| AC12 | Binding (real CapabilityRegistry, idempotent lần 2 = 6, unknown raises, swap) | ✅ 4 test |
| AC13 | Factory + metadata (6 tool thứ tự cố định, semver, MIT) | ✅ 3 test |
| AC14 | Determinism + toàn bộ pytest + coverage | ✅ `test_tools_deterministic_repeat_run` + 622 pass |

**14/14 AC đạt.**

## Xử lý critique ×2 (27) + review (3 lưu ý)

- 17 + 10 vấn đề resolved: no-exec assertion đúng chiều (C1-01), gate raise fail-closed (C1-02/C2-01), _run(input, context) (C1-03), urllib AST check (C1-04/R3), invalid argument convention (C1-05/C2-05), cấm scope rỗng (C1-06), no-syscall global test (C1-07/C2-03), renegotiate scope P4 (C1-08), McpTool validate (C1-10/C2-08), bind return semantics (C1-11), duration_s error path (C1-12/R1), finished capabilities (C1-13), thread-safe contract + test (C1-14/C2-04), tool_id trước gate (C1-15/C2-02), no PermissionService wire (C1-16), AC11 định nghĩa (C1-17), không rollback (C2-06), perf_counter (C2-07), sink fallback (C2-09), constructor thống nhất (C2-10)
- Review: R1 duration_s theo C1-12 ✅, R2 gate-raise test ✅, R3 urllib AST walk ✅, R4 output trước finished ✅, R5 bind ngoài lock ✅, R6 swap test ✅

## Bài học mới

1. Base class có class attribute `id`? KHÔNG — `self.id` set trong `__init__` từ `tool_type` — class attrs chỉ là hằng số bất biến
2. Message validate phải khớp regex test (mcp "server ... methods" không chứa "servers")
3. Monkeypatch no-syscall chạy được vì tests/ không bị allow-list scan
4. Tool thứ 7 swap test — register + bind → tools_for cập nhật, contract không đổi

## Kết luận

**TASK-014 ĐẠT — 14/14 AC, 622 tests pass, 0 skip (allow-list tools/ bật), coverage 96.15%, git sạch sau commit.**
