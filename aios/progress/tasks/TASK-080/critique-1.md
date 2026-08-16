# TASK-080 — Critique vòng 1 (độc lập)

> Mục tiêu phản biện: phát hiện lỗ hổng spec trước khi implement.

## Phát hiện

| ID | Mức | Vấn đề | Giải pháp đề xuất |
|----|-----|--------|------------------|
| C1-01 | P1 | Spec chưa quy định rõ **format manifest.json** ánh xạ sang `SkillManifest` (field `source` chỉ nhận zip/git/pip). Nếu set `source="local"` sẽ vi phạm `extra=forbid` + enum. | Quy định rõ: `source="git"` cho cả 2 skill (vendored), thêm `metadata.vendored_from` ghi nguồn gốc. |
| C1-02 | P1 | AC3 yêu cầu script chạy được nhưng **chưa liệt kê dependency cài đặt** (Pillow/numpy). Test environment (venv) có thể chưa có → fail. | Thêm bước `pip install Pillow numpy` trong test; hoặc kiểm tra import và skip nếu thiếu, ghi rõ trong test.md. |
| C1-03 | P2 | `catalog/` là thư mục mới ở root, có thể gây nhầm lẫn với `backend/src/aios_core/catalog/` (code module). | Ghi chú rõ trong README: root `catalog/` = artifact registry JSON cho SystemCatalog; backend `catalog/` = code. |
| C1-04 | P2 | SKILL.md cô đọng ≤200 dòng nhưng `agent-sprite-forge` gốc rất dài; dễ bỏ sót quy tắc quan trọng (ví dụ: không dùng 1xN strip cho character). | Ưu tiên cô đọng các Rule cốt lõi + dẫn link gốc; liệt kê "cấm" rõ ràng. |
| C1-05 | P3 | Chưa định nghĩa `capabilities`/`permissions` cụ thể → có thể để trống vi phạm AC1 (list không rỗng). | Đặt capabilities/permissions thực tế (vd: `["game-asset-generation","sprite-generation"]`, `["filesystem:write","shell:python"]`). |

## Kết luận vòng 1
Đủ điều kiện tiếp tục sau khi resolve C1-01, C1-02, C1-05 (P1). C1-03/C1-04 là P2/P3, xử lý khi implement.
