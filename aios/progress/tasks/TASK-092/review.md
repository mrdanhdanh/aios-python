# TASK-092 — Review (trước implement)

> Reviewer: independent code review của spec + tasks trước khi đánh dấu done.

## Đánh giá spec.md
- ✅ Mục tiêu rõ: tách System Readiness ≠ Harness Trust + release gate cả 2 PASS
- ✅ Phạm vi chuẩn: module mới `harness/release/`, wiring, CLI, tests; KHÔNG sửa Runtime/Orchestrator, KHÔNG thêm invariant (INV-036 defer TASK-093)
- ✅ Thiết kế đúng: engine pure combiner (AC2), harness chạy sub-harness qua HarnessRunner (INV-017), fail-closed xử lý sub-harness fail → BLOCKED (critique-1 P1 + critique-2 P1)
- ✅ 12 AC bao phủ: 2 score độc lập (AC1), pure (AC2), PASS (AC3), 2 path BLOCKED (AC4/AC5), shape (AC6), harness (AC7/AC8), CLI (AC9), regression (AC10), determinism (AC11), tách biệt thật (AC12)
- ✅ Rủi ro đã liệt kê + giải pháp (R1-R5)

## Đánh giá tasks.md
- ✅ Checklist đủ: implement (T1-T8) → test (T9-T12) → docs (T13-T16)
- ✅ Ánh xạ 1-1 với AC

## Hard gate status
- ✅ Plan (PROGRESS.md updated)
- ✅ Spec (spec.md đầy đủ, tích hợp 2 vòng critique)
- ✅ Critique ×2 (critique-1 + critique-2, độc lập, đã resolve)
- ✅ Task (tasks.md checklist)
- ✅ Review (file này — APPROVED)

**Kết luận: APPROVED — sẵn sàng implement.** Không có blocker. Lưu ý implement: (1) try/except sub-harness fail → BLOCKED; (2) payload extraction an toàn (None/key missing); (3) `_COMPONENT_MODULES["release"]` để không phá READY; (4) cập nhật 4 registry test + test_registry_has_coverage.
