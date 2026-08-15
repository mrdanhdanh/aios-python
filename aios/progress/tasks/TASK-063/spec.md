# TASK-063 — Vẽ lại hoàn toàn tài liệu kiến trúc hệ thống (docs/architecture-v2.md)

## Mục tiêu

Vẽ lại hoàn toàn tài liệu kiến trúc hệ thống theo trạng thái THẬT của repo (M0–M9 done, 1793 tests, M10 — AIOS 1.0 sắp tới). Tạo **file MỚI** `docs/architecture-v2.md`; giữ nguyên `docs/architecture.md` hiện tại làm lịch sử (không sửa, không xóa).

> **AMEND (2026-08-15, theo yêu cầu người dùng)**: định dạng chuyển từ Mermaid sang **markdown thuần** (bảng + danh sách + sơ đồ ASCII trong code block) — không dùng Mermaid, đọc được ở mọi nơi, không phụ thuộc renderer. Các tiêu chí chấp nhận liên quan Mermaid được thay bằng kiểm tra cấu trúc markdown.

## Bối cảnh / Lý do

File `docs/architecture.md` hiện tại lỗi thời nghiêm trọng: mô tả M5 in-progress (TASK-026/027/028 🔲), "AIOS SDK 🔲 (stubs)", INV chỉ đến 016, thiếu hoàn toàn M6 Harness / M7 Enterprise / M8 Ecosystem / M9 Autonomous. Ngoài ra người dùng ghi nhận file hiện tại **đọc bị lỗi** (render Mermaid lỗi).

## Phạm vi

- Tạo `docs/architecture-v2.md` với cấu trúc **markdown thuần** (bảng + danh sách + sơ đồ ASCII trong code block) — KHÔNG dùng Mermaid; tránh mọi lỗi render không phụ thuộc trình đọc.
- Nội dung: 7 tầng lõi (M0–M5) + 4 lớp hệ sinh thái (M6–M9) + Control/Worker/Autonomy Plane + luồng request + Runtime Kernel 9 services + Intelligence Core M5 + Harness M6 + Enterprise M7 + Ecosystem M8 + Autonomous M9 + milestones M0–M10 + INV-001..034 + nguyên tắc xuyên suốt.
- Chỉ tài liệu: KHÔNG đổi code, KHÔNG đổi `docs/PLAN.md`, KHÔNG sửa `docs/architecture.md`.

## Ngoài phạm vi

- Không sửa code backend/dashboard/extension/sdk.
- Không cập nhật PLAN.md (chỉ cập nhật aios/progress/ theo quy trình).

## Input (nguồn sự thật)

- `docs/PLAN.md` (master plan v6 — kiến trúc, milestones, INV)
- `aios/progress/PROGRESS.md` (trạng thái build thật M0–M9, số liệu test)
- `docs/architecture.md` (file cũ — tham khảo cấu trúc, KHÔNG sửa)
- `backend/src/aios_core/` (cấu trúc package thật)

## Output

- `docs/architecture-v2.md` — tài liệu kiến trúc mới (file chính)
- `aios/progress/tasks/TASK-063/` — đủ 8-file hard gate

## Tiêu chí chấp nhận (AC)

| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | Phản ánh đúng trạng thái: M0–M9 `done`, M10 `todo`; số liệu tests/coverage khớp PROGRESS.md | Đối chiếu PROGRESS.md |
| AC2 | KHÔNG còn khối ```` ```mermaid ```` nào trong file; cấu trúc markdown hợp lệ (heading, bảng, code block cân bằng) | Script kiểm tra tự động (node) |
| AC3 | Đủ 7 tầng lõi + 4 lớp M6–M9 (Harness/Enterprise/Ecosystem/Autonomous) | Đọc cấu trúc file |
| AC4 | Bảng INV-001..034 đầy đủ, nhãn canonical đúng (M2: 001–010, M5: 011–016, M6: 017–021, M7: 022–029, M9: 030–034) | Đối chiếu PROGRESS.md §M7 note |
| AC5 | Bảng milestone M0–M10 + bảng tasks M1–M9 đúng task id, mô tả, số tests | Đối chiếu PROGRESS.md |
| AC6 | File cũ `docs/architecture.md` KHÔNG bị sửa | git diff |
| AC7 | Đóng DoD: LOG.md entry + PROGRESS.md cập nhật + commit | Checklist AGENTS.md §3.1 |

## Ghi chú

- Đây là task tài liệu (docs-only): không đổi hành vi hệ thống, không có test code mới; test = kiểm tra cấu trúc markdown (không còn khối mermaid, code fence cân bằng, bảng đủ cột) + đối chiếu dữ liệu.
- Số liệu tests lấy nguyên từ PROGRESS.md (2026-08-15): M1 428/95.76, M2 669/95.51, M3 689+12+19, M4 809/94.92, M5 1086/95.22, M6 1521/95.35, M7 1560/95.05, M8 1639, M9 1780/94.46 (full 1793).
