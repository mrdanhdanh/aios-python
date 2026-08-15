# Review trước implement — TASK-077

## Phạm vi review
Spec.md (bản đã cập nhật sau critique-1 + critique-2, tất cả resolution đã resolve).

## Nhận xét

1. **Story & luồng chơi**: đúng yêu cầu người dùng — 6 cảnh + title + game over + end, đầy đủ các beat (bướm, tối dần, máu, lựa chọn, ma ám, 5 lần hù, sinh nhật).
2. **State machine**: bảng sub-state đầy đủ, mỗi transition có trigger — đủ điều kiện implement không kẹt.
3. **Dữ liệu cụ thể**: map size, camera, trigger rules, sprite list, light radius, collision slide, timer dt — đã chốt (C2-11..18).
4. **AC**: 17 AC, mỗi AC có phương thức kiểm chứng [node]/[manual]/[visual] — đủ rõ.
5. **Rủi ro còn lại (chấp nhận được)**:
   - Pixel art vẽ bằng code có thể chưa đẹp ngay lần đầu → sẽ tinh chỉnh sau khi xem ảnh chụp (manual).
   - GitHub Pages chưa bật → AC13 chỉ verify cục bộ + hướng dẫn user bật.
   - Bubble cảnh 1 có thể bị cắt khi mèo chạm cửa sớm (đã quyết định chấp nhận — C2-21).
   - Phụ đề tiếng Việt có dấu với font monospace — kiểm tra render khi chạy thật.

## Kết luận
- [x] **APPROVED** — đủ điều kiện implement. Các ghi chú P3 xử lý trong lúc code.
- Reviewer: AIOS Orchestrator (pre-implement). Review code thật sau khi implement xong (xem review.md bản cập nhật).
