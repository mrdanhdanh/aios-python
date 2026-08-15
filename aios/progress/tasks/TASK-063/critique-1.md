# TASK-063 — Critique vòng 1 (M10-F1, spec v2)

> Critic vòng 1 cho phần mở rộng M10-F1 (v1 đã qua 2 vòng critique — giữ nguyên). Phản biện spec v2 độc lập.

## Các vấn đề tìm được

### C1-01 (P2) — Constitution phải tránh "invariant trên giấy"
PLAN §M10-5 ghi rõ constitution = INV-001..034, nhưng nếu một INV chưa có enforcement test thì constitution tuyên bố freeze sẽ vô nghĩa.
→ **Resolve**: AC4 bắt buộc script đối chiếu mọi INV trong constitution với `backend/tests/test_architecture.py` (grep `inv001`..`inv034` + `m9_*`); nếu thiếu → FAIL test. Kiểm tra thực tế trước khi viết.

### C1-02 (P2) — Tài liệu 7 layers có thể trùng lặp với architecture-v2.md
Nếu 5 file docs/architecture/* chỉ sao chép nội dung cũ → thừa, không giá trị.
→ **Resolve**: Mỗi file có vai trò riêng: AIOS-1.0 = tổng thể + freeze status; layer-model = 7 tầng chi tiết; control-plane / execution-plane / autonomy = chuyên sâu từng plane (module thật + luồng); constitution = INV. Không lặp bảng milestone/task (đã có ở v2).

### C1-03 (P3) — Ghi chú M10-P5 "Certification" cần phân biệt conformance
`aiagent conformance` là output TASK-073 (M10-P5), không phải TASK-063. Tránh hứa hẹn điều chưa làm trong tài liệu 1.0.
→ **Resolve**: AIOS-1.0.md mô tả mục tiêu conformance/release gates như "planned (TASK-073)" — không khẳng định đã có.

### C1-04 (P3) — Version/date trong tài liệu
Constitution cần version + ngày freeze để theo dõi lịch sử amend.
→ **Resolve**: constitution-1.0.md có header version 1.0 + ngày 2026-08-15 + section "Lịch sử" (v1.0: freeze INV-001..034).

## Kết luận
Các vấn đề đã resolve vào spec v2 (AC4 bắt buộc đối chiếu; vai trò từng file rõ; ghi chú planned; version/date).

## Kết luận vòng 1
Spec cơ bản đủ; các vấn đề trên được resolve bằng quy ước viết (C1-01..C1-06) — chuyển sang critique vòng 2.
