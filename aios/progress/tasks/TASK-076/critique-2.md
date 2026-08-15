# TASK-076 — Critique vòng 2 (critic agent) + Resolution

> Ngày: 2026-08-15 · Critic: subagent `critic` (độc lập) · Spec v2 sau resolution vòng 1

## (a) Xác nhận resolution vòng 1

| Vấn đề vòng 1 | Kết quả |
|---|---|
| P1-1 (7 tầng theo layer-model frozen) | ✅ ĐẠT — spec mục 2 + AC2 đúng L1..L7, khớp 100% layer-model.md |
| P1-2 (Autonomous = L2, không phải lớp mở rộng) | ✅ ĐẠT — Harness/Enterprise/Ecosystem = L7; M9 = milestone của L2; M10 không phải L8 |
| P2-1 (validate Mermaid) | ⚠️ ĐẠT MỘT PHẦN → resolve bổ sung P2-A (thiếu jsdom) |
| P2-2 (bỏ gantt) | ⚠️ ĐẠT MỘT PHẦN → resolve bổ sung P3-A (Mục tiêu còn chữ "gantt") |
| P2-3 (header v2) | ✅ ĐẠT — AC9 mở rộng + git diff |
| P2-4 (thiếu Freeze/Constitution) | ✅ ĐẠT — 13 module khớp PROGRESS |
| P2-5 (bỏ sót 6 sơ đồ) | ⚠️ ĐẠT MỘT PHẦN → resolve bổ sung P2-B (grep theo khối) |
| P3-1..8 | ✅ ĐẠT 7/8; P3-6 → P2-C (AC13 mơ hồ) |

## (b) Vấn đề vòng 2 + Resolution

### P2-A — AC8: `mermaid.parse()` không chạy trong Node thuần (thiếu DOM)
- **Resolution ✅**: AC8 ghi rõ dùng `mermaid` + `jsdom` (pure JS, Windows thuần) HOẶC `@mermaid-js/parser` (Langium, không DOM); nếu npm offline → fallback + ghi rõ trong evaluation.md. Cài ở `aios/tools/mermaid-validate/`, không commit node_modules (P3-C).

### P2-B — AC11: grep toàn file → false-positive
- **Resolution ✅**: AC11 đổi thành **grep THEO KHỐI ` ```mermaid `** — mỗi khối phải chứa từ khóa đặc trưng riêng (đã liệt kê đầy đủ trong AC11), từ khóa nguyên văn trong khối.

### P2-C — AC13: cách so sánh bảng M1–M9 mơ hồ
- **Resolution ✅**: AC13 định nghĩa cụ thể — trích dòng bảng §11.1 v2 chứa `TASK-0xx` (M1–M9), normalize whitespace, so sánh set dòng; spot-check 3–5 dòng với PROGRESS.md.

### P3-A — Mục tiêu còn chữ "gantt"
- **Resolution ✅**: đã bỏ — Mục tiêu giờ ghi `flowchart/sequenceDiagram/stateDiagram-v2`.

### P3-B — Bảng M10 theo thứ tự số liên tục sẽ sai ánh xạ id
- **Resolution ✅**: AC4 ghi rõ theo đúng ánh xạ id↔module PROGRESS (063,064,065,066,069,067,068,070,071,072,075,073,074).

### P3-C — Nơi cài npm mermaid
- **Resolution ✅**: thư mục validate riêng `aios/tools/mermaid-validate/`, không commit node_modules (đã gộp vào AC8).

### P3-D — Header v2 dòng 6 "không dùng Mermaid" để nguyên sẽ kỳ
- **Resolution ✅**: sửa luôn dòng đó thành ghi chú lịch sử ("quy ước cũ; từ v3 dùng Mermaid") — vẫn trong phạm vi header của AC9.

## Kết luận

- [x] **Toàn bộ 2 P1 + 5 P2 + 8 P3 + 3 P2 + 4 P3 (vòng 2) ĐÃ RESOLVE** — spec v3 hoàn chỉnh.
- [x] Critic xác nhận: "Không yêu cầu vòng critique 3 — đây là vòng 2 bắt buộc cuối."
- → Đủ 2 vòng critique resolved → chuyển sang tasks.md + review (pre-implementation).
