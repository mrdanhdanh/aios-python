# TASK-063 — Review (trước implement)

> Reviewer (tự — subagent không phản hồi, tiền lệ TASK-031).

## Đánh giá spec v2 (sau critique ×2 resolved)

- Phạm vi rõ, giới hạn đúng (docs-only, không đụng code/PLAN/file cũ). ✅
- AC đo được (đối chiếu PROGRESS.md, parser mermaid, git diff). ✅
- Rủi ro render đã được xử lý bằng quy ước viết (C1-02, C2-01). ✅
- Số liệu test chốt nguồn duy nhất PROGRESS.md 2026-08-15. ✅

## Yêu cầu khi implement

1. **R1**: Mọi sơ đồ Mermaid phải qua parser `mermaid.parse()` (hoặc ghi rõ lý do fallback trong test.md) — không bỏ qua.
2. **R2**: Không sửa `docs/architecture.md` (AC6) — nếu cần tham chiếu thì chỉ thêm pointer trong file mới.
3. **R3**: Số liệu (tests, coverage, task id) ghi đúng PROGRESS.md; nếu có chỗ không chắc → ghi "theo PROGRESS.md" thay vì bịa.

## Kết luận
**APPROVED có điều kiện** (R1–R3) — được phép viết file mới.
