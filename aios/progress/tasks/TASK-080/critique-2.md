# TASK-080 — Critique vòng 2 (độc lập, sau khi resolve vòng 1)

> Xác nhận các P1 đã resolve; rà thêm góc nhìn khác (bảo mật, khả dụng, tích hợp).

## Trạng thái resolve vòng 1
- C1-01 ✅ resolved — sẽ set `source="git"` + `metadata.vendored_from`.
- C1-02 ✅ resolved — test sẽ `pip install Pillow numpy` (hoặc skip+rõ lý do).
- C1-05 ✅ resolved — capabilities/permissions sẽ không rỗng.

## Phát hiện mới

| ID | Mức | Vấn đề | Giải pháp đề xuất |
|----|-----|--------|------------------|
| C2-01 | P2 | Script `generate2dsprite.py` chạy shell Python → cần permission `shell:python`. Nhưng skill này là "agent skill" (chạy trong Codex/Grok), không chạy tự động trong AIOS. Ghi chú rõ để không lầm tưởng AIOS gọi trực tiếp. | Trong SKILL.md ghi rõ: script chạy bởi host agent (Codex/Grok/Claude), AIOS chỉ index metadata. |
| C2-02 | P2 | Metadata của `pixel-game-dev` mang tính "tài liệu" — có thể trùng với việc lưu knowledge base. Nên tách rõ: skill = hướng dẫn agent làm game; knowledge = dữ liệu tham khảo. | Giữ `pixel-game-dev` là skill (hướng dẫn), các bảng so sánh engine đẩy vào `references/`. |
| C2-03 | P3 | Chưa có cách AIOS "phát hiện" skill mới trong `skills/` (hiện SkillManager đọc từ DB). | Ghi chú trong README: bước đăng ký vào `skills.db` sẽ làm ở task sau khi Runtime sẵn sàng (hoặc qua CLI `aiagent skill register`). |

## Kết luận vòng 2
Không còn P1. Đủ 2 vòng critique độc lập → được phép implement.
