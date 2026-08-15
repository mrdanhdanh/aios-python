# TASK-076 — Evaluation

> Ngày: 2026-08-15 · Đối chiếu 13 AC theo spec + bài học.

## Đối chiếu tiêu chí chấp nhận

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC1 | Tồn tại `docs/architecture-v3.md`; v2 không bị xóa | ✅ | Cả 2 file tồn tại trong repo |
| AC2 | ≥ 8 khối ```mermaid hợp lệ (flowchart/sequenceDiagram/stateDiagram-v2, không gantt) | ✅ | 12 khối, parse 12/12 |
| AC3 | Header + §Milestones phản ánh M10 DONE (1939 tests, conformance READY, doctor 100/100, review ACCEPTED) | ✅ | validate 4/4 |
| AC4 | Bảng tasks M10: 13 task đều done + module thật, đúng ánh xạ id PROGRESS | ✅ | validate 13/13 |
| AC5 | Đủ INV-001..034 + 5 gates + freeze (release blocker) | ✅ | validate 3/3 |
| AC6 | Đủ module M10 (gồm freeze/constitution — critique P2-4) | ✅ | validate 14/14 keyword |
| AC7 | Số liệu đối chiếu PROGRESS khớp; coverage M10 = N/A | ✅ | spot-check + ghi chú §9.2 |
| AC8 | Mermaid parse không lỗi (mermaid v11 + jsdom, không chromium) | ✅ | 12/12 khối parse OK |
| AC9 | v2 header đổi "LỊCH SỬ" + dòng dẫn chiếu; git diff chỉ header/§0/§14 | ✅ | diff 9 dòng |
| AC10 | Đóng DoD: LOG.md + PROGRESS.md + commit | ✅ | file này + entry + commit |
| AC11 | Mỗi sơ đồ keyword đặc trưng (grep theo khối) | ✅ | 5/5 khối chính + P3-1 (state/sequence phủ gián tiếp qua parse + AC6) |
| AC12 | `docs/architecture/*` (6 file frozen) không đổi | ✅ | git status trống |
| AC13 | Bảng tasks M1–M9 khớp v2 §11.1 | ✅ | 0 dòng thiếu |

**Kết quả: 13/13 AC ĐẠT** ✅

## Quyết định đáng chú ý

1. **Đảo quy ước "markdown thuần" (TASK-063 v1) → Mermaid** — theo yêu cầu người dùng 2026-08-15 (phương án "2 và 3": Mermaid + file mới riêng). Lý do: render được trên GitHub + VS Code preview. Đã ghi rõ trong v3 §0 + §14 và đánh dấu v2 là LỊCH SỬ (không xóa).
2. **7 tầng L1..L7 theo layer-model.md frozen** (khác v2) — Autonomous = L2 (không phải lớp mở rộng); Harness/Enterprise/Ecosystem = L7; M10 = nhóm đảm bảo không phải L8. V2 sai điểm này → v3 sửa đúng chuẩn 1.0.
3. **Bỏ gantt** (critique P2-2) — nguồn chỉ có 1 mốc ngày thật (2026-08-15); không bịa ngày. Timeline milestones thay bằng flowchart.

## Bài học

- **Critique ×2 hiệu quả**: P1-1/P1-2 (7 tầng mâu thuẫn với frozen) bắt được trước khi implement — nếu không, v3 đã tạo "2 chân lý" với constitution-1.0.md.
- **AC phải gắn với cơ chế kiểm tra cụ thể**: AC11 (grep theo khối) + AC13 (định nghĩa phạm vi §11.1) đã ngăn false-positive/negative; script lần đầu sai phạm vi → sửa script, không sửa nội dung.
- **Validate Mermaid thật chạy được offline-first**: `mermaid` + `jsdom` (pure JS, không chromium) — bộ validate đặt tại `aios/tools/mermaid-validate/` (đã .gitignore node_modules) tái dùng được cho các tài liệu Mermaid sau này.
- **Docs-only task vẫn phải qua hard gate đủ 8-file** — spec + critique ×2 + tasks + review + test + evaluation (giống TASK-063 v1).

## Đề xuất

- Thêm bước "cập nhật architecture doc + render check Mermaid" vào DoD của các milestone sau (nếu tài liệu Mermaid tiếp tục được dùng).
- Khi tạo tài liệu Mermaid mới: chạy lại `validate-mermaid.mjs` làm gate trước khi commit.

## Kết luận

**TASK-076 DONE** — `docs/architecture-v3.md` (AIOS 1.0 Final, Mermaid) là bản hiện hành; v2/v1 giữ lịch sử; M10 done phản ánh đúng (1939 tests, conformance READY, doctor 100/100).
