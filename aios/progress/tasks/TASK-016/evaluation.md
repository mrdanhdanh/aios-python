# Evaluation — TASK-016 (Architecture Hardening: Invariants + Reference)

> Ngày: 2026-08-13 | Chuỗi: Spec → Critique ×2 (23 vấn đề) → Review (CHANGES REQUESTED → R1 fix) → Implement → Test → **Evaluate**

## Kết quả test

- **502 passed + 2 skipped** (skipped = INV-001/002 — `agents/`/`tools/` chưa tồn tại, đúng thiết kế), coverage 95.96%
- 12 architecture tests mới: INV-003/004(+premise)/005(A+B)/006/007(hard)/009(4 business)/010 + helper 3 test
- AST pure scan: không import runtime → coverage không đổi

## Đối chiếu 10 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | architecture.md §7 — 10 INV + bảng enforce | ✅ §7 đầy đủ |
| AC2 | Control vs Execution Plane + dep 1 chiều + System Brain | ✅ §1.1 (sơ đồ 2 plane) + §3.1 (System Knowledge = System Brain) + dependency T5→T6→T7 |
| AC3 | Flow: Evaluation observer / KB vs KG / Context vs Memory / 3 vai | ✅ §3 + §3.1 + §3.2 + §3.3 |
| AC4 | ADR-0004: 4 INV chốt + rationale + gap sandbox | ✅ (không copy architecture.md) |
| AC5 | PLAN.md: link ADR + index 0001..0004 + Health→M4 | ✅ 2 chỗ sửa |
| AC6 | 12 test INV + rule B vi phạm test | ✅ 12 test pass + 2 skip |
| AC7 | Helper 2 tập, resolve relative, mọi Import node | ✅ 3 test helper pass |
| AC8 | evil.py → phát hiện | ✅ `test_arch_scan_detects_violation` |
| AC9 | pytest pass + bảng tiến độ cập nhật + git sạch | ✅ 502 pass; §4/§5 cập nhật 490 tests |
| AC10 | PROGRESS/LOG/STATS + commit | ✅ (sau commit này) |

**10/10 AC đạt.**

## Xử lý review R1-R5

- R1 (blocking SRC_ROOT): `parents[1] / "src"` + assert fail-fast ✅
- R2 (full dotted + 2-chiều): helper lưu full dotted; rule B điều chỉnh — cấm trần chính xác + provider cụ thể (2-chiều chặn nhầm `models.base` — đã phát hiện khi chạy test và sửa) ✅
- R3 (call-site AST Attribute): ✅ `ast.walk` tìm `_policy.evaluate`
- R4 (format docs): ✅ mermaid giữ, ADR format 0001-0003
- R5 (section 8 đồng bộ 4 business): ✅

## Bài học mới

1. 2-chiều dot-boundary match (`mod.startswith(target + ".")`) chặn NHẦM module con hợp lệ khi target là package trần cấm (models vs models.base) — cấm trần phải là match chính xác (==), cấm nhánh mới dùng prefix.
2. `from aios_core.models import X` (re-export) chỉ có thể chặn bằng match trần chính xác — không thể dùng prefix.
3. AST tests chạy nhanh (0.4s) — phù hợp enforce mọi lúc.

## Kết luận

**TASK-016 ĐẠT — 10/10 AC, 502 tests pass, 12 architecture tests bảo vệ 10 invariants, git sạch sau commit.**
