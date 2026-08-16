# TASK-082 — Critique vòng 2 (spec)

> **Critic**: AIOS Orchestrator | **Ngày**: 2026-08-16 | **Trạng thái**: resolved

## P1 — Phải sửa

### C2-01. R6 pre-route + template macro: workflow creative trong library sẽ match cả 2 đường — test AC1 phải rõ kỳ vọng
Nếu `creative/game_scaffold` được register vào library, request "build a game" sẽ pre-route match (0.85) TRƯỚC — đúng. Nhưng "run workflow.yaml" không có từ khóa creative → không pre-route → macro/... → không match → None. AC2 cần test cả 2 hướng.
→ **Resolve**: AC1 assert `matched_by == "creative"` và confidence 0.85; AC2 assert request backend thường → None (không creative match, không đổi hành vi). Bổ sung AC: request "generate pixel art" → `creative:*`.

### C2-02. R8: SecurityChecker.run() hiện wrap exception → skipped (TASK-078). Check vendor mới cần không phá pattern
→ Resolve: check vendor là method bình thường trong SecurityChecks (như 11 check cũ); SecurityChecker.run() giữ nguyên fail-closed wrap. Không đổi.

### C2-03. R12 `AssetSpec` params — reference output phải merge, không ghi đè params có sẵn
→ Resolve: `params = {**existing, "reference": desc.model_dump()}` — merge an toàn.

## P2 — Nên sửa

### C2-04. CLI `aiagent reference describe` — tên subcommand `reference` có thể xung đột
→ Resolve: kiểm tra cli subcommand list — chưa có `reference`, an toàn. Giữ.

### C2-05. MockVisionAnalyzer — deterministic qua hash ảnh hay path?
→ Resolve: hash nội dung file (sha256 đầu) → seed description (giống mulberry32 pattern TASK-079) — cùng ảnh → cùng description; khác ảnh → khác. Deterministic + meaningful.

## P3 — Ghi nhận

### C2-06. Workflow creative register vào library — có ảnh hưởng catalog search hiện có?
→ Resolve: library.list() trả thêm 2 workflow — các test catalog/library cũ đếm số lượng có thể fail. Ghi vào tasks.md: chạy regression test_workflow* trước/ sau.

## Kết luận
Spec v2 sau resolve → **APPROVED — được phép implement** (đủ 2 vòng).
