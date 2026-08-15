# TASK-076 — Critique vòng 1 (critic agent) + Resolution

> Ngày: 2026-08-15 · Critic: subagent `critic` · Spec: `spec.md`

## Kết quả critique

Spec khởi đầu rõ ràng, dữ liệu M10 khớp PROGRESS.md (1939 pass + vitest 13/13 + conformance READY + doctor 100/100). Mức sẵn sàng ban đầu: 3/5. Tìm được **2 P1, 5 P2, 8 P3** — tất cả đã resolve như dưới đây.

## Vấn đề + Resolution

### P1-1 — Mâu thuẫn cấu trúc 7 tầng (spec theo v2 vs layer-model frozen)
- **Vấn đề**: spec liệt kê 7 tầng theo v2 (UI → Runtime → Workflow → Orchestrator → Intelligence → Capability → Infra), nhưng `docs/architecture/layer-model.md` + `AIOS-1.0.md` (FROZEN TASK-063) định nghĩa L1..L7 khác: L1 UI/SDK/API → L2 Autonomy → L3 Orchestrator → L4 Workflow/Agent/Capability → L5 Runtime Kernel → L6 Tools/State/Events → L7 Infra. v3 tự nhận "hiện hành" mà mâu thuẫn tài liệu frozen = 2 chân lý.
- **Resolution ✅**: v3 dùng **đúng L1..L7 theo layer-model.md** (chuẩn 1.0 frozen). Đã sửa spec Phạm vi mục 2 + AC2 + sơ đồ tổng quan.

### P1-2 — Autonomous vừa là L2 (frozen) vừa là "lớp mở rộng M9" (v2)
- **Vấn đề**: spec yêu cầu vẽ "4 lớp mở rộng (Harness/Enterprise/Ecosystem/**Autonomous**)" — nhưng layer-model frozen đặt Autonomous là L2. Cùng lúc 2 chỗ → mâu thuẫn.
- **Resolution ✅**: Autonomous nằm trong 7 tầng (L2). "Lớp mở rộng" còn 3: Harness/Enterprise/Ecosystem (thuộc L7). Ghi chú: M9 = milestone phát triển của L2, không phải tầng riêng. Đã sửa spec.

### P2-1 — Không có công cụ validate Mermaid trong repo
- **Vấn đề**: grep toàn repo — không package.json nào chứa mermaid/mermaid-cli; script tự chế chỉ check fence/keyword thô.
- **Resolution ✅**: AC8 dùng npm package `mermaid` (pure JS, không cần chromium): `mermaid.parse()` từng block → parse không lỗi = PASS. Fallback cụ thể: fence đủ + keyword dòng đầu hợp lệ (flowchart/sequenceDiagram/stateDiagram-v2) + subgraph cân bằng + label có ký tự đặc biệt phải đặt trong `""`.

### P2-2 — gantt cần ngày tháng nhưng nguồn chỉ có 1 mốc 2026-08-15
- **Vấn đề**: Mermaid gantt bắt buộc dateFormat + date — bịa ngày = vi phạm AC7 (dữ liệu thật).
- **Resolution ✅**: **Bỏ gantt**. Thay bằng flowchart timeline M0→M10 (số liệu thật). Bù lại thêm `stateDiagram-v2` (Safety chain 7 bước) + `sequenceDiagram` (Kill Switch) → vẫn đủ ≥ 8 khối Mermaid.

### P2-3 — Header v2 nằm ngoài §0, v2 vẫn tự nhận "HIỆN HÀNH"
- **Vấn đề**: blockquote header v2 (dòng 2–7) ghi "📌 TÀI LIỆU HIỆN HÀNH" + "M10 — AIOS 1.0 (todo)" — sửa §0/§14 không chạm header.
- **Resolution ✅**: đổi header v2 thành "📜 TÀI LIỆU LỊCH SỬ" + dòng dẫn chiếu v3 ngay dưới title. AC9 mở rộng: `git diff` xác nhận v2 chỉ đổi header/§0/§14.

### P2-4 — Sơ đồ M10 chỉ 12 module, thiếu TASK-063 (Freeze/Constitution)
- **Vấn đề**: M10 có 13 task nhưng danh sách module M10 thiếu Freeze/Constitution.
- **Resolution ✅**: thêm "Freeze (Constitution + INV-001..034)" vào sơ đồ M10 + từ khóa vào AC6.

### P2-5 — Không AC nào kiểm tra nội dung 6 sơ đồ còn lại
- **Vấn đề**: AC chỉ grep M10 modules + INV/gates — bỏ sót 1 sơ đồ vẫn đủ AC.
- **Resolution ✅**: thêm AC11 (mới): grep bắt buộc từ khóa cho từng sơ đồ — 4 plane, Decision Pipeline (Normalizer/Rule Engine/Workflow Matcher/Planner LLM), luồng 12 bước, Runtime Kernel 9 services, Core Intelligence 6 năng lực.

### P3 (8 nhẹ — đều resolved)
1. **AC3 thiếu doctor 100/100** → ✅ thêm vào AC3.
2. **Coverage M10 không tồn tại** trong PROGRESS → ✅ ghi chú spec: coverage M10 = N/A, không bịa.
3. **`stateDiagram` → `stateDiagram-v2`** → ✅ spec dùng stateDiagram-v2.
4. **Không AC bảo vệ docs/architecture/* không đổi** → ✅ AC mới: git diff xác nhận không thay đổi.
5. **"Lớp M10" là khái niệm mới** → ✅ ghi chú trong v3: nhóm đảm bảo (Freeze/Harden/Secure/Productize/Certify), KHÔNG phải L8.
6. **Bảng tasks M1–M9 giữ nguyên từ v2 không có AC đối chiếu** → ✅ AC so sánh bảng với v2.
7. **Quy ước đảo "KHÔNG Mermaid" (TASK-063 v1)**: người đọc v3 không thấy lý do → ✅ thêm dòng trong "Nguồn & lịch sử" v3 (quyết định người dùng 2026-08-15, lý do render GitHub/VS Code).
8. **AC2 "≥ 8 khối" phụ thuộc gantt** → ✅ đã bỏ gantt, thêm stateDiagram-v2 + sequenceDiagram → 8+ khối.

## Kết luận

- [x] **Đã resolve toàn bộ** — spec.md v2 đã cập nhật theo các resolution trên.
- [x] Dữ liệu đối chiếu PROGRESS.md: khớp (không sai số liệu).
- → Chuyển sang **critique vòng 2** (bắt buộc sau khi resolve vòng 1).
