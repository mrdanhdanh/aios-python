# Evaluation — TASK-013 (M2-P3c: Assistants + Safety Layer + System Doctor)

> Ngày: 2026-08-13 | Chuỗi: Spec → Critique ×2 (25 vấn đề) → Review (CHANGES REQUESTED R1.1/R1.2) → Implement → Test → **Evaluate**

## Kết quả test

- **549 passed, 0 skipped** (baseline 502 + 47 mới; INV-001/002/allow-list tự bật và PASS — không còn skip), coverage **96.03%**
- 47 test mới: agents_base 9, coder 11, doctor 12, system_doctor 7, registry 8 + architecture allow-list

## Đối chiếu 12 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | Package + exports + INV compliance (INV-001/002 hết skip + allow-list) | ✅ 0 skip, `test_inv_agents_import_allowlist` pass |
| AC2 | Base handle + event contract (started/finished, best-effort, empty text, error path) | ✅ 6 test |
| AC3 | General deterministic + model optional + fallback | ✅ 4 test (MockModel responses) |
| AC4 | Coder happy path (ast.parse, test_reports, history 7 bước) | ✅ 2 test + escape quotes |
| AC5 | Coder Self-Fix loop (feedback, max_rounds, ValueError) | ✅ 4 test |
| AC6 | Coder error path (handle bắt → status=error, không propagate) | ✅ 1 test |
| AC7 | Doctor pipeline (symptom→KB→risk→recommendation) | ✅ 3 test + longest-match |
| AC8 | Safety Layer invariants (a/b/c/d + b∩d + danger-only) | ✅ tham số hóa + 2 test riêng |
| AC9 | Doctor KB inject + validate + KB-miss cautious + deterministic | ✅ 4 test |
| AC10 | SystemDoctor deterministic (score, invalid probe, raise, None) | ✅ 7 test |
| AC11 | Registry (register/get/list/duplicate/unknown + concurrent RLock) | ✅ 7 test |
| AC12 | Tích hợp AgentSelector thật (4 intent) + 0 skip + coverage ≥80% | ✅ `test_integration_with_agent_selector` + 0 skip |

**12/12 AC đạt.**

## Xử lý critique ×2 (25) + review (R1.1/R1.2)

- 14 + 11 vấn đề critique resolved: safety layer thứ tự (b trước d, danger-only gate), step contract state[step_name] + flat merge, repr-escape, extractor union 3 nguồn, allow-list 2 set + exclude agents*, exec ns contract, issues field, thread prefix
- Review R1.1 (KB-miss dead code → extractor union default KB) ✅ test `test_kb_miss_cautious`
- Review R1.2 (allow-list intra-package → exclude aios_core.agents*) ✅
- R2 (risk default low vs assessment rỗng → assert tầng response/metadata) ✅

## Bài học mới

1. `state[key] = result` + `state.update(result)` — step contract giữ key riêng (test_reports) + flat cho key trực tiếp (code)
2. MockModel `responses=None` → ModelError ngay (exhausted) — test phải truyền `responses=[...]`
3. Extractor substring: "sốt" ⊂ "sốt cao" — phải lọc keyword con sau longest-match
4. `_arch_scan` bỏ qua `from __future__ import ...` (ImportFrom level=0 mod="__future__")
5. Danger-only (danger keyword không trong KB) → risk=high + emergency, KHÔNG vào nhánh KB-miss

## Kết luận

**TASK-013 ĐẠT — 12/12 AC, 549 tests pass, 0 skip (INV-001/002 bật), coverage 96.03%, git sạch sau commit.**
